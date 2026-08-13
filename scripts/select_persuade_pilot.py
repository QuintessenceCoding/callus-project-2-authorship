#!/usr/bin/env python3
"""Select a small human-source PERSUADE pilot with streaming CSV processing.

Outputs:
- data/pilot/persuade_human_source_pilot/MANIFEST.md
- data/pilot/persuade_human_source_pilot/selected/*.txt
"""

from __future__ import annotations

import csv
import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = ROOT / "data" / "raw" / "persuade" / "persuade2_train_srctexts.csv"
OUT_DIR = ROOT / "data" / "pilot" / "persuade_human_source_pilot"
SELECTED_DIR = OUT_DIR / "selected"
MANIFEST_PATH = OUT_DIR / "MANIFEST.md"

TARGET_SELECTION_COUNT = 8
WORD_MIN = 500
WORD_MAX = 1500
PREFERRED_GRADES = {"9", "10"}


@dataclass
class DiscourseRow:
    discourse_id: str
    discourse_type: str
    start: int
    end: int
    text: str


@dataclass
class EssayRecord:
    essay_id: str
    prompt_name: str = ""
    grade_level: str = ""
    task: str = ""
    ell_status: str = ""
    discourse_rows: List[DiscourseRow] = field(default_factory=list)
    source_row_count: int = 0


@dataclass
class Candidate:
    essay: EssayRecord
    text: str
    word_count: int


@dataclass
class ValidationResult:
    reconstructed_success: bool
    duplicate_ids: bool
    non_empty_files: bool
    prompt_diversity: bool
    raw_csv_unchanged: bool


def safe_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def normalize_spaces(text: str) -> str:
    return " ".join((text or "").split())


def word_count(text: str) -> int:
    return len([t for t in text.split() if t.strip()])


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            hasher.update(block)
    return hasher.hexdigest()


def discourse_span_len(row: DiscourseRow) -> int:
    """PERSUADE discourse_end is an inclusive character offset."""
    offset_len = row.end - row.start + 1
    if offset_len > 0:
        return offset_len
    return len(row.text or "")


def reconstruct_essay_text(rows: List[DiscourseRow]) -> Tuple[str, bool]:
    """Reconstruct essay from discourse rows ordered by discourse_start.

    Returns:
    - reconstructed text
    - whether every discourse row could be mapped consistently into reconstructed spans
    """
    if not rows:
        return "", False

    ordered = sorted(rows, key=lambda r: (r.start, r.end, r.discourse_id))
    max_end = max(max(r.end + 1, r.start + len(r.text)) for r in ordered)
    if max_end <= 0:
        return "", False

    chars = [" "] * max_end

    for row in ordered:
        start = max(0, row.start)
        span_len = discourse_span_len(row)
        if span_len <= 0:
            continue

        txt = row.text or ""
        if len(txt) < span_len:
            txt = txt + (" " * (span_len - len(txt)))
        else:
            txt = txt[:span_len]

        for i, ch in enumerate(txt):
            pos = start + i
            if 0 <= pos < len(chars):
                chars[pos] = ch

    reconstructed = "".join(chars)

    # Verify each row aligns with the reconstructed span (best-effort consistency check).
    all_match = True
    full = "".join(chars)
    for row in ordered:
        start = max(0, row.start)
        span_len = discourse_span_len(row)
        if span_len <= 0:
            continue
        expected = (row.text or "")[:span_len]
        actual = full[start : start + span_len]
        if actual != expected:
            all_match = False
            break

    return reconstructed, all_match


def stream_persuade() -> Tuple[Dict[str, EssayRecord], List[str], int]:
    """Read CSV in streaming mode and group rows by essay_id_comp."""
    essays: Dict[str, EssayRecord] = {}
    columns: List[str] = []
    row_count = 0

    with SOURCE_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        for row in reader:
            row_count += 1
            essay_id = (row.get("essay_id_comp") or "").strip()
            if not essay_id:
                continue

            rec = essays.get(essay_id)
            if rec is None:
                rec = EssayRecord(
                    essay_id=essay_id,
                    prompt_name=(row.get("prompt_name") or "").strip(),
                    grade_level=(row.get("grade_level") or "").strip(),
                    task=(row.get("task") or "").strip(),
                    ell_status=(row.get("ell_status") or "").strip(),
                )
                essays[essay_id] = rec

            rec.source_row_count += 1

            rec.discourse_rows.append(
                DiscourseRow(
                    discourse_id=str(row.get("discourse_id") or "").strip(),
                    discourse_type=(row.get("discourse_type") or "").strip(),
                    start=safe_int(row.get("discourse_start")),
                    end=safe_int(row.get("discourse_end")),
                    text=row.get("discourse_text") or "",
                )
            )

    return essays, columns, row_count


