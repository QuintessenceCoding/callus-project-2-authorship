"""EXP-005: feature distribution sanity check.

This experiment compares distributions of EXP-004 candidate features between
paired human and AI texts from DAIGT external data.

Scope constraints:
- No classifier training
- No threshold selection
- No anomaly scoring
- No production-code changes
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import platform
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import spacy
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


EXPERIMENT_ID = "EXP-005"
EXPERIMENT_NAME = "Feature Distribution Sanity Check"
TARGET_SAMPLE_SIZE = 200
SAMPLE_SEED = 20260813

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = EXPERIMENT_DIR / "results" / "results.json"

EXP004_PATH = ROOT / "experiments" / "EXP-004-feature-extraction" / "run.py"

# Expected local file; fallback to any CSV inside this folder if renamed.
DEFAULT_DATASET_PATH = (
    ROOT / "data" / "raw" / "daigt_external" / "daigt_external_dataset.csv"
)

FEATURE_NAMES = [
    "perplexity",
    "sentence_length_cv",
    "mattr",
    "pos_3gram_entropy",
]


def load_module(module_path: Path, module_name: str) -> Any:
    if not module_path.exists():
        raise FileNotFoundError(f"Module not found: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load spec for: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def resolve_dataset_path() -> Path:
    if DEFAULT_DATASET_PATH.exists():
        return DEFAULT_DATASET_PATH

    folder = ROOT / "data" / "raw" / "daigt_external"
    candidates = sorted(folder.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No DAIGT CSV found in {folder}. Expected {DEFAULT_DATASET_PATH.name}."
        )

    return candidates[0]


def environment_info() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "spacy": spacy.__version__,
        "device": "cpu",
    }


def file_integrity(path: Path) -> dict[str, Any]:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            hasher.update(block)

    st = path.stat()
    return {
        "path": str(path),
        "size_bytes": st.st_size,
        "sha256": hasher.hexdigest(),
    }


def is_finite_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and math.isfinite(v)


def quantile_linear(sorted_values: list[float], q: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])

    idx = (len(sorted_values) - 1) * q
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return float(sorted_values[lo])

    frac = idx - lo
    return float(sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac)


def summarize_values(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "stdev": None,
            "iqr": None,
            "q1": None,
            "q3": None,
            "min": None,
            "max": None,
        }

    s = sorted(values)
    q1 = quantile_linear(s, 0.25)
    q3 = quantile_linear(s, 0.75)
    iqr = None if q1 is None or q3 is None else q3 - q1

    stdev = statistics.stdev(values) if len(values) >= 2 else None

    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": stdev,
        "iqr": iqr,
        "q1": q1,
        "q3": q3,
        "min": min(values),
        "max": max(values),
    }


def range_overlap_ratio(
    h_min: float | None,
    h_max: float | None,
    a_min: float | None,
    a_max: float | None,
) -> float | None:
    if None in (h_min, h_max, a_min, a_max):
        return None

    left = max(h_min, a_min)
    right = min(h_max, a_max)
    intersection = max(0.0, right - left)

    union_left = min(h_min, a_min)
    union_right = max(h_max, a_max)
    union = max(0.0, union_right - union_left)

    if union == 0:
        return None
    return intersection / union


def iqr_overlap_ratio(
    h_q1: float | None,
    h_q3: float | None,
    a_q1: float | None,
    a_q3: float | None,
) -> float | None:
    if None in (h_q1, h_q3, a_q1, a_q3):
        return None

    left = max(h_q1, a_q1)
    right = min(h_q3, a_q3)
    intersection = max(0.0, right - left)

    union_left = min(h_q1, a_q1)
    union_right = max(h_q3, a_q3)
    union = max(0.0, union_right - union_left)

    if union == 0:
        return None
    return intersection / union


def cohens_d(human: list[float], ai: list[float]) -> float | None:
    if len(human) < 2 or len(ai) < 2:
        return None

    h_mean = statistics.mean(human)
    a_mean = statistics.mean(ai)
    h_var = statistics.variance(human)
    a_var = statistics.variance(ai)

    denom_df = len(human) + len(ai) - 2
    if denom_df <= 0:
        return None

    pooled_var = ((len(human) - 1) * h_var + (len(ai) - 1) * a_var) / denom_df
    if pooled_var <= 0:
        return None

    pooled_std = math.sqrt(pooled_var)
    if pooled_std == 0:
        return None

    return (statistics.mean(ai) - statistics.mean(human)) / pooled_std


def discover_usable_rows(dataset_path: Path) -> dict[str, Any]:
    usable: list[dict[str, Any]] = []
    total_rows = 0
    unusable_reasons = Counter()

    with dataset_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            total_rows += 1
            text = (row.get("text") or "").strip()
            source_text = (row.get("source_text") or "").strip()

            if not text:
                unusable_reasons["missing_human_text"] += 1
                continue
            if not source_text:
                unusable_reasons["missing_ai_source_text"] += 1
                continue

            usable.append(
                {
                    "row_index": i,
                    "id": row.get("id") or f"row-{i}",
                }
            )

    return {
        "total_rows": total_rows,
        "usable_rows": usable,
        "unusable_reasons": dict(unusable_reasons),
    }


def select_rows(usable_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(SAMPLE_SEED)
    usable_count = len(usable_rows)

    if usable_count >= TARGET_SAMPLE_SIZE:
        selected = rng.sample(usable_rows, TARGET_SAMPLE_SIZE)
        shortfall_reason = None
    else:
        selected = list(usable_rows)
        shortfall_reason = (
            f"usable_records_below_target: usable={usable_count}, target={TARGET_SAMPLE_SIZE}"
        )

    selected_sorted = sorted(selected, key=lambda x: x["row_index"])

    return {
        "selected_rows": selected_sorted,
        "selected_count": len(selected_sorted),
        "shortfall_reason": shortfall_reason,
    }


def extract_text_features(
    text: str,
    nlp: Any,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    exp004_module: Any,
    exp001_module: Any,
) -> dict[str, Any]:
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]

    # EXP-004 sentence perplexity reused; aggregate to document level via median
    # of valid sentence perplexities for distribution comparison.
    sentence_ppl_values: list[float] = []
    sentence_ppl_status_counts = Counter()
    sentence_ppl_unavailable_reasons = Counter()

    sentence_lengths_for_cv: list[int] = []

    for sentence_text in sentences:
        ppl_result = exp001_module.calculate_perplexity(
            sentence_text,
            tokenizer,
            model,
            device,
        )
        status = ppl_result.get("status")
        sentence_ppl_status_counts[status] += 1

        if status == "ok" and is_finite_number(ppl_result.get("perplexity")):
            sentence_ppl_values.append(float(ppl_result["perplexity"]))
        else:
            reason = ppl_result.get("reason") or status or "unknown"
            sentence_ppl_unavailable_reasons[str(reason)] += 1

        sent_doc = nlp.make_doc(sentence_text)
        sent_len = len([t for t in sent_doc if not t.is_space and not t.is_punct])
        sentence_lengths_for_cv.append(sent_len)

    if sentence_ppl_values:
        perplexity_value = float(statistics.median(sentence_ppl_values))
        perplexity_meta = {
            "available": True,
            "reason": None,
            "sentence_count": len(sentences),
            "valid_sentence_perplexity_count": len(sentence_ppl_values),
            "sentence_perplexity_aggregation": "median_of_valid_sentence_perplexities",
            "status_counts": dict(sentence_ppl_status_counts),
        }
    else:
        perplexity_value = None
        perplexity_meta = {
            "available": False,
            "reason": "no_valid_sentence_perplexity_values",
            "sentence_count": len(sentences),
            "valid_sentence_perplexity_count": 0,
            "status_counts": dict(sentence_ppl_status_counts),
            "unavailable_reason_counts": dict(sentence_ppl_unavailable_reasons),
        }

    cv_value, cv_meta = exp004_module.sentence_length_cv(sentence_lengths_for_cv)

    lexical_tokens = exp004_module.tokenize_for_lexical_features(doc)
    mattr_value, mattr_meta = exp004_module.mattr(
        lexical_tokens,
        exp004_module.MATTR_WINDOW,
    )

    pos_entropy_value, pos_entropy_meta = exp004_module.pos_trigram_entropy(doc)

    features = {
        "perplexity": {"value": perplexity_value, "meta": perplexity_meta},
        "sentence_length_cv": {
            "value": float(cv_value) if is_finite_number(cv_value) else None,
            "meta": cv_meta,
        },
        "mattr": {
            "value": float(mattr_value) if is_finite_number(mattr_value) else None,
            "meta": mattr_meta,
        },
        "pos_3gram_entropy": {
            "value": float(pos_entropy_value) if is_finite_number(pos_entropy_value) else None,
            "meta": pos_entropy_meta,
        },
    }

    return {
        "sentence_count": len(sentences),
        "features": features,
    }


def summarize_distributions(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    by_feature_class_values: dict[str, dict[str, list[float]]] = {
        feat: {"human": [], "ai": []} for feat in FEATURE_NAMES
    }
    missing_reason_counts: dict[str, dict[str, Counter[str]]] = {
        feat: {"human": Counter(), "ai": Counter()} for feat in FEATURE_NAMES
    }

    for pair in pairs:
        for label in ("human", "ai"):
            item = pair[label]
            for feat in FEATURE_NAMES:
                value = item["features"][feat]["value"]
                meta = item["features"][feat]["meta"]
                if is_finite_number(value):
                    by_feature_class_values[feat][label].append(float(value))
                else:
                    reason = meta.get("reason") or "unavailable"
                    missing_reason_counts[feat][label][str(reason)] += 1

    feature_summaries: dict[str, Any] = {}

    for feat in FEATURE_NAMES:
        h_vals = by_feature_class_values[feat]["human"]
        a_vals = by_feature_class_values[feat]["ai"]

        h_stats = summarize_values(h_vals)
        a_stats = summarize_values(a_vals)

        h_median = h_stats["median"]
        a_median = a_stats["median"]
        median_diff = None
        if h_median is not None and a_median is not None:
            median_diff = a_median - h_median

        effect = cohens_d(h_vals, a_vals)

        overlap = {
            "range_overlap_ratio": range_overlap_ratio(
                h_stats["min"], h_stats["max"], a_stats["min"], a_stats["max"]
            ),
            "iqr_overlap_ratio": iqr_overlap_ratio(
                h_stats["q1"], h_stats["q3"], a_stats["q1"], a_stats["q3"]
            ),
        }

        paired_diffs = []
        missing_pairs = 0
        for pair in pairs:
            hv = pair["human"]["features"][feat]["value"]
            av = pair["ai"]["features"][feat]["value"]
            if is_finite_number(hv) and is_finite_number(av):
                paired_diffs.append(float(av) - float(hv))
            else:
                missing_pairs += 1

        paired_stats = summarize_values(paired_diffs)
        paired_stats.update(
            {
                "valid_pair_count": len(paired_diffs),
                "missing_pair_count": missing_pairs,
                "difference_direction_counts": {
                    "ai_gt_human": sum(1 for x in paired_diffs if x > 0),
                    "ai_lt_human": sum(1 for x in paired_diffs if x < 0),
                    "ai_eq_human": sum(1 for x in paired_diffs if x == 0),
                },
            }
        )

        feature_summaries[feat] = {
            "human": {
                "valid_count": h_stats["count"],
                "missing_or_abstained_count": len(pairs) - h_stats["count"],
                "stats": h_stats,
                "missing_reason_counts": dict(missing_reason_counts[feat]["human"]),
            },
            "ai": {
                "valid_count": a_stats["count"],
                "missing_or_abstained_count": len(pairs) - a_stats["count"],
                "stats": a_stats,
                "missing_reason_counts": dict(missing_reason_counts[feat]["ai"]),
            },
            "human_vs_ai": {
                "human_median": h_median,
                "ai_median": a_median,
                "median_difference_ai_minus_human": median_diff,
                "overlap_summary": overlap,
                "effect_size": {
                    "name": "cohens_d_ai_minus_human",
                    "value": effect,
                },
                "paired_difference_summary": paired_stats,
            },
        }

    return feature_summaries


def validate_results(output: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}

    sample = output["sampling"]
    selected_count = sample["selected_count"]

    checks["sample_size_expected_or_explained"] = {
        "passed": selected_count == TARGET_SAMPLE_SIZE
        or (
            selected_count < TARGET_SAMPLE_SIZE
            and sample.get("shortfall_reason") is not None
        ),
        "selected_count": selected_count,
        "target": TARGET_SAMPLE_SIZE,
        "shortfall_reason": sample.get("shortfall_reason"),
    }

    selected_ids = sample["selected_row_ids"]
    selected_indices = sample["selected_row_indices"]

    checks["no_duplicate_selected_indices"] = {
        "passed": len(selected_indices) == len(set(selected_indices)),
        "count": len(selected_indices),
        "unique_count": len(set(selected_indices)),
    }

    checks["no_duplicate_selected_ids"] = {
        "passed": len(selected_ids) == len(set(selected_ids)),
        "count": len(selected_ids),
        "unique_count": len(set(selected_ids)),
    }

    pair_results = output["pair_results"]
    checks["pairs_preserved"] = {
        "passed": len(pair_results) == selected_count,
        "pair_count": len(pair_results),
        "selected_count": selected_count,
    }

    pair_indices = [p["row_index"] for p in pair_results]
    pair_ids = [p["id"] for p in pair_results]
    checks["pair_results_match_selected_rows"] = {
        "passed": pair_indices == selected_indices and pair_ids == selected_ids,
        "pair_row_indices_match": pair_indices == selected_indices,
        "pair_ids_match": pair_ids == selected_ids,
    }

    checks["raw_dataset_unchanged"] = {
        "passed": output["dataset"]["integrity_before"]
        == output["dataset"]["integrity_after"],
        "integrity_before": output["dataset"]["integrity_before"],
        "integrity_after": output["dataset"]["integrity_after"],
    }

    finite_ok = True
    mattr_range_ok = True
    for pair in pair_results:
        for label in ("human", "ai"):
            feats = pair[label]["features"]
            for feat in FEATURE_NAMES:
                v = feats[feat]["value"]
                if v is not None and not is_finite_number(v):
                    finite_ok = False
            mv = feats["mattr"]["value"]
            if mv is not None and not (0.0 <= mv <= 1.0):
                mattr_range_ok = False

    checks["finite_feature_values_when_present"] = {
        "passed": finite_ok,
    }

    checks["mattr_in_valid_range_when_present"] = {
        "passed": mattr_range_ok,
    }

    summary_counts_ok = True
    for feat in FEATURE_NAMES:
        for label in ("human", "ai"):
            values = [
                pair[label]["features"][feat]["value"]
                for pair in pair_results
            ]
            valid_count = sum(1 for v in values if is_finite_number(v))
            missing_count = len(values) - valid_count
            summary = output["distribution_summary"][feat][label]
            if (
                summary["valid_count"] != valid_count
                or summary["missing_or_abstained_count"] != missing_count
                or summary["stats"]["count"] != valid_count
            ):
                summary_counts_ok = False

    checks["distribution_summary_counts_consistent"] = {
        "passed": summary_counts_ok,
    }

    return {
        "checks": checks,
        "all_passed": all(v["passed"] for v in checks.values()),
    }


def main() -> None:
    started = time.perf_counter()
    torch.manual_seed(0)
    torch.set_num_threads(max(torch.get_num_threads(), 1))
    device = torch.device("cpu")

    dataset_path = resolve_dataset_path()
    dataset_integrity_before = file_integrity(dataset_path)

    exp004_module = load_module(EXP004_PATH, "exp004_run")
    exp001_module = exp004_module.load_exp001_module()

    nlp = spacy.load(exp004_module.SPACY_MODEL)
    tokenizer = AutoTokenizer.from_pretrained(exp004_module.MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(exp004_module.MODEL_ID)
    model.to(device)
    model.eval()

    usable_info = discover_usable_rows(dataset_path)
    selection = select_rows(usable_info["usable_rows"])

    selected_by_index = {
        item["row_index"]: item for item in selection["selected_rows"]
    }

    pair_results: list[dict[str, Any]] = []

    with dataset_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i not in selected_by_index:
                continue

            row_id = selected_by_index[i]["id"]
            human_text = row.get("text") or ""
            ai_text = row.get("source_text") or ""

            human_features = extract_text_features(
                human_text,
                nlp,
                tokenizer,
                model,
                device,
                exp004_module,
                exp001_module,
            )
            ai_features = extract_text_features(
                ai_text,
                nlp,
                tokenizer,
                model,
                device,
                exp004_module,
                exp001_module,
            )

            pair_results.append(
                {
                    "row_index": i,
                    "id": row_id,
                    "instructions_char_count": len(row.get("instructions") or ""),
                    "human": human_features,
                    "ai": ai_features,
                }
            )

    pair_results.sort(key=lambda x: x["row_index"])

    distributions = summarize_distributions(pair_results)

    output = {
        "experiment_id": EXPERIMENT_ID,
        "name": EXPERIMENT_NAME,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "path": str(dataset_path),
            "semantics": {
                "text": "human/student-written text",
                "source_text": "AI-generated text",
                "instructions": "generation/task context",
            },
            "row_scan": {
                "total_rows": usable_info["total_rows"],
                "usable_rows": len(usable_info["usable_rows"]),
                "unusable_reasons": usable_info["unusable_reasons"],
            },
            "integrity_before": dataset_integrity_before,
            "integrity_after": file_integrity(dataset_path),
        },
        "environment": environment_info(),
        "sampling": {
            "target_sample_size": TARGET_SAMPLE_SIZE,
            "seed": SAMPLE_SEED,
            "selected_count": selection["selected_count"],
            "shortfall_reason": selection["shortfall_reason"],
            "selected_row_indices": [r["row_index"] for r in selection["selected_rows"]],
            "selected_row_ids": [r["id"] for r in selection["selected_rows"]],
            "pair_preservation": True,
        },
        "inherited_feature_parameters": {
            "source_experiment": "EXP-004",
            "exp004_file": str(EXP004_PATH),
            "perplexity_source_experiment": "EXP-001",
            "perplexity_model": exp004_module.MODEL_ID,
            "spacy_model": exp004_module.SPACY_MODEL,
            "mattr_window": exp004_module.MATTR_WINDOW,
            "perplexity_document_aggregation": "median_of_valid_sentence_perplexities",
            "feature_reuse": {
                "sentence_length_cv": "EXP-004 sentence_length_cv",
                "mattr": "EXP-004 mattr",
                "pos_3gram_entropy": "EXP-004 pos_trigram_entropy",
                "lexical_tokenization": "EXP-004 tokenize_for_lexical_features",
                "perplexity": "EXP-001 calculate_perplexity loaded through EXP-004 load_exp001_module",
            },
        },
        "pair_results": pair_results,
        "distribution_summary": distributions,
        "timing_seconds": time.perf_counter() - started,
    }

    output["validation"] = validate_results(output)

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"results_written={RESULTS_PATH}")
    print(f"selected_count={selection['selected_count']}")
    print(f"validation_all_passed={output['validation']['all_passed']}")


if __name__ == "__main__":
    main()
