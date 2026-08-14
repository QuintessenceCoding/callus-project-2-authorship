from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.detector.engine import AuthorshipDetector


ROOT = Path(__file__).resolve().parents[2]

EXP007_RESULTS = (
    ROOT
    / "experiments"
    / "EXP-007-local-anomaly"
    / "results"
    / "results.json"
)

OUT = (
    ROOT
    / "experiments"
    / "EXP-011-passage-attribution"
    / "results"
    / "results.json"
)


def finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def rank_descending(items: list[dict]) -> list[dict]:
    ranked = [
        item
        for item in items
        if finite(item.get("contribution"))
    ]

    ranked.sort(
        key=lambda item: (
            -float(item["contribution"]),
            item["sentence_index"],
        )
    )

    for rank, item in enumerate(
        ranked,
        start=1,
    ):
        item["rank"] = rank

    return ranked


def evaluate_hybrid(
    hybrid: dict,
    detector: AuthorshipDetector,
) -> dict:

    sentences = [
        sentence["text"]
        for sentence in hybrid["sentences"]
    ]

    full_text = " ".join(sentences)

    full_result = detector.analyze(full_text)

    full_probability = full_result.ai_probability

    if full_result.state != "classified":
        return {
            "pair_id": hybrid["pair_id"],
            "status": "full_document_not_classified",
            "full_state": full_result.state,
            "full_probability": full_probability,
            "sentences": [],
            "ground_truth_ai_sentence_indices": (
                hybrid[
                    "ground_truth_ai_hybrid_sentence_indices"
                ]
            ),
        }

    sentence_results = []

    for index, sentence in enumerate(
        sentences
    ):
        remaining = (
            sentences[:index]
            + sentences[index + 1:]
        )

        reduced_text = " ".join(remaining)

        reduced_result = detector.analyze(
            reduced_text
        )

        if reduced_result.state != "classified":
            contribution = None
            reason = (
                "reduced_document_not_classified"
            )
        else:
            contribution = (
                float(full_probability)
                - float(reduced_result.ai_probability)
            )
            reason = None

        sentence_results.append(
            {
                "sentence_index": index,
                "text": sentence,
                "origin": hybrid["sentences"][
                    index
                ]["origin"],
                "is_ground_truth_ai": (
                    index
                    in hybrid[
                        "ground_truth_ai_hybrid_sentence_indices"
                    ]
                ),
                "reduced_state": (
                    reduced_result.state
                ),
                "reduced_probability": (
                    reduced_result.ai_probability
                ),
                "contribution": contribution,
                "reason": reason,
            }
        )

    ranked = rank_descending(
        sentence_results
    )

    total = len(ranked)

    for item in sentence_results:
        item["top_10_percent"] = (
            item.get("rank") is not None
            and item["rank"]
            <= max(1, math.ceil(total * 0.10))
        )
        item["top_25_percent"] = (
            item.get("rank") is not None
            and item["rank"]
            <= max(1, math.ceil(total * 0.25))
        )

    ai_items = [
        item
        for item in sentence_results
        if item["is_ground_truth_ai"]
    ]

    human_items = [
        item
        for item in sentence_results
        if not item["is_ground_truth_ai"]
    ]

    ai_contributions = [
        float(item["contribution"])
        for item in ai_items
        if finite(item["contribution"])
    ]

    human_contributions = [
        float(item["contribution"])
        for item in human_items
        if finite(item["contribution"])
    ]

    return {
        "pair_id": hybrid["pair_id"],
        "status": "ok",
        "full_state": full_result.state,
        "full_probability": full_probability,
        "sentence_count": len(sentence_results),
        "ground_truth_ai_sentence_indices": (
            hybrid[
                "ground_truth_ai_hybrid_sentence_indices"
            ]
        ),
        "sentences": sentence_results,
        "evaluation": {
            "ai_contribution_median": (
                statistics.median(ai_contributions)
                if ai_contributions
                else None
            ),
            "human_contribution_median": (
                statistics.median(human_contributions)
                if human_contributions
                else None
            ),
            "ai_minus_human_median": (
                None
                if not ai_contributions
                or not human_contributions
                else (
                    statistics.median(
                        ai_contributions
                    )
                    - statistics.median(
                        human_contributions
                    )
                )
            ),
            "ai_top_10_percent_capture": (
                sum(
                    item["top_10_percent"]
                    for item in ai_items
                )
                / len(ai_items)
                if ai_items
                else None
            ),
            "ai_top_25_percent_capture": (
                sum(
                    item["top_25_percent"]
                    for item in ai_items
                )
                / len(ai_items)
                if ai_items
                else None
            ),
        },
    }


