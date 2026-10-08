# NIFTY IV Reconstruction — FinanceMeta Checkpoint

A bounded reproducibility and stress-test artifact for reconstructing missing
NIFTY implied-volatility observations. This checkpoint is a research evaluation,
not a trading strategy, live-trading system, or capital-deployment exercise.

## Research question

Under the frozen structured holdout used for this checkpoint, how do Linear
Strike interpolation, Nearest Strike, and a bounded raw SVI volatility-smile fit
behave as controlled missingness increases from 10% to 20% to 30%?

## Scope

The retained dataset contains one expiry. Therefore this checkpoint evaluates
single-expiry cross-sectional strike/moneyness reconstruction over time. It does
not establish multi-expiry term-structure performance or global
arbitrage-freedom.

## Frozen benchmark design

The exact configuration is preserved in `config/benchmark_config.json` and the
full protocol is in `docs/protocol.md`.

Key frozen settings:

- chronological unique-timestamp split: 60% development / 20% validation /
  20% evaluation;
- seed: 42;
- nested structured holdouts: 10%, 20%, 30%;
- same target population nested across missingness levels;
- Linear Strike, Nearest Strike, bounded raw SVI;
- primary metric: RMSE;
- secondary metric: MAE;
- runtime and coverage recorded;
- no per-condition retuning;
- holdout values never supplied to model fitting;
- Linear interpolation does not silently extrapolate outside the observed strike
  bracket.

The exact held-out cells are in `results/holdout_manifest.csv`.

## What the recorded benchmark shows

The retained aggregate tables show the following model-specific conditional
errors:

| Missingness | Linear RMSE | SVI RMSE | Linear MAE | SVI MAE |
|---:|---:|---:|---:|---:|
| 10% | **0.014114** | 0.024243 | **0.005197** | 0.007901 |
| 20% | **0.012079** | 0.039045 | **0.004961** | 0.009482 |
| 30% | **0.013816** | 0.038535 | **0.005886** | 0.009619 |

These errors are computed on each model's own successful predictions. Linear
coverage is 82.00%, 77.20%, and 74.47%; SVI coverage is 100.00%, 99.20%, and
93.39%. Because coverage differs, the table supports the statement that Linear
has lower reported **conditional** RMSE/MAE on its own successful predictions;
it does not, by itself, establish a matched-target superiority claim.

Nearest Strike has substantially larger conditional error at all three levels.

SVI is much slower than Linear in the retained benchmark and its missing-
prediction count rises with missingness. The `failure_count` field in the
retained table is `n_targets - n_predictions`: missing target predictions, not a
count of distinct optimizer fits.

## Temporal robustness

The retained robustness analysis found SVI ahead of Linear in the earlier
evaluation regime, but Linear ahead of SVI in the later regime. The appropriate
conclusion is **regime-sensitive SVI behavior**, not a stable overall SVI
advantage.

## Surface consistency

The benchmark performs basic Black-Scholes call-price strike monotonicity and
adjacent-strike convexity sanity checks. SVI has lower convexity-violation rates
than Linear at 20% and 30%, although its raw violation counts are higher at both
levels. These checks are not a formal global no-arbitrage proof, and no calendar
check is claimed because the dataset has one expiry.

## Data provenance and rights

The original dataset source, acquisition route, and redistribution/usage rights
are **not verified in the retained repository evidence available for this
closeout**. Repository presence alone does not establish those rights. This is
recorded as an unresolved provenance limitation rather than guessed.

## Protocol chronology

The exact benchmark configuration used for the recorded results has been
recovered and is now tracked in the repository. However, the public submitted
commit combined the protocol and results, so it does not independently prove a
pre-outcome freeze. See `docs/config_provenance.md` for the precise status.

## Common-support comparison

A matched-target comparison would require retained per-target predictions with
explicit missing predictions. No such original export is available in this
closeout package. Therefore no new common-support result is invented. Ryan's
post-hoc checker is included as `shared_support.py`; its synthetic test suite
passes separately.

See `docs/closeout_status.md` for the full review disposition.

## Reproduction of the historical checkpoint

The repository now contains the exact recovered configuration, so a future
fresh run is mechanically reproducible from code and config. It must **not** be
represented as proof of the original historical run chronology.

For a fresh run:

```bash
pip install -r requirements.txt
python run_benchmark.py
```

The fresh run creates new outputs. Do not overwrite or relabel the retained
historical outputs as newly generated evidence.

## Review checker

Ryan's supplied checker is included for any future recovery of the original
per-target predictions:

```bash
python -m unittest -v test_shared_support.py
python shared_support.py retained_predictions.csv --out new_posthoc_review
```

The checker is post-hoc only: it does not fetch data, train models, or run
inference, and it refuses to overwrite an existing output directory.

## Final research conclusion

The recorded checkpoint does not support replacing the simple Linear Strike
baseline with SVI on the model-specific aggregate accuracy table. SVI offers
higher coverage and can outperform Linear in the early temporal regime, but its
advantage is not stable later and its computational/calibration burden rises
with missingness.

The next research step remains a larger multi-expiry benchmark with stronger
term-structure and no-arbitrage constraints, but that is explicitly outside this
closeout.
