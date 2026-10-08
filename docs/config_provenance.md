# Configuration and Run Provenance

## Exact benchmark configuration

The exact configuration used for the benchmark results was recovered from a
retained project artifact created before the post-result package was assembled.
The recovered file is:

`config/benchmark_config.json`

SHA-256 of the recovered file:

`238ded45a6b357040a2c098046c0d0f83aadd3c3244f3ecd5bc531a66313012c`

The configuration specifies the frozen seed, chronological split, nested
10%/20%/30% holdouts, model settings, primary/secondary metrics, and no-retuning
and no-leakage policies. It is included in the repository so the submitted
runner no longer depends on an ignored local directory.

## Chronology status

The configuration artifact was retained before the final result-update package
was created in the project work session. However, the public repository commit
containing the protocol and results does not independently establish a
pre-outcome freeze. No stronger timestamped evidence is claimed here.

Therefore:

- the exact configuration used for the reported benchmark is preserved;
- the benchmark chronology is documented as **not independently verifiable
  from the public commit alone**;
- no replacement configuration has been reconstructed from observed results;
- no new benchmark run is presented as historical evidence.

## Original submitted results

The numerical result files already submitted are preserved. The correction work
changes reporting/documentation, not the recorded benchmark outcomes.
