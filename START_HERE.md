# START HERE

You already have the original repository and `data/dataset.csv`.

## 1. Copy this package into your existing repository

Keep your original `data/dataset.csv` unchanged.

## 2. Open a terminal in the repository root

## 3. Create and activate a virtual environment

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run ONE command

```bash
python run_benchmark.py
```

You do not need to run internal source files yourself.

The command validates the project, runs the frozen benchmark, generates figures,
and validates the output again.

## 6. Inspect

```text
results/benchmark_results.csv
results/consistency_results.csv
results/robustness_results.csv
results/holdout_manifest.csv
results/model_summary.csv
```

Then open:

```text
docs/evidence_note.md
notebooks/02_reproducible_benchmark.ipynb
```

## 7. Before submission

Fill the verified data-source/rights information and final interpretation in
`README.md` and `docs/evidence_note.md`.

Then run:

```bash
python scripts/validate_artifact.py
```

You want:

```text
VALIDATION PASSED
```

Finally:

```bash
git add .
git commit -m "Add leakage-safe IV reconstruction benchmark"
git push origin main
```