def score_candidate(candidate: Candidate) -> float:
    wc = candidate.word_count
    grade_bonus = 20.0 if candidate.essay.grade_level in PREFERRED_GRADES else 0.0

    if WORD_MIN <= wc <= WORD_MAX:
        length_score = 30.0
    else:
        # Smoothly penalize distance from preferred range.
        center = (WORD_MIN + WORD_MAX) / 2.0
        distance = abs(wc - center)
        length_score = max(0.0, 30.0 - (distance / 100.0))

    # Slight preference for text-dependent tasks because most rows are in that setting,
    # but do not exclude independent tasks.
    task_bonus = 2.0 if candidate.essay.task == "Text dependent" else 0.0

    # Reward discourse coverage depth moderately.
    discourse_bonus = min(8.0, math.log2(max(1, candidate.essay.source_row_count)))

    return grade_bonus + length_score + task_bonus + discourse_bonus


def select_diverse(candidates: List[Candidate], target_n: int) -> List[Candidate]:
    by_prompt: Dict[str, List[Candidate]] = defaultdict(list)
    for c in candidates:
        by_prompt[c.essay.prompt_name].append(c)

    for prompt, items in by_prompt.items():
        items.sort(key=score_candidate, reverse=True)

    selected: List[Candidate] = []
    used_ids = set()

    # Round-robin across prompts to maximize diversity.
    prompt_keys = sorted(by_prompt.keys())
    idx = 0
    while len(selected) < target_n and prompt_keys:
        prompt = prompt_keys[idx % len(prompt_keys)]
        pool = by_prompt[prompt]

        pick = None
        while pool:
            c = pool.pop(0)
            if c.essay.essay_id not in used_ids:
                pick = c
                break

        if pick:
            selected.append(pick)
            used_ids.add(pick.essay.essay_id)

        # Remove exhausted prompt buckets.
        prompt_keys = [p for p in prompt_keys if by_prompt[p]]
        idx += 1

    if len(selected) < target_n:
        # Backfill globally by score if diversity pass leaves gaps.
        remaining = [c for c in candidates if c.essay.essay_id not in used_ids]
        remaining.sort(key=score_candidate, reverse=True)
        for c in remaining:
            selected.append(c)
            used_ids.add(c.essay.essay_id)
            if len(selected) >= target_n:
                break

    return selected[:target_n]


def build_candidates(essays: Dict[str, EssayRecord]) -> Tuple[List[Candidate], int]:
    candidates: List[Candidate] = []
    eligible_after_filter = 0

    for rec in essays.values():
        text, ok = reconstruct_essay_text(rec.discourse_rows)
        if not ok or not text:
            continue

        wc = word_count(text)

        # Eligibility pass used for reporting and selection pool.
        # Keep broad enough to preserve prompt diversity and backfill options.
        grade_ok = rec.grade_level in PREFERRED_GRADES
        length_ok = 300 <= wc <= 1800
        if grade_ok and length_ok:
            eligible_after_filter += 1

        # Add all successfully reconstructed records into pool, scored later.
        candidates.append(Candidate(essay=rec, text=text, word_count=wc))

    # Sort by score once so all downstream logic is stable.
    candidates.sort(key=score_candidate, reverse=True)
    return candidates, eligible_after_filter


