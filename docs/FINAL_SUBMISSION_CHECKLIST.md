# Final Submission Checklist — FinanceMeta Closeout

## Completed repairs

- [x] Exact retained `config/benchmark_config.json` restored and tracked.
- [x] `.gitignore` no longer excludes `config/`.
- [x] Existing benchmark result tables preserved.
- [x] Conditional RMSE/MAE interpretation corrected for unequal coverage.
- [x] `failure_count` documented as missing target predictions, not optimizer fits.
- [x] Surface-consistency wording corrected to distinguish rates from raw counts.
- [x] Common-support limitation explicitly documented because no retained per-target export was available.
- [x] Ryan's supplied 14-test post-hoc checker included and tested.
- [x] Protocol chronology limitation documented; no unsupported pre-outcome freeze claim.

## Before pushing

- [ ] Confirm the original dataset source, acquisition route, and usage/redistribution rights from documentary evidence. Update `README.md` and `docs/evidence_note.md` only when verified.
- [ ] Confirm `data/dataset.csv` is unchanged.
- [ ] Run `python scripts/validate_artifact.py` from the repository that contains the original `data/dataset.csv`.
- [ ] Run `python -m unittest -v test_shared_support.py`.
- [ ] Review `docs/closeout_status.md`.
- [ ] Commit and push the closeout repair.
- [ ] Send Ryan the closeout email in `docs/RYAN_CLOSEOUT_EMAIL.md`.

## Do not do

- [ ] Do not rerun models solely to create historical common-support evidence.
- [ ] Do not fabricate or backfill the original prediction export.
- [ ] Do not reconstruct a replacement config from observed outcomes.
- [ ] Do not tune SVI or expand the study before this checkpoint is accepted.
