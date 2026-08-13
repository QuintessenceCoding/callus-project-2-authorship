#!/usr/bin/env python3
"""Inspect local raw AIDE and PERSUADE datasets without modifying them.

Outputs a markdown summary at scripts/raw_dataset_inspection.md.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
AIDE_CSV = ROOT / "data" / "raw" / "aide" / "AIDE_train_essays.csv"
PROMPTS_CSV = ROOT / "data" / "raw" / "aide" / "train_prompts.csv"
AIDE_DOCX = ROOT / "data" / "raw" / "aide" / "Instructions to recreate AI Generated Text Dataset.docx"
PERSUADE_CSV = ROOT / "data" / "raw" / "persuade" / "persuade2_train_srctexts.csv"
PERSUADE_PDF = ROOT / "data" / "raw" / "persuade" / "PERSUADE corpus_ annotation scheme - binary.pdf"
OUT_MD = ROOT / "scripts" / "raw_dataset_inspection.md"

SAFE_PREVIEW_LEN = 240
SAMPLE_ROW_LIMIT = 30


def safe_preview(text: str, max_len: int = SAFE_PREVIEW_LEN) -> str:
    text = (text or "").replace("\n", " ").replace("\r", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def infer_dtype(values: List[str]) -> str:
    def is_int(v: str) -> bool:
        if v == "":
            return False
        if v.startswith(("+", "-")):
            return v[1:].isdigit()
        return v.isdigit()

    def is_float(v: str) -> bool:
        if v == "":
            return False
        try:
            float(v)
            return True
        except ValueError:
            return False

    non_empty = [v for v in values if v != ""]
    if not non_empty:
        return "empty"
    if all(is_int(v) for v in non_empty):
        return "int"
    if all(is_float(v) for v in non_empty):
        return "float"
    return "string"


def pct(values: List[int], p: float) -> float:
    if not values:
        return float("nan")
    values_sorted = sorted(values)
    if len(values_sorted) == 1:
        return float(values_sorted[0])
    idx = (len(values_sorted) - 1) * p
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return float(values_sorted[lo])
    return values_sorted[lo] + (values_sorted[hi] - values_sorted[lo]) * (idx - lo)


def inspect_aide() -> Dict[str, object]:
    row_count = 0
    columns: List[str] = []
    samples_for_type: Dict[str, List[str]] = defaultdict(list)
    generated_counts: Counter = Counter()
    prompt_ids = set()
    text_lengths: List[int] = []
    first_two: List[Dict[str, str]] = []

    with AIDE_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        for row in reader:
            row_count += 1
            if len(first_two) < 2:
                first_two.append(dict(row))

            for col in columns:
                if len(samples_for_type[col]) < 200:
                    samples_for_type[col].append(row.get(col, ""))

            g = row.get("generated", "")
            generated_counts[g] += 1

            pid = row.get("prompt_id", "")
            if pid != "":
                prompt_ids.add(pid)

            text_lengths.append(len(row.get("text", "") or ""))

    dtypes = {col: infer_dtype(samples_for_type[col]) for col in columns}

    prompt_map = {}
    with PROMPTS_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompt_map[row.get("prompt_id", "")] = row

    joinable = all(pid in prompt_map for pid in prompt_ids)

    return {
        "row_count": row_count,
        "columns": columns,
        "dtypes": dtypes,
        "generated_counts": dict(generated_counts),
        "unique_prompt_ids": sorted(prompt_ids, key=lambda x: int(x) if x.isdigit() else x),
        "text_length_min": min(text_lengths) if text_lengths else None,
        "text_length_median": statistics.median(text_lengths) if text_lengths else None,
        "text_length_max": max(text_lengths) if text_lengths else None,
        "first_two": first_two,
        "prompt_joinable": joinable,
    }


def inspect_persuade() -> Dict[str, object]:
    total_rows = 0
    columns: List[str] = []

    unique_essay_ids = set()
    prompt_name_counts: Counter = Counter()
    grade_counts: Counter = Counter()
    ell_counts: Counter = Counter()
    task_counts: Counter = Counter()
    discourse_type_counts: Counter = Counter()

    # Per-essay aggregation for approximate full-length distribution and multi-row check.
    essay_stats: Dict[str, Dict[str, int]] = {}

    sample_essay_id = None

    with PERSUADE_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        for row in reader:
            total_rows += 1

            essay_id = row.get("essay_id_comp", "")
            if sample_essay_id is None and essay_id:
                sample_essay_id = essay_id

            unique_essay_ids.add(essay_id)
            prompt_name_counts[row.get("prompt_name", "")] += 1
            grade_counts[row.get("grade_level", "")] += 1
            ell_counts[row.get("ell_status", "")] += 1
            task_counts[row.get("task", "")] += 1
            discourse_type_counts[row.get("discourse_type", "")] += 1

            try:
                start = int(float(row.get("discourse_start", "0") or 0))
            except ValueError:
                start = 0
            try:
                end = int(float(row.get("discourse_end", "0") or 0))
            except ValueError:
                end = start

            if essay_id not in essay_stats:
                essay_stats[essay_id] = {
                    "min_start": start,
                    "max_end": end,
                    "rows": 1,
                }
            else:
                st = essay_stats[essay_id]
                st["min_start"] = min(st["min_start"], start)
                st["max_end"] = max(st["max_end"], end)
                st["rows"] += 1

    essay_lengths = []
    essays_with_multiple_rows = 0
    for st in essay_stats.values():
        approx_len = max(0, st["max_end"] - st["min_start"])
        essay_lengths.append(approx_len)
        if st["rows"] > 1:
            essays_with_multiple_rows += 1

    # Second pass: collect one sample essay's discourse rows to show mapping.
    sample_rows = []
    if sample_essay_id:
        with PERSUADE_CSV.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("essay_id_comp", "") == sample_essay_id:
                    try:
                        start = int(float(row.get("discourse_start", "0") or 0))
                    except ValueError:
                        start = 0
                    try:
                        end = int(float(row.get("discourse_end", "0") or 0))
                    except ValueError:
                        end = start
                    sample_rows.append(
                        {
                            "discourse_id": row.get("discourse_id", ""),
                            "start": start,
                            "end": end,
                            "type": row.get("discourse_type", ""),
                            "text": row.get("discourse_text", "") or "",
                        }
                    )

    sample_rows.sort(key=lambda r: (r["start"], r["end"]))

    reconstructed_preview = ""
    mapping_match = None
    if sample_rows:
        total_len = max(r["end"] for r in sample_rows) if sample_rows else 0
        chars = [" "] * max(0, total_len)
        for r in sample_rows:
            start = max(0, r["start"])
            end = max(start, r["end"])
            txt = r["text"]
            span = end - start
            if span <= 0:
                continue
            if len(txt) < span:
                txt_fill = txt + (" " * (span - len(txt)))
            else:
                txt_fill = txt[:span]
            for i, ch in enumerate(txt_fill):
                pos = start + i
                if 0 <= pos < len(chars):
                    chars[pos] = ch

        reconstructed = "".join(chars)
        reconstructed_preview = safe_preview(reconstructed, 500)

        matched = 0
        for r in sample_rows:
            start = max(0, r["start"])
            end = max(start, r["end"])
            if end <= len(reconstructed):
                if reconstructed[start:end] == (r["text"][: (end - start)]):
                    matched += 1
        mapping_match = {
            "matched_rows": matched,
            "total_rows": len(sample_rows),
        }

    return {
        "total_rows": total_rows,
        "columns": columns,
        "unique_essay_id_count": len(unique_essay_ids),
        "unique_prompt_name_count": len(prompt_name_counts),
        "grade_counts": dict(grade_counts),
        "ell_counts": dict(ell_counts),
        "task_counts": dict(task_counts),
        "discourse_type_count": len(discourse_type_counts),
        "discourse_type_counts": dict(discourse_type_counts),
        "essays_with_multiple_rows": essays_with_multiple_rows,
        "all_essays_count": len(essay_stats),
        "essay_len_min": min(essay_lengths) if essay_lengths else None,
        "essay_len_median": statistics.median(essay_lengths) if essay_lengths else None,
        "essay_len_p90": pct(essay_lengths, 0.90) if essay_lengths else None,
        "essay_len_p95": pct(essay_lengths, 0.95) if essay_lengths else None,
        "essay_len_max": max(essay_lengths) if essay_lengths else None,
        "sample_essay_id": sample_essay_id,
        "sample_rows": sample_rows[:SAMPLE_ROW_LIMIT],
        "sample_total_rows": len(sample_rows),
        "sample_reconstructed_preview": reconstructed_preview,
        "sample_mapping_match": mapping_match,
    }


def md_counter(counter_dict: Dict[str, int]) -> str:
    items = sorted(counter_dict.items(), key=lambda kv: (-kv[1], kv[0]))
    if not items:
        return "(none)"
    return "\n".join([f"- {k!r}: {v}" for k, v in items])


def format_num(x) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float):
        if math.isnan(x):
            return "n/a"
        if x.is_integer():
            return f"{int(x):,}"
        return f"{x:,.2f}"
    if isinstance(x, int):
        return f"{x:,}"
    return str(x)


def write_report(aide: Dict[str, object], persuade: Dict[str, object]) -> None:
    lines: List[str] = []
    lines.append("# Raw Dataset Inspection (Local Files Only)")
    lines.append("")
    lines.append("## Scope and Guardrails")
    lines.append("- Inspected only local raw files.")
    lines.append("- No raw dataset files were modified.")
    lines.append("- No processed datasets were created.")
    lines.append("- No training or text generation was performed.")
    lines.append("- PERSUADE CSV was processed in streaming mode (row-by-row), not loaded wholesale.")
    lines.append("")
    lines.append("## Files")
    lines.append(f"- AIDE essays: `{AIDE_CSV}`")
    lines.append(f"- AIDE prompts: `{PROMPTS_CSV}`")
    lines.append(f"- AIDE instructions docx: `{AIDE_DOCX}` (exists: {AIDE_DOCX.exists()})")
    lines.append(f"- PERSUADE source rows: `{PERSUADE_CSV}`")
    lines.append(f"- PERSUADE annotation scheme pdf: `{PERSUADE_PDF}` (exists: {PERSUADE_PDF.exists()})")
    lines.append("")

    lines.append("## AIDE Inspection")
    lines.append(f"- Row count: {format_num(aide['row_count'])}")
    lines.append(f"- Columns: {aide['columns']}")
    lines.append("- Inferred data types:")
    for col, dt in aide["dtypes"].items():
        lines.append(f"  - {col}: {dt}")
    lines.append("- `generated` unique values / counts:")
    for k, v in sorted(aide["generated_counts"].items(), key=lambda kv: kv[0]):
        lines.append(f"  - {k!r}: {v}")
    lines.append(f"- Unique prompt IDs ({len(aide['unique_prompt_ids'])}): {aide['unique_prompt_ids']}")
    lines.append(
        "- Text length (characters): "
        f"min={format_num(aide['text_length_min'])}, "
        f"median={format_num(aide['text_length_median'])}, "
        f"max={format_num(aide['text_length_max'])}"
    )

    lines.append("- First 2 records (safe preview):")
    for i, row in enumerate(aide["first_two"], start=1):
        lines.append(f"  - Record {i}:")
        lines.append(f"    - id: {row.get('id', '')}")
        lines.append(f"    - prompt_id: {row.get('prompt_id', '')}")
        lines.append(f"    - generated: {row.get('generated', '')}")
        lines.append(f"    - text_preview: {safe_preview(row.get('text', ''))}")

    lines.append(f"- Prompt joinability with train_prompts.csv: {aide['prompt_joinable']}")
    lines.append("")

    lines.append("## PERSUADE Inspection")
    lines.append(f"- Total row count: {format_num(persuade['total_rows'])}")
    lines.append(f"- Column names ({len(persuade['columns'])}): {persuade['columns']}")
    lines.append(f"- Unique `essay_id_comp` count: {format_num(persuade['unique_essay_id_count'])}")
    lines.append(f"- Unique `prompt_name` count: {format_num(persuade['unique_prompt_name_count'])}")

    lines.append("- `grade_level` values/counts:")
    lines.append(md_counter(persuade["grade_counts"]))

    lines.append("- `ell_status` values/counts:")
    lines.append(md_counter(persuade["ell_counts"]))

    lines.append("- `task` values/counts:")
    lines.append(md_counter(persuade["task_counts"]))

    lines.append("- Approximate essay length distribution (chars, reconstructed using min(discourse_start) and max(discourse_end) per essay):")
    lines.append(
        f"  - min={format_num(persuade['essay_len_min'])}, "
        f"median={format_num(persuade['essay_len_median'])}, "
        f"p90={format_num(persuade['essay_len_p90'])}, "
        f"p95={format_num(persuade['essay_len_p95'])}, "
        f"max={format_num(persuade['essay_len_max'])}"
    )

    lines.append(f"- Number of discourse types: {format_num(persuade['discourse_type_count'])}")
    lines.append("- Discourse type counts:")
    lines.append(md_counter(persuade["discourse_type_counts"]))

    lines.append(
        "- Multiple rows per essay present: "
        f"{persuade['essays_with_multiple_rows'] > 0} "
        f"({format_num(persuade['essays_with_multiple_rows'])} / {format_num(persuade['all_essays_count'])} essays have >1 row)"
    )

    lines.append("- Sample essay discourse-to-text mapping:")
    lines.append(f"  - sample essay_id_comp: {persuade['sample_essay_id']}")
    lines.append(f"  - discourse rows found for sample: {format_num(persuade['sample_total_rows'])}")
    if persuade.get("sample_mapping_match"):
        mm = persuade["sample_mapping_match"]
        lines.append(
            "  - row text aligns with reconstructed span: "
            f"{format_num(mm['matched_rows'])}/{format_num(mm['total_rows'])} rows"
        )
    lines.append("  - reconstructed essay preview (safe):")
    lines.append(f"    - {persuade['sample_reconstructed_preview']}")
    lines.append("  - first discourse rows (ordered by span):")
    for row in persuade["sample_rows"]:
        lines.append(
            "    - "
            f"[{row['start']}, {row['end']}) "
            f"type={row['type']!r} discourse_id={row['discourse_id']} "
            f"text={safe_preview(row['text'], 120)}"
        )

    lines.append("")
    lines.append("## Stop Condition")
    lines.append("Inspection completed. No additional processing was performed.")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    required = [AIDE_CSV, PROMPTS_CSV, PERSUADE_CSV]
    missing = [p for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required files: {missing}")

    aide = inspect_aide()
    persuade = inspect_persuade()
    write_report(aide, persuade)
    print(f"Wrote inspection report: {OUT_MD}")


if __name__ == "__main__":
    main()
