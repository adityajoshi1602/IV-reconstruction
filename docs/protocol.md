# Frozen Research Protocol — NIFTY IV Reconstruction Benchmark

## 1. Research questions

### Primary
Under a leakage-safe holdout, when does an SVI-style volatility-smile fit outperform simpler IV reconstruction baselines?

### Secondary
How do reconstruction error, coverage, runtime, and failure rate change as controlled missingness increases from 10% to 20% to 30%?

### Robustness
Are the relative model results stable across temporally separated market conditions?

## 2. Scope

This is a bounded reproducibility/stress-test study. It is not a trading strategy, live-trading system, or capital-deployment exercise.

The repository dataset is a single-expiry NIFTY option dataset. Therefore, this checkpoint evaluates cross-sectional strike/moneyness reconstruction over time. A meaningful calendar/term-structure arbitrage test is outside this checkpoint and is treated as a limitation/future test.

## 3. Raw data

Canonical raw file:

`data/dataset.csv`

The raw file is treated as read-only by the benchmark.

The benchmark records dataset provenance and redistribution/usage rights in the final README/evidence note from the verified original source information. No rights are inferred from the repository alone.

## 4. Canonical observation unit

Each observed IV cell is represented by:

- timestamp
- option symbol
- expiry
- strike
- option type
- underlying price
- log-moneyness
- IV
- deterministic `observation_id`

An evaluation target is an originally observed IV cell that is intentionally masked after the split and holdout protocol is frozen.

## 5. Chronological split

Unique timestamps are sorted ascending and split chronologically:

- first 60% of unique timestamps: development/training period
- next 20%: validation period
- final 20%: evaluation period

The split rule is frozen before final comparative results are inspected.

No evaluation-period target value is used to fit a model.

## 6. Structured nested holdout

A master 30% holdout is generated only from originally observed IV cells in the evaluation period.

Eligibility is stratified by:

- option type
- moneyness bin
- one of five deterministic time blocks

Moneyness bins use fixed `log_moneyness` edges:

- left wing: `(-inf, -0.05)`
- left near-ATM: `[-0.05, -0.01)`
- ATM: `[-0.01, 0.01]`
- right near-ATM: `(0.01, 0.05]`
- right wing: `(0.05, inf)`

The 10% and 20% conditions are nested subsets of the 30% condition:

`H10 ⊂ H20 ⊂ H30`

The same target population is therefore matched across conditions, rather than drawing three unrelated test samples.

Selection is deterministic from the frozen seed (42) and a stable hash of `observation_id`; no result-dependent selection is permitted.

## 7. Missingness conditions

The benchmark evaluates:

- 10% masked
- 20% masked
- 30% masked

The missingness level is applied only to the predefined holdout targets. Existing natural missing values remain missing and are not converted into pseudo-ground truth.

No model parameter, optimizer bound, or reconstruction rule is changed between missingness conditions.

## 8. Models

### Baseline A — Linear strike interpolation
For each timestamp/expiry/option-type slice, predict a masked strike from the remaining observed strikes with linear interpolation.

Extrapolation outside the observed strike range is disabled by protocol. Such targets are recorded as prediction failures rather than silently extrapolated.

### Baseline B — Nearest observed strike
For each timestamp/expiry/option-type slice, use the IV at the nearest remaining observed strike.

### Model C — Raw SVI
Fit raw SVI to total implied variance as a function of log-moneyness using only the remaining observed training points in the same timestamp/expiry/option-type slice.

The SVI optimizer, parameter bounds, initialization set, minimum point count, and maximum function evaluations are frozen in `config/benchmark_config.json`.

Holdout values are never supplied to the SVI calibration.

## 9. Primary and secondary metrics

Primary metric:

`RMSE`

Secondary metric:

`MAE`

Additional diagnostics:

- prediction coverage
- failure count/rate
- runtime
- basic surface-consistency/arbitrage sanity checks

Metrics are computed only where a model produces a finite prediction. Coverage is reported separately so lower error cannot be obtained by silently dropping difficult targets.

## 10. Runtime measurement

Runtime is measured with a monotonic high-resolution timer around each complete model/condition evaluation.

All models are run in the same environment and on the same machine/session where possible.

## 11. Failure policy

Failures are preserved and categorized rather than replaced with another model.

Examples:

- insufficient observed strikes
- target outside interpolation bracket
- SVI insufficient points
- SVI optimizer failure
- invalid/non-positive fitted total variance
- non-finite prediction

## 12. Surface-consistency sanity check

For reconstructed IVs, the benchmark will later convert IVs to Black-Scholes call prices using explicitly documented assumptions and check basic:

- strike-price monotonicity
- adjacent-strike convexity

These are sanity checks, not a formal proof of global arbitrage freedom.

Because the checkpoint contains one expiry, no meaningful calendar-spread condition is claimed.

## 13. Robustness check

A temporal robustness comparison is performed using the frozen chronological structure. Performance is compared between earlier and later portions of the evaluation sample without changing model settings.

The robustness analysis is descriptive and does not permit protocol changes based on observed results.

## 14. Reproducibility

Frozen settings:

- seed: 42
- split: 60% / 20% / 20% by unique timestamp
- missingness: 10% / 20% / 30%
- nested holdouts: yes
- primary metric: RMSE
- per-condition retuning: no
- evaluation values used for fitting: no

The exact held-out cell membership is saved to `results/holdout_manifest.csv`.

## 15. Reporting rule

The benchmark will report positive, negative, and inconclusive findings without selecting a preferred conclusion in advance.

The final evidence note must explicitly state:

1. what worked
2. what failed
3. whether/when SVI beat simpler baselines
4. how error changed with missingness
5. runtime and failure behavior
6. robustness result
7. limitations
8. next experiment to run
