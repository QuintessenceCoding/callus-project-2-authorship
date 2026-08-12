"""EXP-002: perplexity stability by text length.

This isolated experiment reuses the EXP-001 causal-LM perplexity definition.
It evaluates tokenizer-prefixes of the same passages at increasing token
lengths, then summarizes variation across passages and repetitions.
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


EXPERIMENT_ID = "EXP-002"
MODEL_ID = "distilgpt2"
RESULTS_PATH = Path(__file__).resolve().parent / "results" / "results.json"
TARGET_TOKEN_COUNTS = [10, 20, 30, 50, 75, 100, 150, 200]
SHORT_REPEAT_COUNT = 3
REPRO_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Passage:
    passage_id: str
    title: str
    text: str


PASSAGES = [
    Passage(
        "P1",
        "community garden reflection",
        (
            "The first Saturday at the community garden began with a problem I thought I could solve quickly. "
            "A row of seedlings had wilted after a week of heavy rain, and several volunteers were already arguing "
            "about whether to replace them or wait. I wanted to be useful, so I started measuring the soil and writing "
            "down which beds drained slowly. By the afternoon, the answer was less dramatic than anyone expected: "
            "the lowest corner needed a shallow channel, and the new volunteers needed clearer instructions about "
            "watering after storms. The experience stayed with me because it changed how I understood service. "
            "Helping was not only the visible work of planting or carrying tools. It was also the quiet work of "
            "noticing patterns, asking people what they had already tried, and making a plan that someone else could "
            "continue when I was not there. Over the next month, I helped label each bed, rewrite the volunteer notes, "
            "and build a simple schedule that paired experienced gardeners with first-time helpers. The garden looked "
            "healthier by midsummer, but the more important change was in the way our group talked through mistakes. "
            "Instead of blaming the weather or a single missed task, we learned to treat every setback as information. "
            "That habit made the work slower at first, then steadier, and finally more generous."
        ),
    ),
    Passage(
        "P2",
        "robotics notebook reflection",
        (
            "Our robotics team kept a notebook that no one wanted to maintain. At the beginning of the season, it was "
            "a messy folder of sketches, half-finished calculations, and photographs of parts we had already replaced. "
            "I was impatient with it because I preferred building to documenting. That changed after our drivetrain "
            "failed during a practice match and we spent two evenings rediscovering a wiring mistake someone had fixed "
            "weeks earlier. I volunteered to reorganize the notebook, partly out of embarrassment and partly because I "
            "could see how much time we were losing. I made a page for each subsystem, added dates to every test, and "
            "asked teammates to write down not only what worked but what almost worked. The habit felt awkward at first. "
            "People joked that I had become the paperwork captain. Then the notebook started answering questions before "
            "they became arguments. When an arm motor overheated, we found the earlier load readings. When a sensor gave "
            "inconsistent values, we found the calibration notes. By competition day, our robot was still imperfect, but "
            "our decisions were calmer. I learned that engineering is not only a rush toward the clever solution. It is "
            "also the discipline of leaving enough evidence for the next person, including your future self, to understand "
            "what happened and why."
        ),
    ),
    Passage(
        "P3",
        "family translation reflection",
        (
            "For many years I translated official letters for my grandmother at the kitchen table. The envelopes looked "
            "ordinary, but they often carried questions about appointments, insurance forms, or deadlines she did not "
            "want to miss. At first I treated translation as a simple exchange of words from one language into another. "
            "If a sentence said to bring identification, I repeated that instruction and moved on. Gradually I noticed "
            "that the harder part was not vocabulary. It was context. My grandmother wanted to know which details mattered, "
            "what would happen if a form was late, and whether a polite phrase was actually a warning. I began keeping a "
            "small list of terms, phone numbers, and questions to ask before appointments. That list became useful beyond "
            "our family. Neighbors started bringing similar letters, and I saw how easily a confusing sentence could turn "
            "into a missed service or an unnecessary fee. The work taught me patience, but it also taught me to respect "
            "precision. A translation that sounds fluent but hides uncertainty can be harmful. A good explanation admits "
            "what it does not know and points to the next step. That lesson now shapes the way I study, write, and help "
            "others navigate systems that seem simple only to people already inside them."
        ),
    ),
    Passage(
        "P4",
        "school newspaper reflection",
        (
            "When I joined the school newspaper, I expected to write opinion pieces about decisions everyone was already "
            "discussing in the hallway. My first assignment was less glamorous: interview cafeteria staff about a new "
            "breakfast program that most students ignored. I arrived with narrow questions and a paragraph almost drafted "
            "in my head. The interviews unsettled that plan. One staff member explained that breakfast participation rose "
            "when buses arrived early, another described students who picked up food for younger siblings, and a counselor "
            "showed me attendance records that made the program feel less like a convenience and more like quiet infrastructure. "
            "I rewrote the article three times. Each version became less about my opinion and more about the evidence people "
            "had trusted me to carry accurately. After publication, a teacher thanked us for explaining a policy she had "
            "misunderstood, and several students asked why the serving line closed before some late buses arrived. The article "
            "did not change the school by itself, but it changed my idea of writing. I began to see reporting as a form of "
            "careful listening, where the goal is not to sound certain as quickly as possible but to make the situation visible "
            "enough for better questions. That standard still challenges me whenever I am tempted to simplify a complicated "
            "story because the simpler version is easier to tell."
        ),
    ),
]


def count_words(text: str) -> int:
    return len(text.split())


def finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def sample_stdev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return statistics.stdev(values)


def coefficient_of_variation(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean_value = statistics.mean(values)
    if mean_value == 0:
        return None
    return statistics.stdev(values) / mean_value


def environment_info() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "device": "cpu",
    }


def calculate_perplexity_from_ids(
    input_ids: torch.Tensor,
    tokenizer: Any,
    model: Any,
    device: torch.device,
) -> dict[str, Any]:
    started = time.perf_counter()
    warnings: list[str] = []

    token_count = int(input_ids.shape[-1])
    usable_prediction_count = max(token_count - 1, 0)
    prefix_text = tokenizer.decode(input_ids[0], clean_up_tokenization_spaces=False)

    base_result: dict[str, Any] = {
        "char_count": len(prefix_text),
        "word_count": count_words(prefix_text),
        "token_count": token_count,
        "scored_token_count": usable_prediction_count,
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

    if prefix_text.strip() == "":
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

    input_ids = input_ids.to(device)
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


def prefix_ids(full_input_ids: torch.Tensor, target_token_count: int) -> torch.Tensor:
    actual_count = min(target_token_count, int(full_input_ids.shape[-1]))
    return full_input_ids[:, :actual_count].clone()


def run_prefix_repetitions(
    passage: Passage,
    target_token_count: int,
    prefix_input_ids: torch.Tensor,
    tokenizer: Any,
    model: Any,
    device: torch.device,
) -> dict[str, Any]:
    repeat_count = SHORT_REPEAT_COUNT if target_token_count <= 30 else 1
    runs = [
        calculate_perplexity_from_ids(prefix_input_ids, tokenizer, model, device)
        for _ in range(repeat_count)
    ]
    perplexities = [
        run["perplexity"]
        for run in runs
        if run.get("status") == "ok" and run.get("perplexity") is not None
    ]

    max_abs_diff = None
    effectively_identical = None
    if len(perplexities) >= 2:
        max_abs_diff = max(abs(value - perplexities[0]) for value in perplexities[1:])
        effectively_identical = max_abs_diff <= REPRO_TOLERANCE

    selected = runs[0]
    return {
        "passage_id": passage.passage_id,
        "passage_title": passage.title,
        "target_token_count": target_token_count,
        "actual_token_count": selected["token_count"],
        "scored_token_count": selected["scored_token_count"],
        "prefix_text": tokenizer.decode(prefix_input_ids[0], clean_up_tokenization_spaces=False),
        "repeat_count": repeat_count,
        "runs": runs,
        "selected_run": selected,
        "reproducibility": {
            "perplexities": perplexities,
            "max_absolute_difference": max_abs_diff,
            "tolerance": REPRO_TOLERANCE,
            "effectively_identical": effectively_identical,
        },
    }


def summarize_by_target(measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for target in TARGET_TOKEN_COUNTS:
        target_items = [
            item
            for item in measurements
            if item["target_token_count"] == target and item["selected_run"].get("status") == "ok"
        ]
        perplexities = [item["selected_run"]["perplexity"] for item in target_items]
        mean_nlls = [item["selected_run"]["mean_nll"] for item in target_items]
        scored_counts = [item["selected_run"]["scored_token_count"] for item in target_items]

        summaries.append(
            {
                "target_token_count": target,
                "passage_count": len(target_items),
                "actual_token_counts": [item["actual_token_count"] for item in target_items],
                "scored_token_counts": scored_counts,
                "perplexity_mean": statistics.mean(perplexities) if perplexities else None,
                "perplexity_median": statistics.median(perplexities) if perplexities else None,
                "perplexity_min": min(perplexities) if perplexities else None,
                "perplexity_max": max(perplexities) if perplexities else None,
                "perplexity_stdev": sample_stdev(perplexities),
                "perplexity_cv": coefficient_of_variation(perplexities),
                "mean_nll_mean": statistics.mean(mean_nlls) if mean_nlls else None,
                "mean_nll_stdev": sample_stdev(mean_nlls),
                "mean_nll_cv": coefficient_of_variation(mean_nlls),
            }
        )
    return summaries


def summarize_within_passage_drift(measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for passage in PASSAGES:
        items = [
            item
            for item in measurements
            if item["passage_id"] == passage.passage_id and item["selected_run"].get("status") == "ok"
        ]
        items.sort(key=lambda item: item["actual_token_count"])
        previous_ppl = None
        previous_count = None
        points = []
        for item in items:
            ppl = item["selected_run"]["perplexity"]
            delta = None if previous_ppl is None else ppl - previous_ppl
            relative_delta = None if previous_ppl in (None, 0) else delta / previous_ppl
            points.append(
                {
                    "target_token_count": item["target_token_count"],
                    "actual_token_count": item["actual_token_count"],
                    "perplexity": ppl,
                    "mean_nll": item["selected_run"]["mean_nll"],
                    "delta_from_previous": delta,
                    "relative_delta_from_previous": relative_delta,
                    "previous_actual_token_count": previous_count,
                }
            )
            previous_ppl = ppl
            previous_count = item["actual_token_count"]

        final_ppl = points[-1]["perplexity"] if points else None
        summaries.append(
            {
                "passage_id": passage.passage_id,
                "passage_title": passage.title,
                "points": points,
                "first_perplexity": points[0]["perplexity"] if points else None,
                "final_perplexity": final_ppl,
                "absolute_change_first_to_final": None if not points else final_ppl - points[0]["perplexity"],
                "relative_change_first_to_final": None
                if not points or points[0]["perplexity"] == 0
                else (final_ppl - points[0]["perplexity"]) / points[0]["perplexity"],
            }
        )
    return summaries


def summarize_reproducibility(measurements: list[dict[str, Any]]) -> dict[str, Any]:
    repeated = [
        item
        for item in measurements
        if item["repeat_count"] > 1 and item["selected_run"].get("status") == "ok"
    ]
    max_diffs = [
        item["reproducibility"]["max_absolute_difference"]
        for item in repeated
        if item["reproducibility"]["max_absolute_difference"] is not None
    ]
    return {
        "repeated_condition_count": len(repeated),
        "max_absolute_difference_observed": max(max_diffs) if max_diffs else None,
        "all_effectively_identical": all(
            item["reproducibility"]["effectively_identical"] is True for item in repeated
        )
        if repeated
        else None,
        "tolerance": REPRO_TOLERANCE,
    }


def summarize_performance(measurements: list[dict[str, Any]], load_time: float, total_time: float) -> dict[str, Any]:
    ok_runs = [
        run
        for item in measurements
        for run in item["runs"]
        if run.get("status") == "ok"
    ]
    inference_times = [run["inference_time_seconds"] for run in ok_runs]
    tokens_per_second = [
        run["tokens_per_second"]
        for run in ok_runs
        if run.get("tokens_per_second") is not None
    ]
    return {
        "model_load_time_seconds": load_time,
        "total_experiment_runtime_seconds": total_time,
        "successful_inference_run_count": len(ok_runs),
        "median_successful_inference_time_seconds": statistics.median(inference_times) if inference_times else None,
        "median_tokens_per_second": statistics.median(tokens_per_second) if tokens_per_second else None,
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
    full_passage_metadata = []
    for passage in PASSAGES:
        full_encoded = tokenizer(passage.text, return_tensors="pt", add_special_tokens=False)
        full_input_ids = full_encoded["input_ids"]
        full_token_count = int(full_input_ids.shape[-1])
        full_passage_metadata.append(
            {
                "passage_id": passage.passage_id,
                "title": passage.title,
                "char_count": len(passage.text),
                "word_count": count_words(passage.text),
                "token_count": full_token_count,
            }
        )

        for target in TARGET_TOKEN_COUNTS:
            ids = prefix_ids(full_input_ids, target)
            item = run_prefix_repetitions(passage, target, ids, tokenizer, model, device)
            measurements.append(item)
            selected = item["selected_run"]
            ppl = selected["perplexity"]
            ppl_text = f"{ppl:.6f}" if ppl is not None else "None"
            print(
                f"{passage.passage_id} target={target} actual={item['actual_token_count']} "
                f"scored={item['scored_token_count']} repeats={item['repeat_count']} "
                f"ppl={ppl_text} time_s={selected['inference_time_seconds']:.6f}"
            )

    total_time = time.perf_counter() - experiment_started
    output = {
        "experiment_id": EXPERIMENT_ID,
        "name": "Perplexity Stability by Text Length",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": {
            "identifier": MODEL_ID,
            "source": "Hugging Face Transformers",
            "execution_device": "cpu",
        },
        "environment": environment_info(),
        "method": {
            "target_token_counts": TARGET_TOKEN_COUNTS,
            "prefix_rule": "Each condition is the first N tokenizer tokens of the same underlying passage.",
            "short_repeat_count": SHORT_REPEAT_COUNT,
            "short_repeat_targets": [target for target in TARGET_TOKEN_COUNTS if target <= 30],
            "token_alignment": {
                "input_ids": "[t1, t2, t3, t4]",
                "shift_logits": "predictions for [t2, t3, t4]",
                "shift_labels": "[t2, t3, t4]",
                "excluded": "t1 has no preceding-token prediction inside the supplied sequence",
            },
            "calculation": "mean token negative log likelihood from shifted logits, then exp(mean NLL)",
            "reproducibility_tolerance": REPRO_TOLERANCE,
        },
        "passages": full_passage_metadata,
        "measurements": measurements,
        "summaries": {
            "by_target_token_count": summarize_by_target(measurements),
            "within_passage_drift": summarize_within_passage_drift(measurements),
            "reproducibility": summarize_reproducibility(measurements),
        },
        "performance": summarize_performance(measurements, load_time, total_time),
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"results_written={RESULTS_PATH}")
    print(f"total_experiment_runtime_seconds={total_time:.6f}")


if __name__ == "__main__":
    main()

