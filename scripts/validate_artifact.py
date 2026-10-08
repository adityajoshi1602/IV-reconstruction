"""Static validation for the FinanceMeta benchmark repository."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


REQUIRED_FILES = [
    "data/dataset.csv",
    "src/data_utils.py",
    "src/interpolation.py",
    "src/svi.py",
    "src/benchmark.py",
    "config/benchmark_config.json",
    "docs/protocol.md",
    "docs/evidence_note.md",
    "notebooks/00_eda.ipynb",
    "notebooks/01_baseline_modeling.ipynb",
    "notebooks/02_reproducible_benchmark.ipynb",
    "results/holdout_manifest.csv",
    "results/benchmark_results.csv",
    "README.md",
    "requirements.txt",
    "requirements-lock.txt",
    "config/benchmark_config.json",
    "results/consistency_results.csv",
    "results/robustness_results.csv",
    "results/model_summary.csv",
    "run_benchmark.py",
    "docs/closeout_status.md",
]


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"Missing required file: {rel}")

    cfg_path = root / "config/benchmark_config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            levels = cfg["holdout"]["missingness_levels"]
            if levels != [0.10, 0.20, 0.30]:
                errors.append(f"Unexpected missingness levels: {levels}")
            if cfg["seed"] != 42:
                errors.append("Benchmark seed is not 42.")
            if cfg["policy"]["retune_per_missingness_level"]:
                errors.append("Protocol permits retuning per missingness level.")
            if cfg["policy"]["use_holdout_values_for_fitting"]:
                errors.append("Protocol permits holdout leakage.")
        except Exception as exc:
            errors.append(f"Invalid benchmark config: {exc}")

    for notebook in [
        "notebooks/00_eda.ipynb",
        "notebooks/01_baseline_modeling.ipynb",
        "notebooks/02_reproducible_benchmark.ipynb",
    ]:
        path = root / notebook
        if path.exists():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"Invalid notebook JSON: {notebook}: {exc}")

    for csv_file, required in [
        ("results/holdout_manifest.csv", ["observation_id"]),
        ("results/benchmark_results.csv", ["model", "missingness", "rmse", "mae"]),
    ]:
        path = root / csv_file
        if path.exists():
            try:
                df = pd.read_csv(path)
                missing = [c for c in required if c not in df.columns]
                if missing:
                    errors.append(f"{csv_file} missing columns: {missing}")
            except Exception as exc:
                errors.append(f"Unreadable CSV {csv_file}: {exc}")

    # Confirm that the frozen configuration is parseable and retained.
    if cfg_path.exists():
        try:
            json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print("-", error)
        raise SystemExit(1)
    print("VALIDATION PASSED")
