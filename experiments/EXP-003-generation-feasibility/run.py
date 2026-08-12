"""EXP-003: local instruction-model generation feasibility.

This isolated experiment compares two small open-weight instruction models
using one controlled essay-generation prompt. It does not construct Essay
Families or write generated outputs into the project dataset.
"""

from __future__ import annotations

import gc
import hashlib
import json
import math
import os
import platform
import re
import statistics
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


EXPERIMENT_ID = "EXP-003"
RESULTS_PATH = Path(__file__).resolve().parent / "results" / "results.json"
DEVICE_NAME = "cpu"
SEED = 7
MAX_NEW_TOKENS = 420
MIN_ACCEPTABLE_WORDS = 250
MAX_ACCEPTABLE_WORDS = 600

SYSTEM_PROMPT = (
    "You write clear, natural, reflective student essays. "
    "Follow the user's task directly. Do not mention AI, prompts, models, "
    "experiments, or instructions."
)

CONTROLLED_TASK = (
    "Write an original reflective essay of approximately 300 to 500 words. "
    "Task: Describe a time when you changed your approach after a setback. "
    "Focus on specific actions, reflection, and what you learned."
)


@dataclass(frozen=True)
class CandidateModel:
    model_id: str
    rationale: str


CANDIDATE_MODELS = [
    CandidateModel(
        "HuggingFaceTB/SmolLM2-135M-Instruct",
        "Very small instruction-tuned causal model intended to be practical on CPU.",
    ),
    CandidateModel(
        "Qwen/Qwen2.5-0.5B-Instruct",
        "Sub-1B instruction-tuned causal model selected as a stronger small CPU candidate.",
    ),
]


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def finite_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return value if math.isfinite(value) else None


def environment_info() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "device": DEVICE_NAME,
        "torch_num_threads": torch.get_num_threads(),
    }


def model_cache_dir(model_id: str) -> Path:
    cache_root = os.environ.get("HF_HUB_CACHE")
    if cache_root:
        hub = Path(cache_root)
    else:
        hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
        hub = hf_home / "hub"
    return hub / f"models--{model_id.replace('/', '--')}"


def directory_size_bytes(path: Path) -> int | None:
    if not path.exists():
        return None
    total = 0
    for file_path in path.rglob("*"):
        if file_path.is_file():
            try:
                total += file_path.stat().st_size
            except OSError:
                continue
    return total


def format_prompt(tokenizer: Any) -> tuple[str, str]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": CONTROLLED_TASK},
    ]
    try:
        if getattr(tokenizer, "chat_template", None):
            return (
                tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                ),
                "chat_template",
            )
    except Exception:
        pass

    return (
        f"System:\n{SYSTEM_PROMPT}\n\nUser:\n{CONTROLLED_TASK}\n\nAssistant:\n",
        "plain_instruction",
    )


