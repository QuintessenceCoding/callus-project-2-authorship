"""EXP-007: hybrid local-anomaly feasibility.

This bounded experiment inserts a known two-sentence AI block into otherwise
human DAIGT essays and asks whether the inserted sentences rank as local
within-document anomalies. It is not a production detector and does not set
thresholds, train classifiers, or modify application code.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import platform
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import spacy
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


EXPERIMENT_ID = "EXP-007"
EXPERIMENT_NAME = "Hybrid Local-Anomaly Feasibility"
PAIR_COUNT = 20

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = EXPERIMENT_DIR / "results" / "results.json"

DAIGT_CSV = ROOT / "data" / "raw" / "daigt_external" / "daigt_external_dataset.csv"
EXP004_PATH = ROOT / "experiments" / "EXP-004-feature-extraction" / "run.py"
EXP005_RESULTS = (
    ROOT
    / "experiments"
    / "EXP-005-feature-distribution"
    / "results"
    / "results.json"
)

FEATURE_NAMES = [
    "perplexity",
    "sentence_length",
    "local_mattr",
    "local_pos_3gram_entropy",
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


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def finite_or_none(value: Any) -> float | None:
    return float(value) if is_finite_number(value) else None


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

    ordered = sorted(values)
    q1 = quantile_linear(ordered, 0.25)
    q3 = quantile_linear(ordered, 0.75)

    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) >= 2 else None,
        "iqr": None if q1 is None or q3 is None else q3 - q1,
        "q1": q1,
        "q3": q3,
        "min": min(values),
        "max": max(values),
    }


def median_and_mad(values: list[float]) -> tuple[float, float]:
    median = statistics.median(values)
    deviations = [abs(v - median) for v in values]
    mad = statistics.median(deviations)
    return median, mad


def robust_z_score(value: Any, reference_values: list[float]) -> dict[str, Any]:
    if not is_finite_number(value):
        return {
            "value": None,
            "available": False,
            "reason": "current_value_unavailable",
            "reference_count": len(reference_values),
        }

    if not reference_values:
        return {
            "value": None,
            "available": False,
            "reason": "no_reference_values",
            "reference_count": 0,
        }

    median, mad = median_and_mad(reference_values)
    if mad == 0:
        return {
            "value": None,
            "available": False,
            "reason": "mad_zero",
            "reference_count": len(reference_values),
            "reference_median": median,
            "reference_mad": mad,
        }

    z = 0.6745 * (float(value) - median) / mad
    return {
        "value": z,
        "available": True,
        "reason": None,
        "reference_count": len(reference_values),
        "reference_median": median,
        "reference_mad": mad,
    }


def segment_sentences(text: str, nlp: Any) -> list[str]:
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def middle_ai_block_start(sentence_count: int) -> int:
    return max(0, (sentence_count // 2) - 1)


def middle_human_insertion_index(sentence_count: int) -> int:
    return sentence_count // 2


def sentence_length(sentence_text: str, nlp: Any) -> dict[str, Any]:
    doc = nlp.make_doc(sentence_text)
    value = len([tok for tok in doc if not tok.is_space and not tok.is_punct])
    return {
        "value": value,
        "meta": {
            "available": True,
            "reason": None,
            "tokenization": "spaCy make_doc; excludes space and punctuation tokens",
        },
    }


def window_indices_for_sentence(index: int, sentence_count: int) -> list[int]:
    if sentence_count <= 1:
        return [index]
    if index == 0:
        return [0, 1]
    if index == sentence_count - 1:
        return [sentence_count - 2, sentence_count - 1]
    return [index - 1, index, index + 1]


def local_window_features(
    window_text: str,
    nlp: Any,
    exp004_module: Any,
) -> dict[str, dict[str, Any]]:
    doc = nlp(window_text)
    lexical_tokens = exp004_module.tokenize_for_lexical_features(doc)
    mattr_value, mattr_meta = exp004_module.mattr(
        lexical_tokens,
        exp004_module.MATTR_WINDOW,
    )
    pos_value, pos_meta = exp004_module.pos_trigram_entropy(doc)

    return {
        "local_mattr": {
            "value": finite_or_none(mattr_value),
            "meta": mattr_meta,
        },
        "local_pos_3gram_entropy": {
            "value": finite_or_none(pos_value),
            "meta": pos_meta,
        },
    }


def perplexity_feature(
    sentence_text: str,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    exp001_module: Any,
) -> dict[str, Any]:
    result = exp001_module.calculate_perplexity(
        sentence_text,
        tokenizer,
        model,
        device,
    )
    status = result.get("status")
    value = result.get("perplexity") if status == "ok" else None
    return {
        "value": finite_or_none(value),
        "meta": {
            "available": is_finite_number(value),
            "reason": None if is_finite_number(value) else result.get("reason") or status,
            "status": status,
            "token_count": result.get("token_count"),
            "usable_prediction_count": result.get("usable_prediction_count"),
            "warnings": result.get("warnings", []),
        },
    }


def construct_hybrid(
    pair_spec: dict[str, Any],
    raw_row: dict[str, str],
    nlp: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    human_sentences = segment_sentences(raw_row.get("text") or "", nlp)
    ai_sentences = segment_sentences(raw_row.get("source_text") or "", nlp)

    base = {
        "pair_id": pair_spec["id"],
        "row_index": pair_spec["row_index"],
        "human_sentence_count": len(human_sentences),
        "ai_sentence_count": len(ai_sentences),
    }

    if len(human_sentences) < 2:
        return None, {**base, "reason": "insufficient_human_sentences_for_middle_insertion"}
    if len(ai_sentences) < 3:
        return None, {**base, "reason": "insufficient_ai_sentences_for_two_sentence_block"}

    ai_start = middle_ai_block_start(len(ai_sentences))
    ai_indices = [ai_start, ai_start + 1]
    ai_block = [ai_sentences[i] for i in ai_indices]

    insertion_index = middle_human_insertion_index(len(human_sentences))
    hybrid_sentences: list[dict[str, Any]] = []

    for human_idx, text in enumerate(human_sentences[:insertion_index]):
        hybrid_sentences.append(
            {
                "hybrid_index": len(hybrid_sentences),
                "origin": "human",
                "text": text,
                "source_human_sentence_index": human_idx,
                "source_ai_sentence_index": None,
            }
        )

    ground_truth_indices: list[int] = []
    for ai_idx, text in zip(ai_indices, ai_block):
        hybrid_idx = len(hybrid_sentences)
        ground_truth_indices.append(hybrid_idx)
        hybrid_sentences.append(
            {
                "hybrid_index": hybrid_idx,
                "origin": "ai_inserted",
                "text": text,
                "source_human_sentence_index": None,
                "source_ai_sentence_index": ai_idx,
            }
        )

    for human_idx, text in enumerate(human_sentences[insertion_index:], start=insertion_index):
        hybrid_sentences.append(
            {
                "hybrid_index": len(hybrid_sentences),
                "origin": "human",
                "text": text,
                "source_human_sentence_index": human_idx,
                "source_ai_sentence_index": None,
            }
        )

    return {
        **base,
        "raw_id": raw_row.get("id") or f"row-{pair_spec['row_index']}",
        "instructions_char_count": len(raw_row.get("instructions") or ""),
        "human_sentences": human_sentences,
        "ai_sentences": ai_sentences,
        "selected_ai_source_sentence_indices": ai_indices,
        "selected_ai_sentence_texts": ai_block,
        "human_insertion_boundary_index": insertion_index,
        "ground_truth_ai_hybrid_sentence_indices": ground_truth_indices,
        "hybrid_sentences": hybrid_sentences,
    }, None


def analyze_hybrid(
    hybrid: dict[str, Any],
    nlp: Any,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    exp004_module: Any,
    exp001_module: Any,
) -> dict[str, Any]:
    sentence_items = hybrid["hybrid_sentences"]
    sentence_texts = [item["text"] for item in sentence_items]
    sentence_count = len(sentence_items)

    sentence_results: list[dict[str, Any]] = []
    for item in sentence_items:
        idx = item["hybrid_index"]
        win_indices = window_indices_for_sentence(idx, sentence_count)
        win_text = " ".join(sentence_texts[i] for i in win_indices)

        features = {
            "perplexity": perplexity_feature(
                item["text"],
                tokenizer,
                model,
                device,
                exp001_module,
            ),
            "sentence_length": sentence_length(item["text"], nlp),
        }
        features.update(local_window_features(win_text, nlp, exp004_module))

        sentence_results.append(
            {
                **item,
                "window_indices": win_indices,
                "window_size": len(win_indices),
                "features": features,
            }
        )

    for feat in FEATURE_NAMES:
        all_values = [
            row["features"][feat]["value"]
            for row in sentence_results
        ]
        for i, row in enumerate(sentence_results):
            reference_values = [
                float(v)
                for j, v in enumerate(all_values)
                if j != i and is_finite_number(v)
            ]
            row["features"][feat]["robust_z"] = robust_z_score(
                row["features"][feat]["value"],
                reference_values,
            )

    finite_anomaly_rows: list[dict[str, Any]] = []
    for row in sentence_results:
        z_values = []
        unavailable_components = {}
        for feat in FEATURE_NAMES:
            z_obj = row["features"][feat]["robust_z"]
            if is_finite_number(z_obj.get("value")):
                z_values.append(abs(float(z_obj["value"])))
            else:
                unavailable_components[feat] = z_obj.get("reason") or "unavailable"

        if z_values:
            score = statistics.mean(z_values)
            reason = None
        else:
            score = None
            reason = "no_available_component_z_scores"

        row["local_anomaly"] = {
            "value": score,
            "component_count": len(z_values),
            "unavailable_component_reasons": unavailable_components,
            "reason": reason,
            "interpretation": "experimental ranking score only; no production threshold",
        }
        if is_finite_number(score):
            finite_anomaly_rows.append(row)

    ranked = sorted(
        finite_anomaly_rows,
        key=lambda r: (-float(r["local_anomaly"]["value"]), r["hybrid_index"]),
    )
    for rank, row in enumerate(ranked, start=1):
        row["local_anomaly"]["rank_descending"] = rank
        row["local_anomaly"]["finite_rank_count"] = len(ranked)
        row["local_anomaly"]["top_50_percent"] = rank <= math.ceil(len(ranked) * 0.50)
        row["local_anomaly"]["top_25_percent"] = rank <= math.ceil(len(ranked) * 0.25)
        row["local_anomaly"]["top_10_percent"] = rank <= math.ceil(len(ranked) * 0.10)

    for row in sentence_results:
        if "rank_descending" not in row["local_anomaly"]:
            row["local_anomaly"].update(
                {
                    "rank_descending": None,
                    "finite_rank_count": len(ranked),
                    "top_50_percent": False,
                    "top_25_percent": False,
                    "top_10_percent": False,
                }
            )

    ai_rows = [row for row in sentence_results if row["origin"] == "ai_inserted"]
    human_rows = [row for row in sentence_results if row["origin"] == "human"]
    ai_scores = [
        float(row["local_anomaly"]["value"])
        for row in ai_rows
        if is_finite_number(row["local_anomaly"]["value"])
    ]
    human_scores = [
        float(row["local_anomaly"]["value"])
        for row in human_rows
        if is_finite_number(row["local_anomaly"]["value"])
    ]

    if ai_scores:
        least_anomalous_ai = min(ai_scores)
        human_above_least_ai = sum(score > least_anomalous_ai for score in human_scores)
    else:
        least_anomalous_ai = None
        human_above_least_ai = None

    ai_sentence_reports = [
        {
            "hybrid_index": row["hybrid_index"],
            "source_ai_sentence_index": row["source_ai_sentence_index"],
            "anomaly_score": row["local_anomaly"]["value"],
            "rank_descending": row["local_anomaly"]["rank_descending"],
            "finite_rank_count": row["local_anomaly"]["finite_rank_count"],
            "top_50_percent": row["local_anomaly"]["top_50_percent"],
            "top_25_percent": row["local_anomaly"]["top_25_percent"],
            "top_10_percent": row["local_anomaly"]["top_10_percent"],
        }
        for row in ai_rows
    ]

    return {
        **hybrid,
        "sentences": sentence_results,
        "per_hybrid_evaluation": {
            "ground_truth_ai_sentence_indices": hybrid["ground_truth_ai_hybrid_sentence_indices"],
            "ai_sentence_ranks": ai_sentence_reports,
            "ai_anomaly_summary": summarize_values(ai_scores),
            "human_anomaly_summary": summarize_values(human_scores),
            "human_sentences_ranked_above_least_anomalous_ai_sentence": human_above_least_ai,
            "least_anomalous_ai_score": least_anomalous_ai,
        },
    }


def aggregate_results(hybrids: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> dict[str, Any]:
    reason_counts = Counter(item["reason"] for item in rejected)
    ai_sentence_reports = []
    all_ai_scores: list[float] = []
    all_human_scores: list[float] = []

    for hybrid in hybrids:
        ai_sentence_reports.extend(hybrid["per_hybrid_evaluation"]["ai_sentence_ranks"])
        all_ai_scores.extend(
            float(row["local_anomaly"]["value"])
            for row in hybrid["sentences"]
            if row["origin"] == "ai_inserted" and is_finite_number(row["local_anomaly"]["value"])
        )
        all_human_scores.extend(
            float(row["local_anomaly"]["value"])
            for row in hybrid["sentences"]
            if row["origin"] == "human" and is_finite_number(row["local_anomaly"]["value"])
        )

    total_ai_gt = len(ai_sentence_reports)
    denominator = total_ai_gt if total_ai_gt else 1

    return {
        "selected_pair_count": PAIR_COUNT,
        "eligible_pair_count": len(hybrids),
        "successful_hybrid_count": len(hybrids),
        "rejected_pair_count": len(rejected),
        "rejected_reason_counts": dict(reason_counts),
        "total_ai_ground_truth_sentences": total_ai_gt,
        "aggregate_top_50_capture_rate": (
            sum(1 for r in ai_sentence_reports if r["top_50_percent"]) / denominator
        ),
        "aggregate_top_25_capture_rate": (
            sum(1 for r in ai_sentence_reports if r["top_25_percent"]) / denominator
        ),
        "aggregate_top_10_capture_rate": (
            sum(1 for r in ai_sentence_reports if r["top_10_percent"]) / denominator
        ),
        "ai_anomaly_summary": summarize_values(all_ai_scores),
        "human_anomaly_summary": summarize_values(all_human_scores),
        "ai_vs_human_median_anomaly_difference": (
            None
            if not all_ai_scores or not all_human_scores
            else statistics.median(all_ai_scores) - statistics.median(all_human_scores)
        ),
        "ai_finite_anomaly_count": len(all_ai_scores),
        "human_finite_anomaly_count": len(all_human_scores),
    }


def load_raw_rows_by_index(path: Path, wanted_indices: set[int]) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i in wanted_indices:
                rows[i] = row
    return rows


def validate_output(output: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    pair_ids = output["selection"]["pair_ids"]
    hybrids = output["hybrids"]

    checks["no_duplicate_pair_ids"] = {
        "passed": len(pair_ids) == len(set(pair_ids)),
        "pair_count": len(pair_ids),
        "unique_pair_count": len(set(pair_ids)),
    }

    checks["raw_dataset_unchanged"] = {
        "passed": output["dataset"]["integrity_before"] == output["dataset"]["integrity_after"],
        "integrity_before": output["dataset"]["integrity_before"],
        "integrity_after": output["dataset"]["integrity_after"],
    }

    exact_two_inserted = True
    inserted_text_matches = True
    ground_truth_valid = True
    human_preserved = True
    finite_anomaly_ok = True
    unavailable_reasons_ok = True
    aggregate_ai_sentence_count = 0

    for hybrid in hybrids:
        gt_indices = hybrid["ground_truth_ai_hybrid_sentence_indices"]
        aggregate_ai_sentence_count += len(gt_indices)
        if len(gt_indices) != 2:
            exact_two_inserted = False

        sentence_count = len(hybrid["sentences"])
        if any(not isinstance(i, int) or i < 0 or i >= sentence_count for i in gt_indices):
            ground_truth_valid = False

        inserted = [hybrid["sentences"][i]["text"] for i in gt_indices if 0 <= i < sentence_count]
        if inserted != hybrid["selected_ai_sentence_texts"]:
            inserted_text_matches = False

        for idx, source_ai_idx in zip(gt_indices, hybrid["selected_ai_source_sentence_indices"]):
            if hybrid["ai_sentences"][source_ai_idx] != hybrid["sentences"][idx]["text"]:
                inserted_text_matches = False

        hybrid_human_sentences = [
            row["text"]
            for row in hybrid["sentences"]
            if row["origin"] == "human"
        ]
        if hybrid_human_sentences != hybrid["human_sentences"]:
            human_preserved = False

        for row in hybrid["sentences"]:
            anomaly = row["local_anomaly"]["value"]
            if anomaly is not None and not is_finite_number(anomaly):
                finite_anomaly_ok = False
            if anomaly is None and not row["local_anomaly"].get("reason"):
                unavailable_reasons_ok = False
            for feat in FEATURE_NAMES:
                feature = row["features"][feat]
                value = feature["value"]
                if value is not None and not is_finite_number(value):
                    finite_anomaly_ok = False
                if value is None and not feature["meta"].get("reason"):
                    unavailable_reasons_ok = False
                z_obj = feature["robust_z"]
                z_value = z_obj.get("value")
                if z_value is not None and not is_finite_number(z_value):
                    finite_anomaly_ok = False
                if z_value is None and not z_obj.get("reason"):
                    unavailable_reasons_ok = False

    aggregate = output["aggregate"]
    counts_consistent = (
        aggregate["selected_pair_count"] == PAIR_COUNT
        and aggregate["successful_hybrid_count"] == len(hybrids)
        and aggregate["rejected_pair_count"] == len(output["rejected_pairs"])
        and aggregate["total_ai_ground_truth_sentences"] == aggregate_ai_sentence_count
        and aggregate["total_ai_ground_truth_sentences"] == len(hybrids) * 2
    )

    checks["every_hybrid_has_exactly_two_inserted_ai_sentences"] = {
        "passed": exact_two_inserted,
    }
    checks["inserted_ai_text_matches_source_sentences"] = {
        "passed": inserted_text_matches,
    }
    checks["ground_truth_indices_valid"] = {
        "passed": ground_truth_valid,
    }
    checks["human_sentence_sequence_preserved"] = {
        "passed": human_preserved,
    }
    checks["finite_anomaly_values_when_present"] = {
        "passed": finite_anomaly_ok,
    }
    checks["unavailable_features_have_explicit_reasons"] = {
        "passed": unavailable_reasons_ok,
    }
    checks["result_counts_internally_consistent"] = {
        "passed": counts_consistent,
        "aggregate_ai_sentence_count": aggregate_ai_sentence_count,
    }

    return {
        "checks": checks,
        "all_passed": all(check["passed"] for check in checks.values()),
    }


def main() -> None:
    started = time.perf_counter()
    torch.manual_seed(0)
    torch.set_num_threads(max(torch.get_num_threads(), 1))
    device = torch.device("cpu")

    if not DAIGT_CSV.exists():
        raise FileNotFoundError(f"Missing DAIGT CSV: {DAIGT_CSV}")
    if not EXP005_RESULTS.exists():
        raise FileNotFoundError(f"Missing EXP-005 results: {EXP005_RESULTS}")

    dataset_integrity_before = file_integrity(DAIGT_CSV)

    exp005 = json.loads(EXP005_RESULTS.read_text(encoding="utf-8"))
    selected_pairs = exp005["pair_results"][:PAIR_COUNT]
    wanted_indices = {int(item["row_index"]) for item in selected_pairs}
    raw_rows = load_raw_rows_by_index(DAIGT_CSV, wanted_indices)

    exp004_module = load_module(EXP004_PATH, "exp004_run")
    exp001_module = exp004_module.load_exp001_module()

    nlp = spacy.load(exp004_module.SPACY_MODEL)
    tokenizer = AutoTokenizer.from_pretrained(exp004_module.MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(exp004_module.MODEL_ID)
    model.to(device)
    model.eval()

    hybrids: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for pair in selected_pairs:
        row_index = int(pair["row_index"])
        raw_row = raw_rows.get(row_index)
        if raw_row is None:
            rejected.append(
                {
                    "pair_id": pair["id"],
                    "row_index": row_index,
                    "reason": "raw_row_not_found",
                }
            )
            continue

        raw_id = raw_row.get("id") or f"row-{row_index}"
        if raw_id != pair["id"]:
            rejected.append(
                {
                    "pair_id": pair["id"],
                    "row_index": row_index,
                    "raw_id": raw_id,
                    "reason": "raw_id_mismatch",
                }
            )
            continue

        hybrid, reject = construct_hybrid(pair, raw_row, nlp)
        if reject is not None:
            rejected.append(reject)
            continue

        assert hybrid is not None
        hybrids.append(
            analyze_hybrid(
                hybrid,
                nlp,
                tokenizer,
                model,
                device,
                exp004_module,
                exp001_module,
            )
        )

    output = {
        "experiment_id": EXPERIMENT_ID,
        "name": EXPERIMENT_NAME,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "type": "bounded synthetic hybrid feasibility experiment",
            "not_a_production_detector": True,
            "no_classifier": True,
            "no_thresholds": True,
            "no_full_dataset_processing": True,
        },
        "dataset": {
            "path": str(DAIGT_CSV),
            "semantics": {
                "text": "human/student-written text",
                "source_text": "AI-generated text",
                "instructions": "shared task/generation context",
            },
            "integrity_before": dataset_integrity_before,
            "integrity_after": file_integrity(DAIGT_CSV),
        },
        "source_selection": {
            "source_experiment": "EXP-005",
            "source_results": str(EXP005_RESULTS),
            "selection_rule": "first 20 pair_results from EXP-005 results.json; no resampling and no new random seed",
        },
        "selection": {
            "requested_pair_count": PAIR_COUNT,
            "selected_pair_count": len(selected_pairs),
            "pair_ids": [item["id"] for item in selected_pairs],
            "row_indices": [int(item["row_index"]) for item in selected_pairs],
        },
        "method": {
            "feature_reuse": {
                "sentence_segmentation": f"spaCy {exp004_module.SPACY_MODEL} from EXP-004",
                "perplexity": "EXP-001 calculate_perplexity loaded through EXP-004 load_exp001_module",
                "lexical_tokenization": "EXP-004 tokenize_for_lexical_features",
                "mattr": f"EXP-004 mattr with window={exp004_module.MATTR_WINDOW}",
                "pos_3gram_entropy": "EXP-004 pos_trigram_entropy",
            },
            "hybrid_construction": {
                "ai_requirement": "at least 3 AI sentences",
                "ai_block": "exactly 2 contiguous AI sentences selected from the middle of source_text segmentation",
                "insertion": "AI block inserted at human sentence boundary floor(human_sentence_count / 2)",
                "rewriting": "no human or AI sentence rewriting; sentence strings are spaCy-segmented and stripped",
            },
            "local_window": {
                "target": "centered 3-sentence window",
                "edge_behavior": "first sentence uses [0, 1]; last sentence uses [n-2, n-1]; interior sentences use [i-1, i, i+1]",
            },
            "robust_anomaly": {
                "formula": "robust_z = 0.6745 * (value - median(reference_values)) / MAD(reference_values)",
                "reference": "other sentence/window values in the same hybrid essay, excluding current sentence",
                "mad_zero_behavior": "component z-score unavailable; no fabricated value",
                "local_anomaly": "mean absolute available component z-scores across perplexity, sentence length, local MATTR, local POS 3-gram entropy",
            },
        },
        "environment": environment_info(),
        "rejected_pairs": rejected,
        "hybrids": hybrids,
        "aggregate": aggregate_results(hybrids, rejected),
        "timing_seconds": time.perf_counter() - started,
    }
    output["validation"] = validate_output(output)

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"results_written={RESULTS_PATH}")
    print(f"selected_pair_count={len(selected_pairs)}")
    print(f"successful_hybrid_count={len(hybrids)}")
    print(f"rejected_pair_count={len(rejected)}")
    print(f"validation_all_passed={output['validation']['all_passed']}")


if __name__ == "__main__":
    main()
