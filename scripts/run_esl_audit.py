from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.detector.engine import AuthorshipDetector
from backend.app.detector.model_artifact import load_model_artifact
from backend.app.features.extraction import ProductionFeatureExtractor


DATASET_PATH = Path(
    "data/raw/persuade/persuade2_train_srctexts.csv"
)

MANIFEST_PATH = Path(
    "data/esl_audit_manifest.json"
)

OUTPUT_DIR = Path(
    "data/esl_audit"
)

PREDICTIONS_PATH = OUTPUT_DIR / "predictions.csv"
METRICS_PATH = OUTPUT_DIR / "metrics.json"


def reconstruct_essays() -> dict[str, dict[str, Any]]:
    """
    Reconstruct one essay per essay_id_comp from the discourse-level
    PERSUADE CSV.

    discourse rows are ordered using discourse_start. Duplicate essay-level
    metadata are taken from the first row for that essay.
    """
    essays: dict[str, dict[str, Any]] = {}

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            essay_id = str(row["essay_id_comp"])
            discourse_text = row.get("discourse_text") or ""
            discourse_start_raw = row.get("discourse_start")

            try:
                discourse_start = int(
                    discourse_start_raw
                )
            except (
                TypeError,
                ValueError,
            ):
                discourse_start = 10**12

            if essay_id not in essays:
                essays[essay_id] = {
                    "essay_id": essay_id,
                    "ell_status": row.get("ell_status"),
                    "task": row.get("task"),
                    "segments": [],
                }

            essays[essay_id]["segments"].append(
                (
                    discourse_start,
                    discourse_text,
                )
            )

    for essay in essays.values():
        essay["segments"].sort(
            key=lambda item: item[0]
        )

        parts = [
            text.strip()
            for _, text in essay["segments"]
            if text and text.strip()
        ]

        essay["text"] = " ".join(parts)

    return essays


def mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.fmean(values)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return sorted_values[0]

    index = (len(sorted_values) - 1) * q
    lower = int(index)
    upper = min(
        lower + 1,
        len(sorted_values) - 1,
    )

    if lower == upper:
        return sorted_values[lower]

    fraction = index - lower

    return (
        sorted_values[lower]
        + fraction
        * (
            sorted_values[upper]
            - sorted_values[lower]
        )
    )


def feature_value(
    result: Any,
    name: str,
) -> float | None:
    for feature in result.features:
        if feature["name"] == name:
            value = feature["value"]

            if value is None:
                return None

            return float(value)

    return None


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        manifest = json.load(handle)

    essays = reconstruct_essays()

    ell_ids = set(
        manifest["ell_ids"]
    )

    non_ell_ids = set(
        manifest["non_ell_ids"]
    )

    audit_ids = ell_ids | non_ell_ids

    missing_ids = [
        essay_id
        for essay_id in audit_ids
        if essay_id not in essays
    ]

    if missing_ids:
        raise RuntimeError(
            "Manifest contains essay IDs missing from "
            f"the dataset: {missing_ids[:10]}"
        )

    print(
        "Loading locked production model..."
    )

    extractor = ProductionFeatureExtractor()
    artifact = load_model_artifact()

    detector = AuthorshipDetector(
        feature_extractor=extractor,
        model_artifact=artifact,
    )

    ordered_ids = sorted(audit_ids)

    predictions: list[dict[str, Any]] = []

    total = len(ordered_ids)

    for index, essay_id in enumerate(
        ordered_ids,
        start=1,
    ):
        essay = essays[essay_id]

        group = (
            "ELL"
            if essay_id in ell_ids
            else "non_ELL"
        )

        text = essay["text"]

        print(
            f"[{index}/{total}] "
            f"group={group} "
            f"essay={essay_id}"
        )

        if not text.strip():
            raise RuntimeError(
                f"Essay {essay_id} reconstructed to empty text."
            )

        result = detector.analyze(text)

        predicted_label = None

        if result.label == "human_associated":
            predicted_label = 0

        elif result.label == "ai_associated":
            predicted_label = 1

        row = {
            "essay_id": essay_id,
            "group": group,
            "ell_status": essay["ell_status"],
            "task": essay["task"],
            "state": result.state,
            "predicted_label": predicted_label,
            "predicted_label_name": result.label,
            "ai_probability": result.ai_probability,
            "word_count": len(text.split()),
            "sentence_count": (
                result.text_statistics.get(
                    "sentence_count"
                )
            ),
            "perplexity": feature_value(
                result,
                "perplexity",
            ),
            "sentence_length_cv": feature_value(
                result,
                "sentence_length_cv",
            ),
            "mattr": feature_value(
                result,
                "mattr",
            ),
            "pos_3gram_entropy": feature_value(
                result,
                "pos_3gram_entropy",
            ),
        }

        predictions.append(row)

    def group_summary(
        group_name: str,
    ) -> dict[str, Any]:
        group_rows = [
            row
            for row in predictions
            if row["group"] == group_name
        ]

        classified = [
            row
            for row in group_rows
            if row["predicted_label"] is not None
        ]

        abstained = [
            row
            for row in group_rows
            if row["predicted_label"] is None
        ]

        ai_flagged = [
            row
            for row in classified
            if row["predicted_label"] == 1
        ]

        human_classified = [
            row
            for row in classified
            if row["predicted_label"] == 0
        ]

        probabilities = [
            float(row["ai_probability"])
            for row in classified
            if row["ai_probability"] is not None
        ]

        return {
            "sample_count": len(group_rows),
            "classified": len(classified),
            "abstained": len(abstained),
            "coverage": (
                len(classified)
                / len(group_rows)
                if group_rows
                else None
            ),
            "flagged_ai_count": len(
                ai_flagged
            ),
            "classified_human_count": len(
                human_classified
            ),
            "false_positive_rate": (
                len(ai_flagged)
                / len(classified)
                if classified
                else None
            ),
            "model_signal_mean": mean_or_none(
                probabilities
            ),
            "model_signal_median": (
                statistics.median(probabilities)
                if probabilities
                else None
            ),
            "model_signal_p10": percentile(
                probabilities,
                0.10,
            ),
            "model_signal_p90": percentile(
                probabilities,
                0.90,
            ),
        }

    metrics = {
        "audit_name": manifest[
            "audit_name"
        ],
        "manifest": str(MANIFEST_PATH),
        "seed": manifest["seed"],
        "total_essays": len(
            predictions
        ),
        "model_artifact_version": artifact.metadata.get(
            "artifact_version"
        ),
        "source_experiment": artifact.metadata.get(
            "source_experiment"
        ),
        "groups": {
            "ELL": group_summary("ELL"),
            "non_ELL": group_summary(
                "non_ELL"
            ),
        },
    }

    with PREDICTIONS_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        fieldnames = list(
            predictions[0].keys()
        )

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(predictions)

    with METRICS_PATH.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            metrics,
            handle,
            indent=2,
        )

    print("\n=== ESL / NON-NATIVE-ENGLISH AUDIT ===")
    print(
        json.dumps(
            metrics,
            indent=2,
        )
    )

    print("\nArtifacts:")
    print(PREDICTIONS_PATH)
    print(METRICS_PATH)


if __name__ == "__main__":
    main()