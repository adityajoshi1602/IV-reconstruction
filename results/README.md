# Result files

These files are the retained outputs from the original checkpoint.

- `benchmark_results.csv` — aggregate model-specific conditional metrics,
  coverage, runtime, and missing-prediction counts.
- `robustness_results.csv` — early/late temporal robustness results.
- `consistency_results.csv` — basic strike-wise call-price monotonicity and
  convexity sanity checks.
- `holdout_manifest.csv` — deterministic held-out target membership.
- `model_summary.csv` — compact model summary.

## Important interpretation

The recorded RMSE/MAE values are computed only where each model produced a
finite prediction. Because Linear and SVI have different coverage, these are
**conditional model-specific prediction errors**. They do not by themselves
establish a matched-target ranking.

The `failure_count` column in `benchmark_results.csv` is the number of target
rows without a finite prediction (`n_targets - n_predictions`). It is not a
count of distinct optimizer failures.

No retained per-target prediction export is included in this checkpoint, so a
real common-support post-hoc comparison cannot be computed without generating
new evidence. New prediction rows are intentionally not presented as historical
results.
