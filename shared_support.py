#!/usr/bin/env python3
"""Audit *retained* prediction exports without running or modifying any model.

Required CSV columns: missingness, observation_id, model, iv, prediction.
Export one row per model/target, including explicit blank/NaN predictions for
failed targets. Missing rows are export errors, not assumed model failures.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping

COLUMNS = ("missingness", "observation_id", "model", "iv", "prediction")
MISSING = {"", "nan", "na", "n/a", "null", "none"}


def number(value: object, *, missing_allowed: bool = False) -> float | None:
    text = "" if value is None else str(value).strip()
    if missing_allowed and text.lower() in MISSING:
        return None
    try:
        result = float(text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"Non-finite numeric value: {value!r}")
    return result


def metrics(errors: Iterable[float]) -> dict:
    errors = list(errors)
    if not errors:
        return {"n": 0, "rmse": None, "mae": None}
    return {"n": len(errors),
            "rmse": math.hypot(*errors) / math.sqrt(len(errors)),
            "mae": math.fsum(abs(e) for e in errors) / len(errors)}


def audit(rows: Iterable[Mapping[str, object]]) -> dict:
    groups: dict[str, dict[str, dict[str, tuple[float, float | None]]]] = {}
    count = 0
    for row_number, row in enumerate(rows, 2):
        missing_columns = set(COLUMNS) - set(row)
        if missing_columns:
            raise ValueError(f"Row {row_number}: missing columns {sorted(missing_columns)}")
        condition, oid, model = (str(row[k] or "").strip() for k in COLUMNS[:3])
        if not all((condition, oid, model)):
            raise ValueError(f"Row {row_number}: condition, observation_id and model are required")
        actual = number(row["iv"])
        pred = number(row["prediction"], missing_allowed=True)
        by_model = groups.setdefault(condition, {}).setdefault(model, {})
        if oid in by_model:
            raise ValueError(f"Duplicate model/target row: {(condition, model, oid)!r}")
        by_model[oid] = (actual, pred)
        count += 1
    if not groups:
        raise ValueError("No prediction rows")
    model_set = set().union(*(set(g) for g in groups.values()))
    if len(model_set) < 2:
        raise ValueError("At least two models are required for a comparison")
    results = []
    for condition, models in sorted(groups.items()):
        if set(models) != model_set:
            raise ValueError(f"Condition {condition}: missing model export")
        names = sorted(models)
        target_ids = set().union(*(set(v) for v in models.values()))
        for name in names:
            absent = target_ids - set(models[name])
            if absent:
                raise ValueError(f"{condition}/{name}: {len(absent)} missing target rows; "
                                 "export explicit blank predictions for failures")
        for oid in target_ids:
            truths = [models[name][oid][0] for name in names]
            if any(t != truths[0] for t in truths[1:]):
                raise ValueError(f"{condition}/{oid}: inconsistent ground truth across models")
        common = {oid for oid in target_ids
                  if all(models[name][oid][1] is not None for name in names)}
        item = {"condition": condition, "n_targets": len(target_ids),
                "n_common_targets": len(common), "models": {}, "paired_differences": []}
        for name in names:
            own = [pred - actual for actual, pred in models[name].values() if pred is not None]
            paired = [models[name][oid][1] - models[name][oid][0] for oid in sorted(common)]
            item["models"][name] = {
                "coverage": len(own) / len(target_ids),
                "missing_prediction_count": len(target_ids) - len(own),
                "conditional_on_own_success": metrics(own),
                "on_all_model_common_support": metrics(paired)}
        for i, a in enumerate(names):
            for b in names[i+1:]:
                # Pairwise support is reported separately from all-model common support.
                ids = sorted(oid for oid in target_ids
                             if models[a][oid][1] is not None and models[b][oid][1] is not None)
                ea = [models[a][oid][1] - models[a][oid][0] for oid in ids]
                eb = [models[b][oid][1] - models[b][oid][0] for oid in ids]
                item["paired_differences"].append({
                    "model_a": a, "model_b": b, "direction": "a_minus_b", "n": len(ids),
                    "mean_absolute_error_difference":
                        math.fsum(abs(x)-abs(y) for x,y in zip(ea,eb))/len(ids) if ids else None,
                    "mean_squared_error_difference":
                        math.fsum(x*x-y*y for x,y in zip(ea,eb))/len(ids) if ids else None})
        results.append(item)
    return {"schema_version": 1, "analysis_type": "post_hoc_retained_prediction_audit",
            "model_execution": False, "input_rows": count, "conditions": results,
            "limitations": ["Common-support metrics condition on joint prediction success.",
                            "No causal, financial, statistical-significance or generalization claim is made.",
                            "This audit does not establish data rights or a pre-outcome protocol freeze.",
                            "No uncertainty intervals are computed; dependent targets are not IID samples."]}


def run(input_path: Path, output_directory: Path) -> Path:
    data = input_path.read_bytes()
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        result = audit(csv.DictReader(handle))
    result["input_sha256"] = hashlib.sha256(data).hexdigest()
    result["input_name"] = input_path.name
    output_directory.mkdir(parents=True, exist_ok=False)  # Never overwrite retained output.
    destination = output_directory / "shared_support_audit.json"
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="New, non-existing output directory")
    args = parser.parse_args()
    try:
        destination = run(args.input, args.out)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Audit refused: {exc}\n")
    print(destination)


if __name__ == "__main__":
    main()
