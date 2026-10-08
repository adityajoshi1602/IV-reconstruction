# Frozen Research Protocol — NIFTY IV Reconstruction Benchmark

## 1. Research questions

### Primary
Under a leakage-safe structured holdout, how do an SVI-style volatility-smile
fit and simpler IV reconstruction baselines compare?

### Secondary
How do reconstruction error, prediction coverage, runtime, and missing-prediction
behavior change as controlled missingness increases from 10% to 20% to 30%?

### Robustness
Are the relative model results stable across temporally separated evaluation
regimes?

## 2. Scope

This is a bounded reproducibility/stress-test study. It is not a trading
strategy, live-trading system, or capital-deployment exercise.

The retained dataset has one expiry. The checkpoint therefore evaluates
cross-sectional strike/moneyness reconstruction over time. It does not establish
multi-expiry term-structure performance or global arbitrage-freedom.

## 3. Data and rights

Canonical raw file: `data/dataset.csv`.

The raw file is treated as read-only by the benchmark.

The original external data source, acquisition route, and redistribution/usage
rights are not independently verified in the retained public evidence available
for this closeout. No rights are inferred from repository presence.

## 4. Chronological split

Unique timestamps are sorted ascending:

- first 60%: development/training period;
- next 20%: validation period;
- final 20%: evaluation period.

No evaluation-period target value is used to fit a model.

## 5. Structured nested holdout

A master 30% holdout is generated only from originally observed IV cells in the
evaluation period. Eligibility is stratified by:

- option type;
- fixed log-moneyness bin;
- one of five deterministic time blocks.

The 10% and 20% conditions are nested subsets of the 30% condition:

`H10 ⊂ H20 ⊂ H30`

Selection is deterministic from seed 42 and a stable hash of `observation_id`.
The exact membership is stored in `results/holdout_manifest.csv`.

## 6. Missingness conditions

The benchmark evaluates 10%, 20%, and 30% masking. Existing natural missing
values remain missing and are not treated as pseudo-ground truth.

No model setting is changed between missingness conditions.

## 7. Models

### Linear Strike interpolation

Predict a masked strike from remaining observed strikes within the same
 timestamp/expiry/option-type slice using linear interpolation. Extrapolation is
disabled. Unsupported targets are recorded as missing predictions.

### Nearest Strike

Use the IV at the nearest remaining observed strike.

### Raw SVI

Fit raw SVI to total implied variance as a function of log-moneyness using only
remaining observed training points. Optimizer bounds, initialization set,
minimum point count, and function-evaluation limit are frozen in
`config/benchmark_config.json`.

## 8. Evaluation metrics

Primary: RMSE.

Secondary: MAE.

Additional diagnostics:

- prediction coverage;
- missing-prediction count;
- runtime;
- strike-wise monotonicity/convexity sanity checks;
- temporal robustness.

RMSE/MAE in the retained aggregate benchmark are calculated only on each
model's finite predictions. Therefore the recorded errors are conditional on
model-specific successful prediction subsets. A matched-target ranking requires
a separate common-support calculation on retained per-target predictions.

## 9. Failure terminology

`failure_count` in the retained aggregate result table means the number of target
rows without a finite prediction (`n_targets - n_predictions`). It is not a
count of distinct optimizer failures.

Fit-level optimizer failures are only claimed when separately retained fit logs
establish them.

## 10. Runtime

Runtime is measured around each complete model/condition evaluation using a
monotonic high-resolution timer under the same environment/session where
possible.

## 11. Surface consistency

Reconstructed IVs are converted to Black-Scholes call prices under the documented
assumptions and checked for:

- strike-price monotonicity;
- adjacent-strike convexity.

These are sanity checks, not a formal proof of global arbitrage freedom. With one
expiry, no calendar-spread condition is claimed.

## 12. Robustness

The evaluation sample is compared between earlier and later temporal regimes
using the frozen model settings. No retuning is allowed after inspecting the
results.

## 13. Configuration provenance

The exact configuration used for the retained benchmark has been recovered and
is now tracked at `config/benchmark_config.json`.

The public submitted commit that combined protocol and results does not by itself
prove a pre-outcome freeze. The chronology is therefore reported as not
independently verifiable from the public commit alone. No replacement settings
have been reconstructed from observed outcomes.

## 14. Post-hoc common-support audit

If the original per-target prediction export is later recovered, it may be
analysed with the supplied `shared_support.py` checker. The input must contain
one row per model/target/condition, including explicit blank/NaN predictions for
failed targets.

Any resulting common-support metrics must be labelled **post-hoc** and must not
replace the original aggregate benchmark table.
