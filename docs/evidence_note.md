# FinanceMeta — Final Evidence Note and Closeout

## 1. Research question

This checkpoint asks how Linear Strike interpolation, Nearest Strike, and a
bounded raw SVI fit behave when observed NIFTY IV cells are masked at 10%, 20%,
and 30% under a leakage-safe structured holdout.

## 2. Frozen protocol

The exact benchmark configuration is preserved in `config/benchmark_config.json`.
The protocol fixes the chronological 60%/20%/20% split, seed 42, nested matched
10%/20%/30% holdouts, models, metrics, no-retuning policy, and no-holdout-leakage
policy.

The public commit containing both protocol and results does not independently
establish a pre-outcome freeze. This chronology limitation is recorded rather
than inferred away. See `docs/config_provenance.md`.

## 3. Main retained benchmark results

| Model | Missingness | RMSE | MAE | Coverage | Runtime (s) | failure_count |
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

### Interpretation

The recorded RMSE/MAE values are computed only where each model produced a
finite prediction. Because Linear and SVI have different coverage, the table
supports a **conditional model-specific error comparison**, not a matched-target
overall ranking.

On their own successful predictions, Linear has lower reported RMSE and MAE than
SVI at all three missingness levels, while SVI covers more targets.

Nearest Strike has substantially higher conditional error than either approach
at all three levels.

## 4. Failure-count clarification

The retained `failure_count` is `n_targets - n_predictions`. It counts target
rows without a finite prediction. It is not, by itself, a count of distinct SVI
optimizer failures.

The closeout therefore does not claim 0/7/87 distinct optimizer failures without
separate retained fit-level logs.

## 5. Temporal robustness

The retained robustness analysis found an SVI advantage in the early evaluation
regime:

- 10%: SVI RMSE 0.000900 vs Linear 0.001478;
- 20%: SVI 0.000950 vs Linear 0.001667;
- 30%: SVI 0.001069 vs Linear 0.002508.

In the late regime the ranking reversed:

- 10%: Linear 0.020661 vs SVI 0.035207;
- 20%: Linear 0.017563 vs SVI 0.056254;
- 30%: Linear 0.019716 vs SVI 0.055371.

The appropriate conclusion is **regime-sensitive SVI behavior**, not a stable
overall SVI advantage.

## 6. Surface consistency / arbitrage sanity

Basic call-price monotonicity and adjacent-strike convexity checks are retained.
SVI has lower convexity-violation rates than Linear at 20% and 30%, but higher raw
violation counts at both levels. The correct statement is about the rates, not the
raw counts.

No method is formally demonstrated to be globally arbitrage-free. Because the
dataset has one expiry, no calendar-spread test is claimed.

## 7. Common-support comparison

A matched-target ranking would require retained per-target predictions for all
models and explicit missing predictions for failed targets.

No original per-target prediction export was available in the retained project
artifacts used for this closeout. Therefore no new prediction rows or common-
support results are fabricated, and the original aggregate tables are preserved.

Ryan's supplied post-hoc checker is included as `shared_support.py`; it does not
run models or inference. Its bundled synthetic unit suite passes 14 tests.

## 8. Data provenance and rights

The original data source, acquisition route, and redistribution/usage rights are
not verified in the retained public evidence available for this closeout. This
remains an explicit provenance limitation. No source or licence is guessed.

## 9. What worked

- deterministic structured holdout and nested missingness conditions;
- reproducible aggregate benchmark outputs;
- Linear as the lowest-error method on its own successful predictions;
- SVI's higher coverage relative to Linear;
- temporal robustness revealing regime sensitivity rather than a universal
  model winner.

## 10. What failed / limitations

- unequal model coverage prevents the original conditional RMSE/MAE table from
  being interpreted as a matched-target ranking;
- no retained per-target prediction export means the requested common-support
  comparison cannot be computed without new evidence;
- SVI is much slower and produces more missing target predictions as missingness
  rises;
- the single-expiry dataset limits the checkpoint to cross-sectional
  strike/moneyness reconstruction;
- data-source/rights provenance and an independently verifiable pre-outcome
  protocol timestamp are not present in the public submission record.

## 11. Final conclusion

The retained checkpoint does not justify replacing the simple Linear Strike
baseline with SVI on the reported model-specific conditional accuracy table.
SVI trades higher coverage for materially higher runtime and shows an advantage
only in the earlier temporal regime. The later regime reverses that advantage.

The appropriate next research step remains a larger multi-expiry benchmark with
stronger strike and calendar no-arbitrage constraints, but that work is outside
this closeout.