def main() -> None:
    exp007 = load_json(
        EXP007_RESULTS
    )

    hybrids = exp007.get("hybrids", [])

    if len(hybrids) != 20:
        raise RuntimeError(
            f"Expected 20 hybrids, found {len(hybrids)}."
        )

    detector = AuthorshipDetector()

    results = [
        evaluate_hybrid(
            hybrid,
            detector,
        )
        for hybrid in hybrids
    ]

    usable = [
        item
        for item in results
        if item["status"] == "ok"
    ]

    ai_capture_10 = [
        item["evaluation"][
            "ai_top_10_percent_capture"
        ]
        for item in usable
        if item["evaluation"][
            "ai_top_10_percent_capture"
        ]
        is not None
    ]

    ai_capture_25 = [
        item["evaluation"][
            "ai_top_25_percent_capture"
        ]
        for item in usable
        if item["evaluation"][
            "ai_top_25_percent_capture"
        ]
        is not None
    ]

    ai_medians = [
        item["evaluation"][
            "ai_contribution_median"
        ]
        for item in usable
        if item["evaluation"][
            "ai_contribution_median"
        ]
        is not None
    ]

    human_medians = [
        item["evaluation"][
            "human_contribution_median"
        ]
        for item in usable
        if item["evaluation"][
            "human_contribution_median"
        ]
        is not None
    ]

    output = {
        "experiment_id": "EXP-011",
        "name": "Passage Attribution Feasibility",
        "method": (
            "Leave-one-sentence-out contribution using "
            "the production four-feature Logistic Regression."
        ),
        "source_experiment": "EXP-007",
        "hybrid_count": len(hybrids),
        "usable_hybrids": len(usable),
        "capture": {
            "top_10_percent_mean": (
                statistics.mean(ai_capture_10)
                if ai_capture_10
                else None
            ),
            "top_25_percent_mean": (
                statistics.mean(ai_capture_25)
                if ai_capture_25
                else None
            ),
        },
        "contribution": {
            "ai_sentence_median": (
                statistics.median(ai_medians)
                if ai_medians
                else None
            ),
            "human_sentence_median": (
                statistics.median(human_medians)
                if human_medians
                else None
            ),
            "ai_minus_human_median": (
                None
                if not ai_medians
                or not human_medians
                else (
                    statistics.median(ai_medians)
                    - statistics.median(human_medians)
                )
            ),
        },
        "hybrids": results,
        "interpretation_guardrail": (
            "A positive sentence contribution means "
            "removing that sentence lowers the model's "
            "machine-associated score. It is evidence "
            "contribution, not proof of AI authorship."
        ),
        "validation": {
            "hybrid_count_ok": len(hybrids) == 20,
            "unique_pair_ids": (
                len(
                    {
                        hybrid["pair_id"]
                        for hybrid in hybrids
                    }
                )
                == len(hybrids)
            ),
            "usable_results_present": len(usable) > 0,
        },
    }

    output["validation"]["all_passed"] = all(
        output["validation"].values()
    )

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUT.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "experiment_id": "EXP-011",
                "hybrid_count": len(hybrids),
                "usable_hybrids": len(usable),
                "capture": output["capture"],
                "contribution": output["contribution"],
                "validation": output["validation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()