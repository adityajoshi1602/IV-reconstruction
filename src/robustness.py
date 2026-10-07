"""Temporal robustness analysis for the frozen benchmark results."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


def _metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    actual = frame["iv"].to_numpy(dtype=float)
    pred = frame["prediction"].to_numpy(dtype=float)
    finite = np.isfinite(actual) & np.isfinite(pred)
    n = int(finite.sum())
    targets = int(len(frame))
    if n == 0:
        return {
            "n_targets": targets,
            "n_predictions": 0,
            "coverage": 0.0,
            "rmse": np.nan,
            "mae": np.nan,
        }
    return {
        "n_targets": targets,
        "n_predictions": n,
        "coverage": n / targets if targets else np.nan,
        "rmse": float(np.sqrt(mean_squared_error(actual[finite], pred[finite]))),
        "mae": float(mean_absolute_error(actual[finite], pred[finite])),
    }


def temporal_regime_results(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compare earlier/later halves of the frozen evaluation predictions."""
    if predictions.empty:
        return pd.DataFrame()

    unique_times = np.array(sorted(pd.to_datetime(predictions["datetime"]).unique()))
    if len(unique_times) < 4:
        raise ValueError("Need at least four unique timestamps for robustness split.")

    split_idx = len(unique_times) // 2
    early = set(unique_times[:split_idx])
    later = set(unique_times[split_idx:])

    work = predictions.copy()
    work["datetime"] = pd.to_datetime(work["datetime"])
    work["regime"] = np.where(
        work["datetime"].isin(early),
        "early_evaluation",
        "late_evaluation",
    )

    rows = []
    for (model, missingness, regime), group in work.groupby(
        ["model", "missingness", "regime"],
        sort=True,
        observed=True,
    ):
        rows.append(
            {
                "model": model,
                "missingness": missingness,
                "regime": regime,
                **_metrics(group),
            }
        )
    return pd.DataFrame(rows)