def write_outputs(selected: List[Candidate], source_columns: List[str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SELECTED_DIR.mkdir(parents=True, exist_ok=True)

    for c in selected:
        out_path = SELECTED_DIR / f"{c.essay.essay_id}.txt"
        out_path.write_text(c.text, encoding="utf-8")

    source_version = "PERSUADE 2.0 train source rows (local raw file)"
    archive_file = str(SOURCE_CSV)

    lines: List[str] = []
    lines.append("# PERSUADE Human-Source Pilot Manifest")
    lines.append("")
    lines.append("## Dataset Provenance")
    lines.append(f"- source dataset/version: {source_version}")
    lines.append(f"- source archive/file: {archive_file}")
    lines.append(f"- source columns observed: {source_columns}")
    lines.append("")
    lines.append("## Selection Policy")
    lines.append("- Target count: approximately 8 essays")
    lines.append("- Preference: grade_level 9/10")
    lines.append("- Preference: substantial essays roughly 500-1500 words where possible")
    lines.append("- Preference: prompt diversity")
    lines.append("- No duplicate essay IDs")
    lines.append("- Demographic fields (race, gender, economic status, disability status, etc.) are not used as model features")
    lines.append("- ell_status retained only as metadata for later bias analysis")
    lines.append("- No AI variants generated")
    lines.append("")
    lines.append("## Reconstruction Finding")
    lines.append("- The source rows include meaningful embedded whitespace in `discourse_text`, including paragraph line breaks for selected essays.")
    lines.append("- `discourse_start` and `discourse_end` are used as inclusive character offsets; selected source rows are contiguous under that interpretation.")
    lines.append("- Reconstruction preserves the `discourse_text` characters at their source offsets and uses spaces only for any offset gaps whose original characters are not available in this CSV.")
    lines.append("")
    lines.append("## Selected Essays")

    for i, c in enumerate(selected, start=1):
        ordered_rows = sorted(c.essay.discourse_rows, key=lambda r: (r.start, r.end, r.discourse_id))
        discourse_types = sorted({r.discourse_type for r in ordered_rows if r.discourse_type})
        discourse_id_preview = ", ".join(r.discourse_id for r in ordered_rows[:12])

        rationale_parts = []
        if c.essay.grade_level in PREFERRED_GRADES:
            rationale_parts.append("preferred grade 9/10")
        if WORD_MIN <= c.word_count <= WORD_MAX:
            rationale_parts.append("within preferred word range")
        else:
            rationale_parts.append("selected to maintain prompt diversity despite word-range deviation")
        rationale_parts.append("unique essay_id_comp")

        lines.append(f"### {i}. {c.essay.essay_id}")
        lines.append(f"- essay_id_comp: {c.essay.essay_id}")
        lines.append(f"- prompt_name: {c.essay.prompt_name}")
        lines.append(f"- grade_level: {c.essay.grade_level}")
        lines.append(f"- task: {c.essay.task}")
        lines.append(f"- ell_status: {c.essay.ell_status if c.essay.ell_status else '(missing)'}")
        lines.append(f"- word count: {c.word_count}")
        lines.append(f"- source row count for essay: {c.essay.source_row_count}")
        lines.append(f"- discourse row ordering key: discourse_start ascending")
        lines.append(f"- discourse type set: {discourse_types}")
        lines.append(f"- discourse_id preview (first 12 in order): {discourse_id_preview}")
        lines.append(f"- selected file: selected/{c.essay.essay_id}.txt")
        lines.append(f"- selection rationale: {', '.join(rationale_parts)}")
        lines.append("")

    MANIFEST_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def validate(
    selected: List[Candidate],
    csv_stat_before: Tuple[int, float, str],
    csv_stat_after: Tuple[int, float, str],
) -> ValidationResult:
    ids = [c.essay.essay_id for c in selected]
    duplicate_ids = len(ids) != len(set(ids))

    reconstructed_success = True
    for c in selected:
        text, ok = reconstruct_essay_text(c.essay.discourse_rows)
        if not ok or not text:
            reconstructed_success = False
            break

    non_empty_files = True
    for c in selected:
        p = SELECTED_DIR / f"{c.essay.essay_id}.txt"
        if not p.exists() or p.stat().st_size == 0:
            non_empty_files = False
            break

    prompt_count = len({c.essay.prompt_name for c in selected})
    prompt_diversity = prompt_count >= min(4, len(selected))

    raw_csv_unchanged = csv_stat_before == csv_stat_after

    return ValidationResult(
        reconstructed_success=reconstructed_success,
        duplicate_ids=duplicate_ids,
        non_empty_files=non_empty_files,
        prompt_diversity=prompt_diversity,
        raw_csv_unchanged=raw_csv_unchanged,
    )


def csv_stat_tuple(path: Path) -> Tuple[int, float, str]:
    st = path.stat()
    # Include hash to strongly validate unchanged raw file.
    return (st.st_size, st.st_mtime, sha256_file(path))


def main() -> None:
    if not SOURCE_CSV.exists():
        raise FileNotFoundError(f"Missing input CSV: {SOURCE_CSV}")

    csv_before = csv_stat_tuple(SOURCE_CSV)

    essays, columns, source_row_count = stream_persuade()
    unique_essays_processed = len(essays)

    candidates, eligible_after_filter = build_candidates(essays)
    selected = select_diverse(candidates, TARGET_SELECTION_COUNT)

    write_outputs(selected, columns)

    csv_after = csv_stat_tuple(SOURCE_CSV)
    validation = validate(selected, csv_before, csv_after)

    print("PERSUADE pilot selection complete.")
    print(f"unique_essays_processed={unique_essays_processed}")
    print(f"eligible_after_filter={eligible_after_filter}")
    print(f"selected_count={len(selected)}")
    print("selected_rows:")
    for c in selected:
        print(
            f"- {c.essay.essay_id} | prompt={c.essay.prompt_name} | "
            f"grade={c.essay.grade_level} | words={c.word_count}"
        )

    print("validation:")
    print(f"- reconstructed_success={validation.reconstructed_success}")
    print(f"- no_duplicate_ids={not validation.duplicate_ids}")
    print(f"- selected_files_non_empty={validation.non_empty_files}")
    print(f"- prompt_diversity_ok={validation.prompt_diversity}")
    print(f"- raw_csv_unchanged={validation.raw_csv_unchanged}")


if __name__ == "__main__":
    main()
