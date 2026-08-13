"""EXP-004: feature extraction laboratory.

This isolated experiment converts small fixed essay fixtures into quantitative
linguistic features. It is intentionally not a detector and does not perform
classification, thresholding, anomaly scoring, API work, or UI work.
"""

from __future__ import annotations

import importlib.util
import json
import math
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import spacy
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


EXPERIMENT_ID = "EXP-004"
EXPERIMENT_NAME = "Feature Extraction Laboratory"
MODEL_ID = "distilgpt2"
SPACY_MODEL = "en_core_web_sm"
MATTR_WINDOW = 25

EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = EXPERIMENT_DIR / "results" / "results.json"
EXP001_PATH = (
    EXPERIMENT_DIR.parent / "EXP-001-perplexity-feasibility" / "run.py"
)


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    category: str
    text: str


FIXTURES = [
    Fixture(
        fixture_id="fixture-main-essay",
        category="main",
        text=(
            "I used to think leadership meant always speaking first. "
            "During my junior year, I coordinated peer tutoring at our library, "
            "and the role forced me to listen more carefully than I ever had before. "
            "When a lesson failed, we documented what confused students and rewrote the "
            "examples together. By spring, the program was less about my planning and "
            "more about routines the whole team could maintain."
        ),
    ),
    Fixture(
        fixture_id="fixture-edge-short",
        category="edge",
        text="Hi",
    ),
]


