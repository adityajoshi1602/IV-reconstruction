# Start Here — FinanceMeta Checkpoint Closeout

This package repairs and documents the existing checkpoint. It does not create
a new benchmark or retune any model.

## 1. Copy into the repository

Merge these files into the existing `IV-reconstruction` repository root.
Keep the original `data/dataset.csv` unchanged.

The important restored file is:

`config/benchmark_config.json`

The configuration is now intended to remain tracked by Git.

## 2. Validate the artifact

```bash
python scripts/validate_artifact.py
```

Expected:

```text
VALIDATION PASSED
```

## 3. Validate Ryan's post-hoc checker

```bash
python -m unittest -v test_shared_support.py
```

Expected: 14 tests passing.

## 4. Do not manufacture common-support results

A retained per-target prediction export was not available in the closeout
artifacts. Therefore do not create replacement prediction rows and call them
historical evidence.

If the original export is recovered later, use:

```bash
python shared_support.py retained_predictions.csv --out new_posthoc_review
```

The input must include:

`missingness,observation_id,model,iv,prediction`

and must preserve explicit blank/NaN predictions for failed targets.

## 5. Verify data provenance before sending the final email

`README.md` and `docs/evidence_note.md` intentionally state that the original
data source, acquisition route, and usage/redistribution rights are not
verified in the retained public evidence.

Replace that wording only when you have documentary evidence for the real source
and rights. Do not guess.

## 6. Final Git checks

```bash
git status
git diff -- data/dataset.csv
```

The dataset should remain unchanged.

Then:

```bash
git add .
git commit -m "Close FinanceMeta reproducibility review"
git push origin main
```

## 7. Final response to Ryan

Use the closeout email drafted in `docs/RYAN_CLOSEOUT_EMAIL.md` after the
provenance status is verified.
