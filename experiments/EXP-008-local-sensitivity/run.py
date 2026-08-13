from __future__ import annotations

import copy
import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
EXP007_RUN = ROOT / "experiments" / "EXP-007-local-anomaly" / "run.py"
EXP007_RESULTS = (
    ROOT
    / "experiments"
    / "EXP-007-local-anomaly"
    / "results"
    / "results.json"
)

OUT_DIR = ROOT / "experiments" / "EXP-008-local-sensitivity"
RESULTS_PATH = OUT_DIR / "results" / "results.json"

WINDOW_SIZES = [1, 3, 5, 7]

FEATURE_CONFIGS = {
    "perplexity_only": ["perplexity"],
    "sentence_length_only": ["sentence_length"],
    "mattr_only": ["local_mattr"],
    "pos_3gram_entropy_only": ["local_pos_3gram_entropy"],
    "all_features": [
        "perplexity",
        "sentence_length",
        "local_mattr",
        "local_pos_3gram_entropy",
    ],
}


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

    idx = (len(ordered) - 1) * q
    lo = math.floor(idx)
    hi = math.ceil(idx)

    if lo == hi:
        return float(ordered[lo])

    frac = idx - lo
    return float(
        ordered[lo] + (ordered[hi] - ordered[lo]) * frac
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


def window_indices(
    index: int,
    sentence_count: int,
    window_size: int,
) -> list[int]:
    """
    Center the requested odd-sized window on the current sentence.

    At document edges, shift the window inward so that the requested
    size is preserved whenever enough sentences exist.
    """
    if sentence_count <= 1:
        return [0]

    actual_size = min(window_size, sentence_count)

    if actual_size % 2 == 0:
        raise ValueError(
            f"Window size must be odd, got {window_size}"
        )

    radius = actual_size // 2

    start = index - radius
    end = index + radius

    if start < 0:
        end -= start
        start = 0

    if end >= sentence_count:
        shift = end - sentence_count + 1
        start -= shift
        end -= shift

    start = max(0, start)
    end = min(sentence_count - 1, end)

    return list(range(start, end + 1))


def median_mad(values: list[float]) -> tuple[float, float]:
    median = statistics.median(values)
    deviations = [abs(v - median) for v in values]
    mad = statistics.median(deviations)
    return median, mad


def robust_z(
    value: Any,
    reference_values: list[float],
) -> float | None:
    if not finite(value) or not reference_values:
        return None

    median, mad = median_mad(reference_values)

    if mad == 0:
        return None

    return 0.6745 * (float(value) - median) / mad


def feature_value_from_exp007(
    sentence: dict[str, Any],
    feature_name: str,
) -> float | None:
    value = sentence["features"][feature_name]["value"]

    if finite(value):
        return float(value)

    return None


def recompute_window_features(
    sentence_item: dict[str, Any],
    hybrid: dict[str, Any],
    exp007: Any,
    exp004: Any,
    nlp: Any,
    window_size: int,
) -> dict[str, Any]:
    sentences = hybrid["sentences"]
    sentence_index = sentence_item["hybrid_index"]
    sentence_texts = [
        item["text"] for item in sentences
    ]

    indices = window_indices(
        sentence_index,
        len(sentences),
        window_size,
    )

    window_text = " ".join(
        sentence_texts[i] for i in indices
    )

    local = exp007.local_window_features(
        window_text,
        nlp,
        exp004,
    )

    return {
        "window_indices": indices,
        "window_size": len(indices),
        "local_mattr": local["local_mattr"]["value"],
        "local_pos_3gram_entropy": local[
            "local_pos_3gram_entropy"
        ]["value"],
        "local_meta": {
            "mattr": local["local_mattr"]["meta"],
            "pos_3gram_entropy": local[
                "local_pos_3gram_entropy"
            ]["meta"],
        },
    }


def evaluate_configuration(
    hybrid: dict[str, Any],
    window_size: int,
    feature_names: list[str],
    exp007: Any,
    exp004: Any,
    nlp: Any,
) -> dict[str, Any]:

    sentence_rows = copy.deepcopy(hybrid["sentences"])

    for row in sentence_rows:
        base_features = row["features"]

        # Existing sentence-level features from EXP-007.
        feature_values = {
            "perplexity": base_features["perplexity"]["value"],
            "sentence_length": base_features[
                "sentence_length"
            ]["value"],
        }

        # Recompute local features using the requested window.
        local = recompute_window_features(
            row,
            {"sentences": sentence_rows},
            exp007,
            exp004,
            nlp,
            window_size,
        )

        feature_values["local_mattr"] = local["local_mattr"]
        feature_values[
            "local_pos_3gram_entropy"
        ] = local["local_pos_3gram_entropy"]

        row["_sensitivity"] = {
            "window_indices": local["window_indices"],
            "window_size": local["window_size"],
            "feature_values": feature_values,
        }

    # Compute leave-one-out robust z-scores for each requested feature.
    for feature in feature_names:
        values = [
            row["_sensitivity"]["feature_values"][feature]
            for row in sentence_rows
        ]

        for i, row in enumerate(sentence_rows):
            ref = [
                float(v)
                for j, v in enumerate(values)
                if j != i and finite(v)
            ]

            z = robust_z(
                row["_sensitivity"]["feature_values"][feature],
                ref,
            )

            row.setdefault("_sensitivity_z", {})[feature] = z

    # Calculate configuration-specific anomaly score.
    for row in sentence_rows:
        z_values = []

        for feature in feature_names:
            z = row["_sensitivity_z"].get(feature)

            if finite(z):
                z_values.append(abs(float(z)))

        row["_sensitivity_anomaly"] = (
            statistics.mean(z_values)
            if z_values
            else None
        )

    finite_rows = [
        row
        for row in sentence_rows
        if finite(row["_sensitivity_anomaly"])
    ]

    ranked = sorted(
        finite_rows,
        key=lambda row: (
            -float(row["_sensitivity_anomaly"]),
            row["hybrid_index"],
        ),
    )

    rank_lookup = {
        row["hybrid_index"]: rank
        for rank, row in enumerate(ranked, start=1)
    }

    total_ranked = len(ranked)

    ai_reports = []

    for row in sentence_rows:
        score = row["_sensitivity_anomaly"]

        if not finite(score):
            continue

        rank = rank_lookup[row["hybrid_index"]]

        ai_reports.append(
            {
                "hybrid_index": row["hybrid_index"],
                "rank_descending": rank,
                "finite_rank_count": total_ranked,
                "anomaly_score": float(score),
                "is_ai_ground_truth": (
                    row["origin"] == "ai_inserted"
                ),
                "top_50_percent": (
                    rank <= math.ceil(total_ranked * 0.50)
                ),
                "top_25_percent": (
                    rank <= math.ceil(total_ranked * 0.25)
                ),
                "top_10_percent": (
                    rank <= math.ceil(total_ranked * 0.10)
                ),
            }
        )

    ai_scores = [
        r["anomaly_score"]
        for r in ai_reports
        if r["is_ai_ground_truth"]
    ]

    human_scores = [
        r["anomaly_score"]
        for r in ai_reports
        if not r["is_ai_ground_truth"]
    ]

    ai_ranked = [
        r for r in ai_reports
        if r["is_ai_ground_truth"]
    ]

    return {
        "window_size": window_size,
        "feature_set": feature_names,
        "ai_ground_truth_sentence_count": len(ai_ranked),
        "ai_anomaly_summary": summary(ai_scores),
        "human_anomaly_summary": summary(human_scores),
        "ai_minus_human_median": (
            None
            if not ai_scores or not human_scores
            else statistics.median(ai_scores)
            - statistics.median(human_scores)
        ),
        "top_50_capture": (
            sum(r["top_50_percent"] for r in ai_ranked)
            / len(ai_ranked)
            if ai_ranked
            else None
        ),
        "top_25_capture": (
            sum(r["top_25_percent"] for r in ai_ranked)
            / len(ai_ranked)
            if ai_ranked
            else None
        ),
        "top_10_capture": (
            sum(r["top_10_percent"] for r in ai_ranked)
            / len(ai_ranked)
            if ai_ranked
            else None
        ),
        "finite_ranked_sentence_count": total_ranked,
        "configuration_reports": ai_reports,
    }


def main() -> None:
    started = time.perf_counter()

    exp007 = load_module(
        EXP007_RUN,
        "exp007_run_for_exp008",
    )

    exp004 = exp007.load_module(
        exp007.EXP004_PATH,
        "exp004_run_for_exp008",
    )

    exp007_results = json.loads(
        EXP007_RESULTS.read_text(encoding="utf-8")
    )

    hybrids = exp007_results["hybrids"]

    if len(hybrids) != 20:
        raise RuntimeError(
            f"EXP-007 contains {len(hybrids)} hybrids; "
            "EXP-008 requires exactly 20."
        )

    nlp = __import__("spacy").load(
        exp004.SPACY_MODEL
    )

    results = []

    for window_size in WINDOW_SIZES:
        for feature_name, feature_list in FEATURE_CONFIGS.items():
            

            # The above was deliberately designed around one hybrid.
            # We aggregate across all 20 below.
            per_hybrid_results = [
                evaluate_configuration(
                    hybrid=hybrid,
                    window_size=window_size,
                    feature_names=feature_list,
                    exp007=exp007,
                    exp004=exp004,
                    nlp=nlp,
                )
                for hybrid in hybrids
            ]

            ai_scores = []
            human_scores = []
            ai_reports = []

            for item in per_hybrid_results:
                ai_summary = item["ai_anomaly_summary"]
                human_summary = item["human_anomaly_summary"]

                # Reconstruct aggregate score lists from reports.
                for report in item["configuration_reports"]:
                    if report["is_ai_ground_truth"]:
                        ai_scores.append(
                            report["anomaly_score"]
                        )
                        ai_reports.append(report)
                    else:
                        human_scores.append(
                            report["anomaly_score"]
                        )

            results.append(
                {
                    "window_size": window_size,
                    "window_name": (
                        f"{window_size}_sentence"
                    ),
                    "feature_set_name": feature_name,
                    "feature_set": feature_list,
                    "hybrid_count": len(hybrids),
                    "ai_ground_truth_sentence_count": len(
                        ai_reports
                    ),
                    "ai_anomaly_summary": summary(
                        ai_scores
                    ),
                    "human_anomaly_summary": summary(
                        human_scores
                    ),
                    "ai_minus_human_median": (
                        statistics.median(ai_scores)
                        - statistics.median(human_scores)
                        if ai_scores and human_scores
                        else None
                    ),
                    "top_50_capture": (
                        sum(
                            r["top_50_percent"]
                            for r in ai_reports
                        )
                        / len(ai_reports)
                        if ai_reports
                        else None
                    ),
                    "top_25_capture": (
                        sum(
                            r["top_25_percent"]
                            for r in ai_reports
                        )
                        / len(ai_reports)
                        if ai_reports
                        else None
                    ),
                    "top_10_capture": (
                        sum(
                            r["top_10_percent"]
                            for r in ai_reports
                        )
                        / len(ai_reports)
                        if ai_reports
                        else None
                    ),
                }
            )

    output = {
        "experiment_id": "EXP-008",
        "name": "Local Window & Feature Contribution Sensitivity",
        "source_experiment": "EXP-007",
        "hybrid_count": len(hybrids),
        "ground_truth_ai_sentences": len(hybrids) * 2,
        "window_sizes": WINDOW_SIZES,
        "feature_configurations": FEATURE_CONFIGS,
        "results": results,
        "validation": {
            "hybrid_count_ok": len(hybrids) == 20,
            "ground_truth_sentence_count_ok": (
                len(hybrids) * 2 == 40
            ),
            "configuration_count_ok": (
                len(results)
                == len(WINDOW_SIZES)
                * len(FEATURE_CONFIGS)
            ),
        },
        "timing_seconds": time.perf_counter() - started,
    }

    output["validation"]["all_passed"] = all(
        output["validation"].values()
    )

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_PATH.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "experiment_id": "EXP-008",
                "configuration_count": len(results),
                "validation": output["validation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()