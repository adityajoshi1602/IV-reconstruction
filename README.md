# NIFTY IV Surface Reconstruction — FinanceMeta Reproducible Benchmark

This repository contains a bounded reproducibility/stress-test benchmark for
reconstructing missing NIFTY implied-volatility observations.

## Research question

Under a leakage-safe structured holdout, when does an SVI-style volatility-smile
fit outperform simpler interpolation baselines?

Secondary question: how do error, coverage, runtime, and failures change as
controlled missingness increases from 10% to 20% to 30%?

## Final finding

**SVI did not beat Linear Strike interpolation on overall RMSE or MAE at any
tested missingness level.**

| Missingness | Linear RMSE | SVI RMSE | Linear MAE | SVI MAE |
|---:|---:|---:|---:|---:|
| 10% | **0.014114** | 0.024243 | **0.005197** | 0.007901 |
| 20% | **0.012079** | 0.039045 | **0.004961** | 0.009482 |
| 30% | **0.013816** | 0.038535 | **0.005886** | 0.009619 |

However, Linear coverage declined from 82.00% to 74.47%, while SVI coverage
was 100.00%, 99.20%, and 93.39%.

SVI also required roughly 74–85x the Linear runtime in the three benchmark
conditions and had 0, 7, and 87 calibration failures as missingness increased.

## Robustness result

The temporal robustness test found that SVI **did outperform Linear during the
early evaluation regime**, but Linear outperformed SVI during the later regime.

This means the evidence supports **conditional/regime-sensitive SVI behavior**,
not a stable overall SVI advantage.

## Models

1. Linear Strike interpolation
2. Nearest Strike baseline
3. Bounded raw SVI fit

## Frozen protocol

See [`docs/protocol.md`](docs/protocol.md).

- chronological split: 60% / 20% / 20% by unique timestamp
- seed: 42
- nested matched holdouts: 10%, 20%, 30%
- same target population across missingness conditions
- RMSE as primary metric
- MAE as secondary metric
- no per-condition retuning
- holdout values excluded from fitting

## Results

Machine-readable outputs:

- [`results/benchmark_results.csv`](results/benchmark_results.csv)
- [`results/consistency_results.csv`](results/consistency_results.csv)
- [`results/robustness_results.csv`](results/robustness_results.csv)
- [`results/holdout_manifest.csv`](results/holdout_manifest.csv)

Research summary:

- [`docs/evidence_note.md`](docs/evidence_note.md)

Main notebook:

- [`notebooks/02_reproducible_benchmark.ipynb`](notebooks/02_reproducible_benchmark.ipynb)

## Scope limitation

The current repository dataset contains one expiry. This checkpoint therefore
evaluates single-expiry cross-sectional strike/moneyness reconstruction. It
does not establish multi-expiry term-structure performance or global
arbitrage-freedom.

## Data provenance and rights

Before submission, insert the verified original data source, acquisition route,
and redistribution/usage rights. Do not infer these rights from repository
presence alone.

## Reproduction

Create/activate a virtual environment, then:

```bash
pip install -r requirements.txt
python run_benchmark.py
```

The runner validates the artifact, executes the frozen benchmark, produces the
result tables/figures, and validates the outputs again.

## Next step

Test the conditional SVI result on a larger multi-expiry dataset with stronger
calendar and strike no-arbitrage constraints.

## Author

Aditya Joshi