def load_exp001_module() -> Any:
    if not EXP001_PATH.exists():
        raise FileNotFoundError(f"EXP-001 implementation not found: {EXP001_PATH}")

    spec = importlib.util.spec_from_file_location("exp001_run", EXP001_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load EXP-001 module specification.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    required_symbol = "calculate_perplexity"
    if not hasattr(module, required_symbol):
        raise RuntimeError(
            f"EXP-001 module does not expose required function: {required_symbol}"
        )

    return module


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


def finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def tokenize_for_lexical_features(doc: Any) -> list[str]:
    return [
        tok.text.lower()
        for tok in doc
        if not tok.is_space and tok.is_alpha
    ]


def mattr(tokens: list[str], window_size: int) -> tuple[float | None, dict[str, Any]]:
    if len(tokens) < window_size:
        return None, {
            "available": False,
            "reason": (
                f"insufficient_tokens_for_window: have={len(tokens)} require_at_least={window_size}"
            ),
            "window_size": window_size,
            "token_count": len(tokens),
        }

    ratios: list[float] = []
    for start in range(0, len(tokens) - window_size + 1):
        window = tokens[start : start + window_size]
        ratio = len(set(window)) / window_size
        ratios.append(ratio)

    value = statistics.mean(ratios)
    return value, {
        "available": True,
        "reason": None,
        "window_size": window_size,
        "token_count": len(tokens),
        "window_count": len(ratios),
    }


def pos_trigram_entropy(doc: Any) -> tuple[float | None, dict[str, Any]]:
    pos_tags = [
        tok.pos_
        for tok in doc
        if not tok.is_space and not tok.is_punct
    ]

    if len(pos_tags) < 3:
        return None, {
            "available": False,
            "reason": f"insufficient_pos_tags_for_3grams: have={len(pos_tags)} require_at_least=3",
            "pos_tag_count": len(pos_tags),
            "trigram_count": 0,
        }

    counts: dict[tuple[str, str, str], int] = {}
    for i in range(len(pos_tags) - 2):
        gram = (pos_tags[i], pos_tags[i + 1], pos_tags[i + 2])
        counts[gram] = counts.get(gram, 0) + 1

    total = sum(counts.values())
    entropy = 0.0
    for c in counts.values():
        p = c / total
        entropy -= p * math.log2(p)

    return entropy, {
        "available": True,
        "reason": None,
        "pos_tag_count": len(pos_tags),
        "trigram_count": total,
        "unique_trigram_count": len(counts),
    }


def sentence_length_cv(sentence_lengths: list[int]) -> tuple[float | None, dict[str, Any]]:
    if len(sentence_lengths) < 2:
        return None, {
            "available": False,
            "reason": "insufficient_sentences_for_cv: require_at_least=2",
            "sentence_count": len(sentence_lengths),
        }

    mean_len = statistics.mean(sentence_lengths)
    if mean_len == 0:
        return None, {
            "available": False,
            "reason": "zero_mean_sentence_length",
            "sentence_count": len(sentence_lengths),
        }

    stdev_len = statistics.stdev(sentence_lengths)
    return stdev_len / mean_len, {
        "available": True,
        "reason": None,
        "sentence_count": len(sentence_lengths),
        "mean_sentence_length_tokens": mean_len,
        "stdev_sentence_length_tokens": stdev_len,
    }


def analyze_fixture(
    fixture: Fixture,
    nlp: Any,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    exp001_module: Any,
) -> dict[str, Any]:
    analysis_started = time.perf_counter()
    doc = nlp(fixture.text)

    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    sentence_rows: list[dict[str, Any]] = []
    sentence_lengths_for_cv: list[int] = []

    for idx, sentence_text in enumerate(sentences, start=1):
        ppl_result = exp001_module.calculate_perplexity(
            sentence_text,
            tokenizer,
            model,
            device,
        )

        # Sentence length for CV uses spaCy tokenization, excluding space/punctuation.
        sent_doc = nlp.make_doc(sentence_text)
        length_for_cv = len([t for t in sent_doc if not t.is_space and not t.is_punct])
        sentence_lengths_for_cv.append(length_for_cv)

        sentence_rows.append(
            {
                "sentence_id": idx,
                "sentence_text": sentence_text,
                "token_count": ppl_result.get("token_count"),
                "perplexity": ppl_result.get("perplexity"),
                "perplexity_status": ppl_result.get("status"),
                "perplexity_reason_unavailable": ppl_result.get("reason"),
                "perplexity_warnings": ppl_result.get("warnings", []),
            }
        )

    cv_value, cv_meta = sentence_length_cv(sentence_lengths_for_cv)

    lexical_tokens = tokenize_for_lexical_features(doc)
    mattr_value, mattr_meta = mattr(lexical_tokens, MATTR_WINDOW)

    pos_entropy_value, pos_meta = pos_trigram_entropy(doc)

    duration = time.perf_counter() - analysis_started

    return {
        "fixture_id": fixture.fixture_id,
        "category": fixture.category,
        "input_text": fixture.text,
        "sentence_count": len(sentences),
        "sentence_features": sentence_rows,
        "essay_features": {
            "sentence_length_cv": {
                "value": finite_or_none(cv_value) if cv_value is not None else None,
                "meta": cv_meta,
            },
            "mattr": {
                "value": finite_or_none(mattr_value) if mattr_value is not None else None,
                "meta": mattr_meta,
            },
            "pos_3gram_entropy": {
                "value": finite_or_none(pos_entropy_value)
                if pos_entropy_value is not None
                else None,
                "meta": pos_meta,
            },
        },
        "timing_seconds": duration,
    }


def validate_fixture_result(result: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    sentence_rows = result.get("sentence_features", [])

    checks["sentence_count_matches"] = {
        "passed": result.get("sentence_count") == len(sentence_rows),
        "observed_sentence_count": result.get("sentence_count"),
        "observed_rows": len(sentence_rows),
    }

    token_counts = [row.get("token_count") for row in sentence_rows if row.get("token_count") is not None]
    checks["token_counts_non_negative"] = {
        "passed": all(isinstance(v, int) and v >= 0 for v in token_counts),
        "observed_token_counts": token_counts,
    }

    ok_perplexities = [
        row.get("perplexity")
        for row in sentence_rows
        if row.get("perplexity_status") == "ok"
    ]
    checks["successful_perplexities_finite"] = {
        "passed": all(v is not None and math.isfinite(v) for v in ok_perplexities),
        "observed_perplexities": ok_perplexities,
    }

    cv_obj = result["essay_features"]["sentence_length_cv"]
    cv_available = cv_obj["value"] is not None
    cv_sentence_count = cv_obj["meta"].get("sentence_count", 0)
    cv_expected = cv_sentence_count >= 2
    checks["sentence_length_cv_validity"] = {
        "passed": (not cv_expected and not cv_available)
        or (cv_expected and cv_available and math.isfinite(cv_obj["value"])),
        "cv_value": cv_obj["value"],
        "cv_available": cv_available,
        "cv_expected": cv_expected,
        "meta": cv_obj["meta"],
    }

    mattr_obj = result["essay_features"]["mattr"]
    mattr_value = mattr_obj["value"]
    mattr_ok = True
    if mattr_value is not None:
        mattr_ok = 0.0 <= mattr_value <= 1.0 and math.isfinite(mattr_value)
    checks["mattr_valid_range"] = {
        "passed": mattr_ok,
        "mattr_value": mattr_value,
        "meta": mattr_obj["meta"],
    }

    pos_obj = result["essay_features"]["pos_3gram_entropy"]
    pos_value = pos_obj["value"]
    pos_trigram_count = pos_obj["meta"].get("trigram_count", 0)
    pos_expected = pos_trigram_count > 0
    checks["pos_entropy_finite_when_ngrams_exist"] = {
        "passed": (not pos_expected and pos_value is None)
        or (pos_expected and pos_value is not None and math.isfinite(pos_value)),
        "pos_entropy_value": pos_value,
        "meta": pos_obj["meta"],
    }

    return {
        "checks": checks,
        "all_passed": all(item["passed"] for item in checks.values()),
    }


def main() -> None:
    started = time.perf_counter()
    torch.manual_seed(0)
    torch.set_num_threads(max(torch.get_num_threads(), 1))
    device = torch.device("cpu")

    exp001_module = load_exp001_module()

    nlp = spacy.load(SPACY_MODEL)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    model.to(device)
    model.eval()

    fixture_results = [
        analyze_fixture(fixture, nlp, tokenizer, model, device, exp001_module)
        for fixture in FIXTURES
    ]

    validations = {
        item["fixture_id"]: validate_fixture_result(item)
        for item in fixture_results
    }

    output = {
        "experiment_id": EXPERIMENT_ID,
        "name": EXPERIMENT_NAME,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment_info(),
        "method": {
            "sentence_segmentation": {
                "library": "spaCy",
                "model": SPACY_MODEL,
            },
            "perplexity": {
                "source_experiment": "EXP-001",
                "source_file": str(EXP001_PATH),
                "model_identifier": MODEL_ID,
                "device": "cpu",
                "causal_shift": "Reused EXP-001 calculate_perplexity implementation.",
            },
            "essay_features": {
                "sentence_length_cv": "stdev/mean of per-sentence spaCy token counts (excluding punctuation and spaces)",
                "mattr": f"moving-average type-token ratio over lowercase alphabetic tokens, window={MATTR_WINDOW}",
                "pos_3gram_entropy": "Shannon entropy (base 2) of POS-tag trigrams over non-space, non-punctuation tokens",
            },
            "edge_case_fixture_included": True,
        },
        "fixtures": fixture_results,
        "validation": {
            "per_fixture": validations,
            "all_passed": all(v["all_passed"] for v in validations.values()),
        },
        "timing_seconds": time.perf_counter() - started,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"results_written={RESULTS_PATH}")
    print(f"fixtures_processed={len(fixture_results)}")
    print(f"validation_all_passed={output['validation']['all_passed']}")


if __name__ == "__main__":
    main()
