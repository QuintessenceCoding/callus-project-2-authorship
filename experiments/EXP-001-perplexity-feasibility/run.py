"""EXP-001: local sentence-level perplexity feasibility.

This is an isolated experiment, not production detection code.
It measures whether distilgpt2 can produce local token-level logits on CPU
and whether shifted causal-LM perplexity behaves numerically.
"""

from __future__ import annotations

import json
import math
import platform
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


EXPERIMENT_ID = "EXP-001"
MODEL_ID = "distilgpt2"
RESULTS_PATH = Path(__file__).resolve().parent / "results" / "results.json"
REPRO_TOLERANCE = 1e-9


@dataclass(frozen=True)
class TestInput:
    test_id: str
    category: str
    text: str
    repeat_count: int = 1


TEST_INPUTS = [
    TestInput(
        "A-very-short",
        "valid",
        "The library closed early.",
        repeat_count=3,
    ),
    TestInput(
        "B-medium",
        "valid",
        "Although the lab was quiet, I kept revising my notes because the problem finally felt solvable.",
    ),
    TestInput(
        "C-long",
        "valid",
        "During the summer before my final year of school, I volunteered at a community clinic, learned how easily small administrative mistakes could delay care, and began building a simple checklist that helped patients prepare the documents they needed before arriving.",
    ),
    TestInput(
        "D-paragraph",
        "valid",
        (
            "My first robotics project failed in the most ordinary way: a loose wire and a rushed assumption. "
            "Instead of replacing the parts, our team traced the circuit together and wrote down every test we had skipped. "
            "That habit of slowing down became more valuable than the robot itself."
        ),
    ),
    TestInput(
        "E-admissions-style",
        "valid",
        (
            "I used to think leadership meant having the clearest answer in the room. "
            "While organizing weekend tutoring sessions for younger students, I learned that the quieter work mattered more: "
            "listening when someone was embarrassed to ask for help, changing the lesson when an example did not land, and "
            "admitting when I needed to prepare better. By the end of the year, the program had become less about my plan "
            "and more about the trust our group built together."
        ),
    ),
    TestInput("EDGE-empty", "edge", ""),
    TestInput("EDGE-whitespace", "edge", "   \t  \n  "),
    TestInput("EDGE-extremely-short", "edge", "Hi"),
    TestInput("EDGE-one-usable-prediction", "edge", "Hello world"),
]


def count_words(text: str) -> int:
    return len(text.split())


def finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def environment_info() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "device": "cpu",
    }


def calculate_perplexity(
    text: str,
    tokenizer: Any,
    model: Any,
    device: torch.device,
) -> dict[str, Any]:
    started = time.perf_counter()
    warnings: list[str] = []

    encoded = tokenizer(text, return_tensors="pt", add_special_tokens=False)
    input_ids = encoded["input_ids"].to(device)
    token_count = int(input_ids.shape[-1])
    usable_prediction_count = max(token_count - 1, 0)

    base_result: dict[str, Any] = {
        "char_count": len(text),
        "word_count": count_words(text),
        "token_count": token_count,
        "usable_prediction_token_count": usable_prediction_count,
        "finite": False,
        "warnings": warnings,
        "errors": [],
    }

    if token_count < 2:
        elapsed = time.perf_counter() - started
        return {
            **base_result,
            "status": "insufficient_input",
            "reason": "At least two tokens are required because token 1 has no preceding-token prediction in the supplied sequence.",
            "perplexity": None,
            "mean_nll": None,
            "inference_time_seconds": elapsed,
            "tokens_per_second": None,
        }

    if text.strip() == "":
        elapsed = time.perf_counter() - started
        return {
            **base_result,
            "status": "insufficient_input",
            "reason": "Whitespace-only text has tokens but no lexical content suitable for an evidence-first measurement.",
            "perplexity": None,
            "mean_nll": None,
            "inference_time_seconds": elapsed,
            "tokens_per_second": None,
        }

    if usable_prediction_count == 1:
        warnings.append("Only one token prediction is available; perplexity is finite but not stable evidence.")

    with torch.inference_mode():
        inference_started = time.perf_counter()
        outputs = model(input_ids=input_ids)
        inference_time = time.perf_counter() - inference_started

        logits = outputs.logits

        # Causal alignment:
        # input_ids:     [t1, t2, t3, t4]
        # shift_logits: predictions for [t2, t3, t4]
        # shift_labels:                 [t2, t3, t4]
        # The first token has no in-sequence context and is excluded.
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., 1:].contiguous()

        token_nll = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            reduction="none",
        )
        mean_nll_tensor = token_nll.mean()
        perplexity_tensor = torch.exp(mean_nll_tensor)

    mean_nll = float(mean_nll_tensor.item())
    perplexity = float(perplexity_tensor.item())
    finite = math.isfinite(mean_nll) and math.isfinite(perplexity)

    if not finite:
        warnings.append("Non-finite mean NLL or perplexity produced; result is not treated as successful.")

    tokens_per_second = None
    if inference_time > 0:
        tokens_per_second = usable_prediction_count / inference_time

    return {
        **base_result,
        "status": "ok" if finite else "non_finite",
        "perplexity": finite_or_none(perplexity),
        "mean_nll": finite_or_none(mean_nll),
        "inference_time_seconds": inference_time,
        "tokens_per_second": finite_or_none(tokens_per_second) if tokens_per_second is not None else None,
        "finite": finite,
    }


