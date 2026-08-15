from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from backend.app.detector.engine import AuthorshipDetector
from backend.app.detector.model_artifact import load_model_artifact
from backend.app.features.extraction import ProductionFeatureExtractor


DATASET_PATH = Path(
    "data/raw/daigt_external/daigt_external_dataset.csv"
)
MANIFEST_PATH = Path(
    "data/final_evaluation_manifest.json"
)
OUTPUT_DIR = Path(
    "data/final_evaluation"
)

PREDICTIONS_PATH = OUTPUT_DIR / "predictions.csv"
METRICS_PATH = OUTPUT_DIR / "metrics.json"


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

    selected_ids = set(
        manifest["selected_pair_ids"]
    )

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    selected_rows = [
        row
        for row in rows
        if row["id"] in selected_ids
    ]

    if len(selected_rows) != manifest["final_pair_count"]:
        raise RuntimeError(
            "Frozen manifest does not match the expected "
            f"pair count: expected {manifest['final_pair_count']}, "
            f"found {len(selected_rows)}."
        )

    print(
        f"Loading production model and feature extractor..."
    )

    extractor = ProductionFeatureExtractor(
        perplexity_calculator=None,
    )

    artifact = load_model_artifact()

    detector = AuthorshipDetector(
        feature_extractor=extractor,
        model_artifact=artifact,
    )

    predictions: list[dict[str, Any]] = []

    total = len(selected_rows) * 2
    completed = 0

    for row in selected_rows:
        pair_id = row["id"]

        cases = [
            (
                "human",
                0,
                row["text"],
            ),
            (
                "ai",
                1,
                row["source_text"],
            ),
        ]

        for expected_type, expected_label, text in cases:
            completed += 1

            print(
                f"[{completed}/{total}] "
                f"pair={pair_id} "
                f"type={expected_type}"
            )

            result = detector.analyze(text)

            prediction_label = None

            if result.label == "human_associated":
                prediction_label = 0
            elif result.label == "ai_associated":
                prediction_label = 1

            predictions.append(
                {
                    "pair_id": pair_id,
                    "expected_type": expected_type,
                    "expected_label": expected_label,
                    "predicted_label": prediction_label,
                    "predicted_label_name": result.label,
                    "state": result.state,
                    "ai_probability": result.ai_probability,
                    "word_count": len(text.split()),
                    "char_count": len(text),
                    "sentence_count": (
                        result.text_statistics.get(
                            "sentence_count"
                        )
                    ),
                    "perplexity": (
                        next(
                            (
                                feature["value"]
                                for feature in result.features
                                if feature["name"] == "perplexity"
                            ),
                            None,
                        )
                    ),
                    "sentence_length_cv": (
                        next(
                            (
                                feature["value"]
                                for feature in result.features
                                if feature["name"]
                                == "sentence_length_cv"
                            ),
                            None,
                        )
                    ),
                    "mattr": (
                        next(
                            (
                                feature["value"]
                                for feature in result.features
                                if feature["name"] == "mattr"
                            ),
                            None,
                        )
                    ),
                    "pos_3gram_entropy": (
                        next(
                            (
                                feature["value"]
                                for feature in result.features
                                if feature["name"]
                                == "pos_3gram_entropy"
                            ),
                            None,
                        )
                    ),
                }
            )

    classified = [
        item
        for item in predictions
        if item["predicted_label"] is not None
    ]

    abstained = [
        item
        for item in predictions
        if item["predicted_label"] is None
    ]

    if not classified:
        raise RuntimeError(
            "No classified samples were produced."
        )

    y_true = [
        item["expected_label"]
        for item in classified
    ]

    y_pred = [
        item["predicted_label"]
        for item in classified
    ]

    probabilities = [
        item["ai_probability"]
        for item in classified
        if item["ai_probability"] is not None
    ]

    probability_labels = [
        item["expected_label"]
        for item in classified
        if item["ai_probability"] is not None
    ]

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    tn, fp, fn, tp = (
        int(cm[0][0]),
        int(cm[0][1]),
        int(cm[1][0]),
        int(cm[1][1]),
    )

    fpr = (
        fp / (fp + tn)
        if (fp + tn)
        else None
    )

    fnr = (
        fn / (fn + tp)
        if (fn + tp)
        else None
    )

    coverage = (
        len(classified) / len(predictions)
    )

    metrics: dict[str, Any] = {
        "evaluation_name": manifest[
            "evaluation_name"
        ],
        "manifest": str(MANIFEST_PATH),
        "dataset_sha256": manifest[
            "dataset_sha256"
        ],
        "final_pair_count": manifest[
            "final_pair_count"
        ],
        "total_inputs": len(predictions),
        "classified_inputs": len(classified),
        "abstained_inputs": len(abstained),
        "coverage": coverage,
        "accuracy": accuracy_score(
            y_true,
            y_pred,
        ),
        "precision": precision_score(
            y_true,
            y_pred,
            zero_division=0,
        ),
        "recall": recall_score(
            y_true,
            y_pred,
            zero_division=0,
        ),
        "f1": f1_score(
            y_true,
            y_pred,
            zero_division=0,
        ),
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "confusion_matrix": [
            [
                tn,
                fp,
            ],
            [
                fn,
                tp,
            ],
        ],
        "probability_samples": len(
            probabilities
        ),
        "roc_auc": (
            roc_auc_score(
                probability_labels,
                probabilities,
            )
            if len(set(probability_labels)) == 2
            else None
        ),
        "model_artifact_version": artifact.metadata.get(
            "artifact_version"
        ),
        "source_experiment": artifact.metadata.get(
            "source_experiment"
        ),
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

    print("\n=== FINAL EVALUATION ===")
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