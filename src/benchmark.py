"""Core benchmark utilities for the FinanceMeta NIFTY IV trial.

This module freezes and applies the benchmark protocol. It does not write
results unless explicitly called by the notebook/CLI layer.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    from .data_utils import prepare_dataset
    from .interpolation import linear_strike_predict, nearest_strike_predict
    from .svi import fit_svi, predict_svi_iv
except ImportError:  # Support `python src/benchmark.py`-style execution.
    from data_utils import prepare_dataset
    from interpolation import linear_strike_predict, nearest_strike_predict
    from svi import fit_svi, predict_svi_iv


@dataclass(frozen=True)
class BenchmarkConfig:
    """Minimal immutable configuration loaded from the JSON protocol."""

    seed: int
    train_fraction: float
    validation_fraction: float
    evaluation_fraction: float
    missingness_levels: tuple[float, ...]
    time_block_count: int
    moneyness_edges: tuple[float, ...]
    moneyness_labels: tuple[str, ...]
    linear_allow_extrapolation: bool
    svi_min_points: int
    svi_max_nfev: int
    svi_initial_rhos: tuple[float, ...]
    svi_initial_sigmas: tuple[float, ...]

    @classmethod
    def from_json(cls, path: str | Path) -> "BenchmarkConfig":
        with Path(path).open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        split = raw["split"]
        holdout = raw["holdout"]
        strat = holdout["stratification"]
        mono = strat["moneyness_definition"]
        models = raw["models"]

        if not math.isclose(
            split["train_fraction"]
            + split["validation_fraction"]
            + split["evaluation_fraction"],
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("Chronological split fractions must sum to 1.")

        missingness = tuple(float(x) for x in holdout["missingness_levels"])
        if missingness != tuple(sorted(missingness)):
            raise ValueError("Missingness levels must be ascending.")
        if max(missingness) > 1.0 or min(missingness) <= 0.0:
            raise ValueError("Missingness levels must be in (0, 1].")
        if not holdout.get("nested", False):
            raise ValueError("Benchmark requires nested holdouts.")

        return cls(
            seed=int(raw["seed"]),
            train_fraction=float(split["train_fraction"]),
            validation_fraction=float(split["validation_fraction"]),
            evaluation_fraction=float(split["evaluation_fraction"]),
            missingness_levels=missingness,
            time_block_count=int(strat["time_block_count"]),
            moneyness_edges=tuple(float(x) for x in mono["edges"]),
            moneyness_labels=tuple(str(x) for x in mono["labels"]),
            linear_allow_extrapolation=bool(
                models["linear_strike"].get("allow_extrapolation", False)
            ),
            svi_min_points=int(models["svi"]["min_points"]),
            svi_max_nfev=int(models["svi"]["max_nfev"]),
            svi_initial_rhos=tuple(float(x) for x in models["svi"]["initial_rhos"]),
            svi_initial_sigmas=tuple(float(x) for x in models["svi"]["initial_sigmas"]),
        )


def add_moneyness_bins(
    df: pd.DataFrame,
    *,
    edges: Iterable[float],
    labels: Iterable[str],
) -> pd.DataFrame:
    """Add deterministic moneyness bins without changing the source rows."""
    result = df.copy()
    result["moneyness_bin"] = pd.cut(
        result["log_moneyness"],
        bins=list(edges),
        labels=list(labels),
        include_lowest=True,
        right=True,
    )
    result["moneyness_bin"] = result["moneyness_bin"].astype("string")
    result["moneyness_bin"] = result["moneyness_bin"].fillna("unbinned")
    return result


def chronological_split(
    df: pd.DataFrame,
    *,
    train_fraction: float,
    validation_fraction: float,
    evaluation_fraction: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split by unique timestamp, preserving all cells from each timestamp."""
    if not math.isclose(
        train_fraction + validation_fraction + evaluation_fraction,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("Split fractions must sum to 1.")

    timestamps = np.sort(df["datetime"].dropna().unique())
    n = len(timestamps)
    if n < 3:
        raise ValueError("At least three unique timestamps are required.")

    train_end = max(1, int(np.floor(n * train_fraction)))
    val_end = max(train_end + 1, int(np.floor(n * (train_fraction + validation_fraction))))
    if val_end >= n:
        val_end = n - 1

    train_ts = set(timestamps[:train_end])
    validation_ts = set(timestamps[train_end:val_end])
    evaluation_ts = set(timestamps[val_end:])

    train = df[df["datetime"].isin(train_ts)].copy()
    validation = df[df["datetime"].isin(validation_ts)].copy()
    evaluation = df[df["datetime"].isin(evaluation_ts)].copy()

    if train.empty or validation.empty or evaluation.empty:
        raise ValueError("Chronological split produced an empty partition.")

    return train, validation, evaluation


def _stable_score(observation_id: str, seed: int) -> int:
    """Stable pseudo-random ranking independent of row order and Python hash randomization."""
    payload = f"{seed}|{observation_id}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:16], 16)


def _rank_for_holdout(df: pd.DataFrame, seed: int) -> pd.Series:
    return df["observation_id"].map(lambda x: _stable_score(str(x), seed))


def build_nested_holdout(
    evaluation_df: pd.DataFrame,
    *,
    missingness_levels: Iterable[float],
    seed: int,
    time_block_count: int,
    moneyness_edges: Iterable[float],
    moneyness_labels: Iterable[str],
) -> tuple[dict[float, set[str]], pd.DataFrame]:
    """Create deterministic nested structured holdouts and their manifest.

    The same master 30% population is used to derive all smaller conditions.
    Strata are option type × moneyness bin × time block.
    """
    eval_df = evaluation_df.loc[evaluation_df["iv"].notna()].copy()
    if eval_df.empty:
        raise ValueError("Evaluation period contains no observed IV cells.")

    eval_df = add_moneyness_bins(
        eval_df,
        edges=moneyness_edges,
        labels=moneyness_labels,
    )
    unique_times = np.sort(eval_df["datetime"].unique())
    time_block_lookup = {}
    blocks = np.array_split(unique_times, time_block_count)
    for block_idx, block in enumerate(blocks):
        for ts in block:
            time_block_lookup[ts] = block_idx
    eval_df["time_block"] = eval_df["datetime"].map(time_block_lookup).astype(int)

    levels = sorted(float(x) for x in missingness_levels)
    max_fraction = levels[-1]
    target_n = int(np.ceil(len(eval_df) * max_fraction))
    target_n = min(target_n, len(eval_df))

    # Deterministic within-stratum ranking.
    eval_df["_rank"] = _rank_for_holdout(eval_df, seed)
    strata = ["option_type", "moneyness_bin", "time_block"]

    # Initial allocation proportional to stratum size, then distribute remainder.
    counts = eval_df.groupby(strata, dropna=False).size().sort_index()
    raw_quota = counts * (target_n / len(eval_df))
    quota = np.floor(raw_quota).astype(int)
    remainder = target_n - int(quota.sum())

    if remainder > 0:
        fractional = (raw_quota - quota).sort_values(ascending=False)
        for key in fractional.index[:remainder]:
            quota.loc[key] += 1

    selected_frames = []
    for key, group in eval_df.groupby(strata, dropna=False, sort=True):
        n_select = int(quota.loc[key])
        if n_select <= 0:
            continue
        selected_frames.append(
            group.sort_values(["_rank", "observation_id"]).head(n_select)
        )

    master = pd.concat(selected_frames, ignore_index=False) if selected_frames else eval_df.iloc[0:0]
    master = master.sort_values(["_rank", "observation_id"]).reset_index(drop=True)

    # Guard against allocation drift.
    if len(master) != target_n:
        # Fill any deficit using globally ranked unused candidates.
        selected_ids = set(master["observation_id"])
        remaining = eval_df[~eval_df["observation_id"].isin(selected_ids)]
        deficit = target_n - len(master)
        if deficit > 0:
            master = pd.concat(
                [
                    master,
                    remaining.sort_values(["_rank", "observation_id"]).head(deficit),
                ],
                ignore_index=True,
            )
        elif deficit < 0:
            master = master.head(target_n).copy()

    if len(master) != target_n:
        raise RuntimeError("Failed to construct the requested master holdout.")

    # Nested subsets of the same master ordering.
    manifests: dict[float, set[str]] = {}
    for level in levels:
        n_level = int(np.ceil(len(eval_df) * level))
        n_level = min(n_level, len(master))
        manifests[level] = set(master.head(n_level)["observation_id"])

    manifest = master[
        [
            "observation_id",
            "datetime",
            "symbol",
            "expiry",
            "strike",
            "option_type",
            "underlying_price",
            "log_moneyness",
            "moneyness_bin",
            "time_block",
        ]
    ].copy()

    for level in levels:
        col = f"missingness_{int(round(level * 100))}"
        manifest[col] = manifest["observation_id"].isin(manifests[level])

    manifest["master_holdout_30"] = True
    return manifests, manifest


def _evaluate_predictions(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float | int]:
    """Compute metrics and coverage without silently dropping failures."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    finite = np.isfinite(actual) & np.isfinite(predicted)
    n_targets = int(actual.size)
    n_pred = int(finite.sum())

    if n_pred == 0:
        rmse = float("nan")
        mae = float("nan")
    else:
        rmse = float(np.sqrt(mean_squared_error(actual[finite], predicted[finite])))
        mae = float(mean_absolute_error(actual[finite], predicted[finite]))

    coverage = float(n_pred / n_targets) if n_targets else float("nan")
    return {
        "n_targets": n_targets,
        "n_predictions": n_pred,
        "coverage": coverage,
        "rmse": rmse,
        "mae": mae,
        "failure_count": n_targets - n_pred,
    }


def _slice_groups(df: pd.DataFrame) -> Iterable[tuple[tuple, pd.DataFrame]]:
    """Group each timestamp/expiry/option-type slice used by all three models."""
    return df.groupby(
        ["datetime", "expiry", "option_type"],
        sort=True,
        observed=True,
    )


def _run_linear_for_condition(
    masked_df: pd.DataFrame,
    holdout_ids: set[str],
    *,
    allow_extrapolation: bool,
) -> tuple[pd.DataFrame, float]:
    predictions = []
    start = time.perf_counter()

    for key, group in _slice_groups(masked_df):
        train = group[(~group["observation_id"].isin(holdout_ids)) & group["iv"].notna()].copy()
        targets = group[group["observation_id"].isin(holdout_ids)].copy()
        if targets.empty:
            continue

        pred = linear_strike_predict(
            train["strike"].to_numpy(),
            train["iv"].to_numpy(),
            targets["strike"].to_numpy(),
            allow_extrapolation=allow_extrapolation,
        )
        targets = targets[
            [
                "observation_id", "datetime", "expiry", "option_type", "strike",
                "iv", "underlying_price", "time_to_expiry_years", "log_moneyness"
            ]
        ].copy()
        targets["prediction"] = pred
        targets["model"] = "linear_strike"
        predictions.append(targets)

    runtime = time.perf_counter() - start
    result = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    return result, runtime


def _run_nearest_for_condition(
    masked_df: pd.DataFrame,
    holdout_ids: set[str],
) -> tuple[pd.DataFrame, float]:
    predictions = []
    start = time.perf_counter()

    for key, group in _slice_groups(masked_df):
        train = group[(~group["observation_id"].isin(holdout_ids)) & group["iv"].notna()].copy()
        targets = group[group["observation_id"].isin(holdout_ids)].copy()
        if targets.empty:
            continue

        pred = nearest_strike_predict(
            train["strike"].to_numpy(),
            train["iv"].to_numpy(),
            targets["strike"].to_numpy(),
        )
        targets = targets[
            [
                "observation_id", "datetime", "expiry", "option_type", "strike",
                "iv", "underlying_price", "time_to_expiry_years", "log_moneyness"
            ]
        ].copy()
        targets["prediction"] = pred
        targets["model"] = "nearest_strike"
        predictions.append(targets)

    runtime = time.perf_counter() - start
    result = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    return result, runtime


def _run_svi_for_condition(
    masked_df: pd.DataFrame,
    holdout_ids: set[str],
    *,
    min_points: int,
    max_nfev: int,
    initial_rhos: tuple[float, ...],
    initial_sigmas: tuple[float, ...],
) -> tuple[pd.DataFrame, float]:
    predictions = []
    start = time.perf_counter()

    for key, group in _slice_groups(masked_df):
        train = group[(~group["observation_id"].isin(holdout_ids)) & group["iv"].notna()].copy()
        targets = group[group["observation_id"].isin(holdout_ids)].copy()
        if targets.empty:
            continue

        t_values = train["time_to_expiry_years"].dropna()
        T = float(t_values.iloc[0]) if not t_values.empty else float("nan")

        fit = fit_svi(
            train["log_moneyness"].to_numpy(),
            train["iv"].to_numpy(),
            T,
            min_points=min_points,
            max_nfev=max_nfev,
            initial_rhos=initial_rhos,
            initial_sigmas=initial_sigmas,
        )
        pred = predict_svi_iv(
            targets["log_moneyness"].to_numpy(),
            T,
            fit,
        )
        targets = targets[
            [
                "observation_id", "datetime", "expiry", "option_type", "strike",
                "iv", "underlying_price", "time_to_expiry_years", "log_moneyness"
            ]
        ].copy()
        targets["prediction"] = pred
        targets["model"] = "svi"
        targets["fit_success"] = bool(fit.success)
        targets["fit_message"] = fit.message
        predictions.append(targets)

    runtime = time.perf_counter() - start
    result = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    return result, runtime


def run_condition(
    evaluation_df: pd.DataFrame,
    holdout_ids: set[str],
    *,
    level: float,
    config: BenchmarkConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run all frozen models for one missingness condition."""
    # Natural-missing observations stay NaN; only the predefined holdout is
    # considered a target. All originally observed non-target cells remain usable.
    masked = evaluation_df.copy()

    linear_preds, linear_runtime = _run_linear_for_condition(
        masked,
        holdout_ids,
        allow_extrapolation=config.linear_allow_extrapolation,
    )
    nearest_preds, nearest_runtime = _run_nearest_for_condition(
        masked,
        holdout_ids,
    )
    svi_preds, svi_runtime = _run_svi_for_condition(
        masked,
        holdout_ids,
        min_points=config.svi_min_points,
        max_nfev=config.svi_max_nfev,
        initial_rhos=config.svi_initial_rhos,
        initial_sigmas=config.svi_initial_sigmas,
    )

    prediction_frames = [
        frame for frame in (linear_preds, nearest_preds, svi_preds) if not frame.empty
    ]
    predictions = (
        pd.concat(prediction_frames, ignore_index=True)
        if prediction_frames
        else pd.DataFrame()
    )

    rows = []
    runtimes = {
        "linear_strike": linear_runtime,
        "nearest_strike": nearest_runtime,
        "svi": svi_runtime,
    }

    for model in ("linear_strike", "nearest_strike", "svi"):
        frame = predictions[predictions["model"] == model].copy()
        if frame.empty:
            metrics = {
                "n_targets": len(holdout_ids),
                "n_predictions": 0,
                "coverage": 0.0,
                "rmse": np.nan,
                "mae": np.nan,
                "failure_count": len(holdout_ids),
            }
        else:
            metrics = _evaluate_predictions(
                frame["iv"].to_numpy(),
                frame["prediction"].to_numpy(),
            )

        svi_failure_count = 0
        if model == "svi" and not frame.empty and "fit_success" in frame.columns:
            svi_failure_count = int((~frame["fit_success"].astype(bool)).sum())

        rows.append(
            {
                "model": model,
                "missingness": level,
                "runtime_seconds": float(runtimes[model]),
                "svi_fit_failure_count": svi_failure_count,
                **metrics,
            }
        )

    results = pd.DataFrame(rows)
    return results, predictions