def run_repeated_measurements(
    test_input: TestInput,
    tokenizer: Any,
    model: Any,
    device: torch.device,
) -> dict[str, Any]:
    runs = [
        calculate_perplexity(test_input.text, tokenizer, model, device)
        for _ in range(test_input.repeat_count)
    ]
    perplexities = [
        run["perplexity"]
        for run in runs
        if run.get("status") == "ok" and run.get("perplexity") is not None
    ]

    observation: dict[str, Any] = {
        "repeat_count": test_input.repeat_count,
        "perplexities": perplexities,
        "max_absolute_difference": None,
        "tolerance": REPRO_TOLERANCE,
        "effectively_identical": None,
    }

    if len(perplexities) >= 2:
        max_abs_diff = max(abs(value - perplexities[0]) for value in perplexities[1:])
        observation.update(
            {
                "max_absolute_difference": max_abs_diff,
                "effectively_identical": max_abs_diff <= REPRO_TOLERANCE,
            }
        )

    return {
        "test_id": test_input.test_id,
        "category": test_input.category,
        "text": test_input.text,
        "runs": runs,
        "selected_run": runs[0],
        "reproducibility": observation,
    }


def summarize_performance(results: list[dict[str, Any]], load_time: float, total_time: float) -> dict[str, Any]:
    ok_runs = [
        item["selected_run"]
        for item in results
        if item["selected_run"].get("status") == "ok"
    ]
    inference_times = [run["inference_time_seconds"] for run in ok_runs]
    tokens_per_second = [
        run["tokens_per_second"]
        for run in ok_runs
        if run.get("tokens_per_second") is not None
    ]

    return {
        "model_load_time_seconds": load_time,
        "first_successful_inference_time_seconds": inference_times[0] if inference_times else None,
        "median_successful_inference_time_seconds": statistics.median(inference_times) if inference_times else None,
        "median_tokens_per_second": statistics.median(tokens_per_second) if tokens_per_second else None,
        "total_experiment_runtime_seconds": total_time,
    }


def main() -> None:
    experiment_started = time.perf_counter()
    torch.manual_seed(0)
    torch.set_num_threads(max(torch.get_num_threads(), 1))
    device = torch.device("cpu")

    print(f"{EXPERIMENT_ID}: loading {MODEL_ID} on CPU")
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    model.to(device)
    model.eval()
    load_time = time.perf_counter() - load_started

    print(f"model_load_time_seconds={load_time:.6f}")
    print("causal_shift=input_ids[:, 1:] labels are scored by logits[:, :-1, :]")

    measurements = []
    for test_input in TEST_INPUTS:
        item = run_repeated_measurements(test_input, tokenizer, model, device)
        measurements.append(item)
        selected = item["selected_run"]
        ppl = selected["perplexity"]
        ppl_text = f"{ppl:.6f}" if ppl is not None else "None"
        tps = selected["tokens_per_second"]
        tps_text = f"{tps:.2f}" if tps is not None else "None"
        print(
            f"{test_input.test_id}: status={selected['status']} "
            f"tokens={selected['token_count']} usable={selected['usable_prediction_token_count']} "
            f"ppl={ppl_text} time_s={selected['inference_time_seconds']:.6f} tps={tps_text}"
        )

    total_time = time.perf_counter() - experiment_started
    output = {
        "experiment_id": EXPERIMENT_ID,
        "name": "Local Perplexity Feasibility",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": {
            "identifier": MODEL_ID,
            "source": "Hugging Face Transformers",
            "execution_device": "cpu",
        },
        "environment": environment_info(),
        "method": {
            "token_alignment": {
                "input_ids": "[t1, t2, t3, t4]",
                "shift_logits": "predictions for [t2, t3, t4]",
                "shift_labels": "[t2, t3, t4]",
                "excluded": "t1 has no preceding-token prediction inside the supplied sequence",
            },
            "calculation": "mean token negative log likelihood from shifted logits, then exp(mean NLL)",
            "reproducibility_tolerance": REPRO_TOLERANCE,
        },
        "measurements": measurements,
        "performance": summarize_performance(measurements, load_time, total_time),
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"results_written={RESULTS_PATH}")
    print(f"total_experiment_runtime_seconds={total_time:.6f}")


if __name__ == "__main__":
    main()