def repeated_ngram_ratio(text: str, n: int = 4) -> float | None:
    words = [word.lower() for word in re.findall(r"\b[\w'-]+\b", text)]
    if len(words) < n * 2:
        return None
    ngrams = [tuple(words[index : index + n]) for index in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / len(ngrams)


def quality_checks(text: str) -> dict[str, Any]:
    lower = text.lower()
    word_count = count_words(text)
    prompt_leakage_terms = [
        "as an ai",
        "language model",
        "prompt",
        "instruction",
        "controlled local generation",
        "experiment",
    ]
    leaked_terms = [term for term in prompt_leakage_terms if term in lower]
    repeated_ratio = repeated_ngram_ratio(text)
    line_counts = Counter(line.strip() for line in text.splitlines() if line.strip())
    repeated_lines = [line for line, count in line_counts.items() if count > 1]

    task_keywords = ["setback", "changed", "approach", "learned", "reflection", "mistake"]
    keyword_hits = [keyword for keyword in task_keywords if keyword in lower]
    ends_with_sentence_punctuation = bool(re.search(r'[.!?]["\')\]]?\s*$', text.strip()))

    return {
        "non_empty": bool(text.strip()),
        "word_count": word_count,
        "approximately_requested_length": MIN_ACCEPTABLE_WORDS <= word_count <= MAX_ACCEPTABLE_WORDS,
        "prompt_leakage_terms": leaked_terms,
        "no_prompt_leakage": not leaked_terms,
        "task_keyword_hits": keyword_hits,
        "has_task_keyword_signal": len(keyword_hits) >= 2,
        "ends_with_sentence_punctuation": ends_with_sentence_punctuation,
        "repeated_4gram_ratio": finite_or_none(repeated_ratio),
        "obvious_repeated_lines": repeated_lines[:5],
        "obvious_repetition": (repeated_ratio is not None and repeated_ratio > 0.08) or bool(repeated_lines),
    }


def generate_for_model(candidate: CandidateModel, device: torch.device) -> dict[str, Any]:
    print(f"{EXPERIMENT_ID}: loading {candidate.model_id} on CPU")
    started = time.perf_counter()
    load_started = time.perf_counter()

    result: dict[str, Any] = {
        "model_id": candidate.model_id,
        "rationale": candidate.rationale,
        "runtime": "Hugging Face Transformers",
        "device": DEVICE_NAME,
        "status": "failed",
        "errors": [],
        "warnings": [],
    }

    try:
        tokenizer = AutoTokenizer.from_pretrained(candidate.model_id)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(candidate.model_id)
        model.to(device)
        model.eval()
        load_time = time.perf_counter() - load_started

        parameter_count = sum(parameter.numel() for parameter in model.parameters())
        cache_dir = model_cache_dir(candidate.model_id)
        prompt_text, prompt_format = format_prompt(tokenizer)
        encoded = tokenizer(prompt_text, return_tensors="pt").to(device)
        prompt_token_count = int(encoded["input_ids"].shape[-1])

        torch.manual_seed(SEED)
        generation_started = time.perf_counter()
        with torch.inference_mode():
            output_ids = model.generate(
                **encoded,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                repetition_penalty=1.05,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        generation_time = time.perf_counter() - generation_started

        generated_ids = output_ids[:, prompt_token_count:]
        generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True).strip()
        output_token_count = int(generated_ids.shape[-1])
        tokens_per_second = output_token_count / generation_time if generation_time > 0 else None
        total_time = time.perf_counter() - started
        checks = quality_checks(generated_text)
        completed = output_token_count < MAX_NEW_TOKENS
        checks["likely_truncated"] = (not completed) or (not checks["ends_with_sentence_punctuation"])

        if output_token_count >= MAX_NEW_TOKENS:
            result["warnings"].append("Generation reached max_new_tokens; output may have been truncated.")

        result.update(
            {
                "status": "ok" if checks["non_empty"] else "empty_output",
                "model_revision": getattr(model.config, "_commit_hash", None),
                "model_type": getattr(model.config, "model_type", None),
                "parameter_count": parameter_count,
                "approximate_local_cache_size_bytes": directory_size_bytes(cache_dir),
                "load_time_seconds": load_time,
                "generation_time_seconds": generation_time,
                "total_model_runtime_seconds": total_time,
                "prompt_format": prompt_format,
                "prompt_token_count": prompt_token_count,
                "max_new_tokens": MAX_NEW_TOKENS,
                "generation_parameters": {
                    "do_sample": False,
                    "temperature": None,
                    "top_p": None,
                    "repetition_penalty": 1.05,
                    "seed": SEED,
                },
                "generation_completed_before_token_limit": completed,
                "output_token_count": output_token_count,
                "tokens_per_second": finite_or_none(tokens_per_second),
                "output_word_count": checks["word_count"],
                "output_char_count": len(generated_text),
                "output_sha256": hashlib.sha256(generated_text.encode("utf-8")).hexdigest(),
                "generated_text": generated_text,
                "quality_checks": checks,
            }
        )

        tps_text = f"{tokens_per_second:.2f}" if tokens_per_second is not None else "None"
        print(
            f"{candidate.model_id}: status={result['status']} "
            f"load_s={load_time:.3f} gen_s={generation_time:.3f} "
            f"tokens={output_token_count} words={checks['word_count']} "
            f"tps={tps_text}"
        )
    except Exception as exc:
        total_time = time.perf_counter() - started
        result.update(
            {
                "status": "failed",
                "total_model_runtime_seconds": total_time,
                "error_type": type(exc).__name__,
                "errors": [str(exc)],
            }
        )
        print(f"{candidate.model_id}: failed {type(exc).__name__}: {exc}")
    finally:
        try:
            del model
        except UnboundLocalError:
            pass
        try:
            del tokenizer
        except UnboundLocalError:
            pass
        gc.collect()

    return result


def summarize_results(model_results: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [item for item in model_results if item.get("status") == "ok"]
    successful_quality = [
        item
        for item in successful
        if item.get("quality_checks", {}).get("non_empty")
        and item.get("quality_checks", {}).get("approximately_requested_length")
        and item.get("quality_checks", {}).get("no_prompt_leakage")
        and item.get("quality_checks", {}).get("has_task_keyword_signal")
        and not item.get("quality_checks", {}).get("likely_truncated")
        and not item.get("quality_checks", {}).get("obvious_repetition")
    ]
    generation_times = [
        item["generation_time_seconds"]
        for item in successful
        if item.get("generation_time_seconds") is not None
    ]
    token_rates = [
        item["tokens_per_second"]
        for item in successful
        if item.get("tokens_per_second") is not None
    ]

    return {
        "candidate_model_count": len(model_results),
        "successful_generation_count": len(successful),
        "basic_quality_pass_count": len(successful_quality),
        "median_generation_time_seconds": statistics.median(generation_times) if generation_times else None,
        "median_tokens_per_second": statistics.median(token_rates) if token_rates else None,
        "all_successful_models": [item["model_id"] for item in successful],
        "quality_pass_models": [item["model_id"] for item in successful_quality],
    }


def main() -> None:
    experiment_started = time.perf_counter()
    torch.manual_seed(SEED)
    torch.set_num_threads(max(torch.get_num_threads(), 1))
    device = torch.device(DEVICE_NAME)

    model_results = [generate_for_model(candidate, device) for candidate in CANDIDATE_MODELS]
    total_time = time.perf_counter() - experiment_started

    output = {
        "experiment_id": EXPERIMENT_ID,
        "name": "Local Generation Feasibility",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Feasibility only; generated samples are not dataset variants or Essay Families.",
        "constraints": {
            "cost": "₹0",
            "paid_apis_used": False,
            "production_code_modified": False,
            "dataset_generation_performed": False,
            "essay_families_created": False,
        },
        "environment": environment_info(),
        "controlled_task": {
            "system_prompt": SYSTEM_PROMPT,
            "user_task": CONTROLLED_TASK,
            "target_words": "approximately 300-500",
        },
        "model_results": model_results,
        "summary": summarize_results(model_results),
        "total_experiment_runtime_seconds": total_time,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"results_written={RESULTS_PATH}")
    print(f"total_experiment_runtime_seconds={total_time:.3f}")


if __name__ == "__main__":
    main()
