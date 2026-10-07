"""Run and finalize the FinanceMeta benchmark artifact."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

try:
    from .benchmark import (
        BenchmarkConfig,
        chronological_split,
        build_nested_holdout,
        run_condition,
    )
    from .consistency import consistency_summary
    from .data_utils import prepare_dataset
    from .robustness import temporal_regime_results
except ImportError:
    from benchmark import (
        BenchmarkConfig,
        chronological_split,
        build_nested_holdout,
        run_condition,
    )
    from consistency import consistency_summary
    from data_utils import prepare_dataset
    from robustness import temporal_regime_results


def run(repo_root: str | Path) -> dict[str, pd.DataFrame]:
    root = Path(repo_root)
    results_dir = root / "results"
    figures_dir = results_dir / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    config = BenchmarkConfig.from_json(root / "config" / "benchmark_config.json")
    df = prepare_dataset(root / "data" / "dataset.csv")

    train, validation, evaluation = chronological_split(
        df,
        train_fraction=config.train_fraction,
        validation_fraction=config.validation_fraction,
        evaluation_fraction=config.evaluation_fraction,
    )

    holdouts, manifest = build_nested_holdout(
        evaluation,
        missingness_levels=config.missingness_levels,
        seed=config.seed,
        time_block_count=config.time_block_count,
        moneyness_edges=config.moneyness_edges,
        moneyness_labels=config.moneyness_labels,
    )
    manifest.to_csv(results_dir / "holdout_manifest.csv", index=False)

    all_results = []
    all_predictions = []

    for level in config.missingness_levels:
        result, predictions = run_condition(
            evaluation,
            holdouts[level],
            level=level,
            config=config,
        )
        all_results.append(result)
        if not predictions.empty:
            predictions["missingness"] = level
            all_predictions.append(predictions)

    benchmark = pd.concat(all_results, ignore_index=True)
    predictions = (
        pd.concat(all_predictions, ignore_index=True)
        if all_predictions
        else pd.DataFrame()
    )

    benchmark.to_csv(results_dir / "benchmark_results.csv", index=False)

    consistency = (
        consistency_summary(predictions)
        if not predictions.empty
        else pd.DataFrame()
    )
    consistency.to_csv(results_dir / "consistency_results.csv", index=False)

    robustness = (
        temporal_regime_results(predictions)
        if not predictions.empty
        else pd.DataFrame()
    )
    robustness.to_csv(results_dir / "robustness_results.csv", index=False)

    # Compact summary: model winner by missingness, based on RMSE among finite results.
    if not benchmark.empty:
        summary = benchmark.sort_values(
            ["missingness", "rmse", "mae"],
            na_position="last",
        ).groupby("missingness", as_index=False).first()
    else:
        summary = pd.DataFrame()

    summary.to_csv(results_dir / "model_summary.csv", index=False)

    return {
        "benchmark_results": benchmark,
        "predictions": predictions,
        "consistency_results": consistency,
        "robustness_results": robustness,
        "model_summary": summary,
    }


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    outputs = run(repo_root)
    print(outputs["benchmark_results"].to_string(index=False))
    print("\nConsistency:")
    print(outputs["consistency_results"].to_string(index=False))
    print("\nRobustness:")
    print(outputs["robustness_results"].to_string(index=False))
