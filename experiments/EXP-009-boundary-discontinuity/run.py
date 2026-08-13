from __future__ import annotations

import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

EXP007_RESULTS = (
    ROOT
    / "experiments"
    / "EXP-007-local-anomaly"
    / "results"
    / "results.json"
)

OUT_DIR = ROOT / "experiments" / "EXP-009-boundary-discontinuity"
RESULTS_PATH = OUT_DIR / "results" / "results.json"

PAIR_COUNT = 20


def load_module(path: Path, name: str) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)

    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def quantile_linear(values: list[float], q: float) -> float | None:
    if not values:
        return None

    ordered = sorted(values)

    if len(ordered) == 1:
        return float(ordered[0])

    index = (len(ordered) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)

    if low == high:
        return float(ordered[low])

    fraction = index - low

    return float(
        ordered[low]
        + (ordered[high] - ordered[low]) * fraction
    )


def summary(values: list[float]) -> dict[str, Any]:
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

    q1 = quantile_linear(values, 0.25)
    q3 = quantile_linear(values, 0.75)

    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": (
            statistics.stdev(values)
            if len(values) >= 2
            else None
        ),
        "iqr": (
            None
            if q1 is None or q3 is None
            else q3 - q1
        ),
        "q1": q1,
        "q3": q3,
        "min": min(values),
        "max": max(values),
    }


def robust_z(
    value: float | None,
    reference_values: list[float],
) -> float | None:
    if value is None or not finite(value):
        return None

    if not reference_values:
        return None

    median = statistics.median(reference_values)
    deviations = [
        abs(item - median)
        for item in reference_values
    ]
    mad = statistics.median(deviations)

    if mad == 0:
        return None

    return (
        0.6745
        * (value - median)
        / mad
    )


def safe_log(value: Any) -> float | None:
    if not finite(value):
        return None

    if float(value) <= 0:
        return None

    return math.log(float(value))


