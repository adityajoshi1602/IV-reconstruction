# FinanceMeta — Final Evidence Note

## 1. Research question

**Primary:** Under a leakage-safe structured holdout, when does an SVI-style
volatility-smile fit outperform simpler IV reconstruction baselines?

**Secondary:** How do reconstruction error, coverage, runtime, and failure rate
change as controlled missingness increases from 10% to 20% to 30%?

**Robustness:** Are the model rankings stable across temporally separated
evaluation regimes?

## 2. Frozen protocol

The benchmark was run under the frozen protocol in `docs/protocol.md`.

- Chronological unique-timestamp split: 60% development / 20% validation / 20% evaluation.
- Seed: 42.
- Nested matched holdouts: 10%, 20%, 30%.
- Same target population is nested across missingness levels.
- Models: Linear Strike, Nearest Strike, raw SVI.
- Primary metric: RMSE.
- Secondary metric: MAE.
- No per-condition retuning.
- Holdout values are not supplied to model fitting.
- Linear interpolation does not silently extrapolate beyond the observed strike range.

## 3. Dataset and scope

The benchmark uses the repository's `data/dataset.csv`.

The current EDA identifies a single expiry with multiple timestamped strikes and
CE/PE IV observations. Therefore this checkpoint is a **single-expiry,
cross-sectional strike/moneyness reconstruction study**, not a full
multi-expiry term-structure benchmark.

**Data source / rights:** insert the verified original source, acquisition
route, and redistribution/usage rights here before submission. Do not infer
rights from repository presence alone.

## 4. Main benchmark result

| Model | Missingness | RMSE | MAE | Coverage | Runtime (s) | Failures |
|---|---:|---:|---:|---:|---:|---:|
| Linear Strike | 10% | 0.014114 | 0.005197 | 82.00% | 0.514 | 79 |
| Nearest Strike | 10% | 0.077078 | 0.038354 | 100.00% | 0.559 | 0 |
| SVI | 10% | 0.024243 | 0.007901 | 100.00% | 37.775 | 0 |
| Linear Strike | 20% | 0.012079 | 0.004961 | 77.20% | 0.601 | 200 |
| Nearest Strike | 20% | 0.090699 | 0.043305 | 100.00% | 0.641 | 0 |
| SVI | 20% | 0.039045 | 0.009482 | 99.20% | 50.821 | 7 |
| Linear Strike | 30% | 0.013816 | 0.005886 | 74.47% | 0.677 | 336 |
| Nearest Strike | 30% | 0.102487 | 0.048728 | 100.00% | 0.614 | 0 |
| SVI | 30% | 0.038535 | 0.009619 | 93.39% | 54.388 | 87 |

### Main finding

**SVI did not beat Linear Strike interpolation overall.**

Linear Strike achieved the lowest RMSE and MAE at all three missingness levels:

- 10%: Linear RMSE 0.014114 vs SVI 0.024243.
- 20%: Linear RMSE 0.012079 vs SVI 0.039045.
- 30%: Linear RMSE 0.013816 vs SVI 0.038535.

Nearest Strike was substantially worse on error at every level.

The important trade-off is coverage: Linear Strike coverage declined from
82.00% to 74.47%, while SVI remained at 100.00%, 99.20%, and 93.39%.

SVI was also much more expensive computationally: roughly 74–85x the Linear
runtime across the three missingness levels.

## 5. SVI failure behavior

SVI fit failures increased as missingness increased:

- 10%: 0 failures.
- 20%: 7 failures.
- 30%: 87 failures.

This indicates increasing calibration fragility as the observed smile becomes
sparser.

## 6. Robustness / regime sensitivity

The temporal robustness check changes the interpretation.

### Early evaluation regime

| Missingness | Linear RMSE | SVI RMSE | Better |
|---:|---:|---:|---|
| 10% | 0.001478 | **0.000900** | SVI |
| 20% | 0.001667 | **0.000950** | SVI |
| 30% | 0.002508 | **0.001069** | SVI |

### Late evaluation regime

| Missingness | Linear RMSE | SVI RMSE | Better |
|---:|---:|---:|---|
| 10% | **0.020661** | 0.035207 | Linear |
| 20% | **0.017563** | 0.056254 | Linear |
| 30% | **0.019716** | 0.055371 | Linear |

Therefore:

> **SVI has a conditional advantage in the earlier evaluation regime,
> but that advantage does not persist in the later regime.**

This is evidence of regime sensitivity rather than a stable overall SVI
advantage.

## 7. Surface-consistency / arbitrage sanity checks

The benchmark uses basic Black-Scholes call-price checks after reconstruction.

| Model | Missingness | Monotonicity violations | Monotonicity rate | Convexity violations | Convexity rate |
|---|---:|---:|---:|---:|---:|
| Linear Strike | 10% | 1 | 1.56% | 6 | 35.29% |
| Linear Strike | 20% | 2 | 1.18% | 11 | 16.18% |
| Linear Strike | 30% | 5 | 1.61% | 31 | 19.14% |
| Nearest Strike | 10% | 15 | 17.44% | 5 | 20.83% |
| Nearest Strike | 20% | 43 | 16.80% | 27 | 21.95% |
| Nearest Strike | 30% | 74 | 15.91% | 64 | 22.30% |
| SVI | 10% | 5 | 5.81% | 5 | 20.83% |
| SVI | 20% | 6 | 2.38% | 18 | 15.00% |
| SVI | 30% | 10 | 2.39% | 45 | 17.79% |

Interpretation:

- Nearest Strike has the highest monotonicity-violation rate.
- Linear has the lowest monotonicity-violation rate in this benchmark.
- SVI has fewer convexity violations than Linear at 20% and 30%.
- No method is formally demonstrated to be globally arbitrage-free.

Because the dataset has one expiry, no meaningful calendar-spread check is
claimed.

## 8. What worked

1. The frozen nested holdout produced a reproducible comparison across 10%,
   20%, and 30% missingness.
2. Linear Strike interpolation was the most accurate method on the overall
   benchmark RMSE/MAE.
3. SVI substantially improved error over Nearest Strike.
4. SVI maintained much higher coverage than Linear Strike.
5. The temporal robustness test identified a clear change in model ranking
   between earlier and later evaluation regimes.

## 9. What failed / limitations

1. Linear interpolation loses coverage as missingness increases because some
   held-out targets are not bracketed by remaining observed strikes.
2. SVI is much slower than the simple methods.
3. SVI calibration failures increase materially at 30% missingness.
4. The overall SVI advantage is not robust across the temporal split.
5. The single-expiry dataset limits conclusions about full volatility-surface
   and term-structure behavior.
6. The arbitrage analysis is a basic sanity check rather than a global
   no-arbitrage proof.

## 10. What I would test next

The highest-value next experiment is a **multi-expiry benchmark** with a larger
sample. It should test whether the conditional SVI advantage seen in the
earlier regime generalizes across expiries and volatility regimes, and should
add calendar-spread constraints alongside stronger strike-wise no-arbitrage
constraints.

## 11. Final conclusion

For this checkpoint, the evidence does **not** support replacing simple linear
strike interpolation with SVI on overall predictive accuracy.

A more nuanced conclusion is:

> **Linear interpolation is the strongest accuracy baseline on this dataset,
> while SVI trades substantially higher runtime for higher coverage and can
> outperform Linear during the earlier evaluation regime. The advantage is not
> stable in the later regime and becomes harder to calibrate as missingness
> increases.**
