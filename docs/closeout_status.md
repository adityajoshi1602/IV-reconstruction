# FinanceMeta Checkpoint Closeout Status

This document records the state of the existing checkpoint after source review.
No new model training, tuning, larger dataset, or new benchmark is introduced.

| Review item | Status | Treatment |
|---|---|---|
| Exact benchmark configuration | Recovered | `config/benchmark_config.json` is restored and tracked. |
| Pre-outcome protocol freeze | Not independently verified | State this limitation; do not invent chronology. |
| Original benchmark results | Preserved | Existing result tables remain the recorded outputs. |
| Model-specific conditional RMSE/MAE | Corrected in interpretation | Reported as conditional on each model's finite predictions. |
| Common-support metrics | Not available | No retained per-target prediction export was found in the project artifacts available for this closeout; no new rows are fabricated. |
| Coverage | Preserved | Keep beside conditional error metrics. |
| Failure count semantics | Corrected | `failure_count` means target rows without a finite prediction, not distinct optimizer fits. |
| SVI calibration failures | Not claimed at fit level | Distinct fit failures require separate retained fit logs. |
| Surface consistency wording | Corrected | SVI has lower convexity-violation *rates* at 20% and 30%, despite higher raw counts. |
| Data source / rights | Unverified | Do not state a source, acquisition route, or licence basis without evidence. |

## Reporting rule

The final evidence preserves the original negative result but does not overstate
what the unequal model coverage establishes. The correct primary comparison is
model-specific successful-prediction error; a matched-target superiority claim
requires an existing retained per-target prediction export and a separate
post-hoc common-support calculation.