def build_boundary_features(
    sentences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundaries: list[dict[str, Any]] = []

    for left_index in range(len(sentences) - 1):
        right_index = left_index + 1

        left = sentences[left_index]
        right = sentences[right_index]

        left_features = left["features"]
        right_features = right["features"]

        left_ppl = left_features["perplexity"]["value"]
        right_ppl = right_features["perplexity"]["value"]

        left_length = left_features["sentence_length"]["value"]
        right_length = right_features["sentence_length"]["value"]

        left_mattr = left_features["local_mattr"]["value"]
        right_mattr = right_features["local_mattr"]["value"]

        left_pos = left_features[
            "local_pos_3gram_entropy"
        ]["value"]
        right_pos = right_features[
            "local_pos_3gram_entropy"
        ]["value"]

        left_log_ppl = safe_log(left_ppl)
        right_log_ppl = safe_log(right_ppl)

        raw_ppl_change = (
            None
            if left_ppl is None or right_ppl is None
            else abs(
                float(right_ppl)
                - float(left_ppl)
            )
        )

        log_ppl_change = (
            None
            if left_log_ppl is None or right_log_ppl is None
            else abs(
                right_log_ppl
                - left_log_ppl
            )
        )

        length_change = (
            None
            if left_length is None
            or right_length is None
            else abs(
                float(right_length)
                - float(left_length)
            )
        )

        mattr_change = (
            None
            if left_mattr is None
            or right_mattr is None
            else abs(
                float(right_mattr)
                - float(left_mattr)
            )
        )

        pos_change = (
            None
            if left_pos is None or right_pos is None
            else abs(
                float(right_pos)
                - float(left_pos)
            )
        )

        boundaries.append(
            {
                "boundary_index": left_index,
                "left_sentence_index": left_index,
                "right_sentence_index": right_index,
                "left_origin": left["origin"],
                "right_origin": right["origin"],
                "boundary_type": (
                    f"{left['origin']}__TO__{right['origin']}"
                ),
                "target_boundary": (
                    left["origin"] == "human"
                    and right["origin"] == "ai_inserted"
                )
                or (
                    left["origin"] == "ai_inserted"
                    and right["origin"] == "human"
                ),
                "human_to_ai_boundary": (
                    left["origin"] == "human"
                    and right["origin"] == "ai_inserted"
                ),
                "ai_to_human_boundary": (
                    left["origin"] == "ai_inserted"
                    and right["origin"] == "human"
                ),
                "ai_internal_boundary": (
                    left["origin"] == "ai_inserted"
                    and right["origin"] == "ai_inserted"
                ),
                "human_internal_boundary": (
                    left["origin"] == "human"
                    and right["origin"] == "human"
                ),
                "features": {
                    "raw_perplexity_change": raw_ppl_change,
                    "log_perplexity_change": log_ppl_change,
                    "sentence_length_change": length_change,
                    "mattr_change": mattr_change,
                    "pos_3gram_entropy_change": pos_change,
                },
            }
        )

    return boundaries


def add_robust_scores(
    boundaries: list[dict[str, Any]],
) -> None:
    feature_names = [
        "log_perplexity_change",
        "sentence_length_change",
        "mattr_change",
        "pos_3gram_entropy_change",
    ]

    for feature_name in feature_names:
        values = [
            boundary["features"][feature_name]
            for boundary in boundaries
            if finite(boundary["features"][feature_name])
        ]

        for boundary in boundaries:
            current = boundary["features"][feature_name]

            references = [
                float(other["features"][feature_name])
                for other in boundaries
                if other is not boundary
                and finite(other["features"][feature_name])
            ]

            z = robust_z(current, references)

            boundary.setdefault(
                "robust_z",
                {},
            )[feature_name] = z

    for boundary in boundaries:
        z_values = [
            abs(float(value))
            for value in boundary["robust_z"].values()
            if finite(value)
        ]

        boundary["boundary_score"] = (
            statistics.mean(z_values)
            if z_values
            else None
        )


def rank_boundaries(
    boundaries: list[dict[str, Any]],
) -> None:
    ranked = [
        boundary
        for boundary in boundaries
        if finite(boundary["boundary_score"])
    ]

    ranked.sort(
        key=lambda item: (
            -float(item["boundary_score"]),
            item["boundary_index"],
        )
    )

    for rank, boundary in enumerate(
        ranked,
        start=1,
    ):
        boundary["rank_descending"] = rank
        boundary["finite_rank_count"] = len(ranked)

        boundary["top_50_percent"] = (
            rank <= math.ceil(len(ranked) * 0.50)
        )
        boundary["top_25_percent"] = (
            rank <= math.ceil(len(ranked) * 0.25)
        )
        boundary["top_10_percent"] = (
            rank <= math.ceil(len(ranked) * 0.10)
        )

    ranked_indices = {
        item["boundary_index"]
        for item in ranked
    }

    for boundary in boundaries:
        if boundary["boundary_index"] not in ranked_indices:
            boundary["rank_descending"] = None
            boundary["finite_rank_count"] = len(ranked)
            boundary["top_50_percent"] = False
            boundary["top_25_percent"] = False
            boundary["top_10_percent"] = False


def evaluate_hybrid(
    hybrid: dict[str, Any],
) -> dict[str, Any]:
    boundaries = build_boundary_features(
        hybrid["sentences"]
    )

    add_robust_scores(boundaries)
    rank_boundaries(boundaries)

    target_boundaries = [
        item
        for item in boundaries
        if item["target_boundary"]
    ]

    human_internal = [
        item
        for item in boundaries
        if item["human_internal_boundary"]
    ]

    ai_internal = [
        item
        for item in boundaries
        if item["ai_internal_boundary"]
    ]

    target_scores = [
        float(item["boundary_score"])
        for item in target_boundaries
        if finite(item["boundary_score"])
    ]

    human_internal_scores = [
        float(item["boundary_score"])
        for item in human_internal
        if finite(item["boundary_score"])
    ]

    ai_internal_scores = [
        float(item["boundary_score"])
        for item in ai_internal
        if finite(item["boundary_score"])
    ]

    return {
        "pair_id": hybrid["pair_id"],
        "row_index": hybrid["row_index"],
        "ground_truth_ai_sentence_indices": hybrid[
            "ground_truth_ai_hybrid_sentence_indices"
        ],
        "boundaries": boundaries,
        "evaluation": {
            "target_boundary_count": len(target_boundaries),
            "target_boundary_score_summary": summary(
                target_scores
            ),
            "human_internal_boundary_score_summary": summary(
                human_internal_scores
            ),
            "ai_internal_boundary_score_summary": summary(
                ai_internal_scores
            ),
            "target_minus_human_internal_median": (
                None
                if not target_scores
                or not human_internal_scores
                else (
                    statistics.median(target_scores)
                    - statistics.median(
                        human_internal_scores
                    )
                )
            ),
            "target_boundary_ranks": [
                {
                    "boundary_index": item["boundary_index"],
                    "boundary_type": item["boundary_type"],
                    "score": item["boundary_score"],
                    "rank_descending": item[
                        "rank_descending"
                    ],
                    "finite_rank_count": item[
                        "finite_rank_count"
                    ],
                    "top_50_percent": item[
                        "top_50_percent"
                    ],
                    "top_25_percent": item[
                        "top_25_percent"
                    ],
                    "top_10_percent": item[
                        "top_10_percent"
                    ],
                }
                for item in target_boundaries
            ],
        },
    }


def main() -> None:
    started = time.perf_counter()

    if not EXP007_RESULTS.exists():
        raise FileNotFoundError(
            f"Missing EXP-007 results: {EXP007_RESULTS}"
        )

    exp007 = json.loads(
        EXP007_RESULTS.read_text(
            encoding="utf-8"
        )
    )

    hybrids = exp007["hybrids"]

    if len(hybrids) != PAIR_COUNT:
        raise RuntimeError(
            f"Expected {PAIR_COUNT} hybrids, "
            f"found {len(hybrids)}."
        )

    evaluated = [
        evaluate_hybrid(hybrid)
        for hybrid in hybrids
    ]

    all_target_scores: list[float] = []
    all_human_internal_scores: list[float] = []
    all_ai_internal_scores: list[float] = []

    target_boundary_reports: list[dict[str, Any]] = []

    for hybrid in evaluated:
        evaluation = hybrid["evaluation"]

        all_target_scores.extend(
            float(item["boundary_score"])
            for item in hybrid["boundaries"]
            if item["target_boundary"]
            and finite(item["boundary_score"])
        )

        all_human_internal_scores.extend(
            float(item["boundary_score"])
            for item in hybrid["boundaries"]
            if item["human_internal_boundary"]
            and finite(item["boundary_score"])
        )

        all_ai_internal_scores.extend(
            float(item["boundary_score"])
            for item in hybrid["boundaries"]
            if item["ai_internal_boundary"]
            and finite(item["boundary_score"])
        )

        target_boundary_reports.extend(
            evaluation["target_boundary_ranks"]
        )

    target_count = len(target_boundary_reports)

    output = {
        "experiment_id": "EXP-009",
        "name": "Boundary Discontinuity Feasibility",
        "source_experiment": "EXP-007",
        "hybrid_count": len(hybrids),
        "ground_truth_target_boundaries": target_count,
        "feature_changes": [
            "raw_perplexity_change",
            "log_perplexity_change",
            "sentence_length_change",
            "mattr_change",
            "pos_3gram_entropy_change",
        ],
        "primary_score": (
            "mean absolute robust z-score across "
            "log_perplexity_change, sentence_length_change, "
            "mattr_change, and pos_3gram_entropy_change"
        ),
        "target_boundary_summary": summary(
            all_target_scores
        ),
        "human_internal_boundary_summary": summary(
            all_human_internal_scores
        ),
        "ai_internal_boundary_summary": summary(
            all_ai_internal_scores
        ),
        "target_minus_human_internal_median": (
            None
            if not all_target_scores
            or not all_human_internal_scores
            else (
                statistics.median(all_target_scores)
                - statistics.median(
                    all_human_internal_scores
                )
            )
        ),
        "capture": {
            "top_50_percent": (
                sum(
                    bool(item["top_50_percent"])
                    for item in target_boundary_reports
                )
                / target_count
                if target_count
                else None
            ),
            "top_25_percent": (
                sum(
                    bool(item["top_25_percent"])
                    for item in target_boundary_reports
                )
                / target_count
                if target_count
                else None
            ),
            "top_10_percent": (
                sum(
                    bool(item["top_10_percent"])
                    for item in target_boundary_reports
                )
                / target_count
                if target_count
                else None
            ),
        },
        "target_boundary_ranks": target_boundary_reports,
        "hybrid_results": evaluated,
        "validation": {
            "hybrid_count_ok": len(hybrids) == 20,
            "two_target_boundaries_per_hybrid": all(
                len(
                    item["evaluation"][
                        "target_boundary_ranks"
                    ]
                ) == 2
                for item in evaluated
            ),
            "no_duplicate_pair_ids": (
                len(
                    {
                        item["pair_id"]
                        for item in evaluated
                    }
                )
                == len(evaluated)
            ),
        },
        "timing_seconds": (
            time.perf_counter() - started
        ),
    }

    output["validation"]["all_passed"] = all(
        output["validation"].values()
    )

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_PATH.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "experiment_id": "EXP-009",
                "hybrid_count": len(hybrids),
                "target_boundaries": target_count,
                "validation": output["validation"],
                "capture": output["capture"],
                "target_minus_human_internal_median": output[
                    "target_minus_human_internal_median"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()