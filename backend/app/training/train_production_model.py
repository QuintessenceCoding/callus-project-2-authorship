from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from backend.app.features.extraction import FEATURE_ORDER
from backend.app.paths import (
    ARTIFACT_DIR,
    DEFAULT_MODEL_ARTIFACT_PATH,
    DEFAULT_MODEL_METADATA_PATH,
    EXP005_RESULTS_PATH,
    EXP006_RESULTS_PATH,
    EXP010_RESULTS_PATH,
)


SEED = 20260814
VALIDATION_TEST_SIZE = 0.20


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def load_feature_rows() -> pd.DataFrame:
    exp005 = _load_json(EXP005_RESULTS_PATH)
    rows: list[dict[str, Any]] = []
    for pair in exp005["pair_results"]:
        pair_id = str(pair["id"])
        for label, role in [(0, "human"), (1, "ai")]:
            feature_block = pair[role]["features"]
            row: dict[str, Any] = {"pair_id": pair_id, "label": label}
            for feature in FEATURE_ORDER:
                row[feature] = feature_block[feature]["value"]
            rows.append(row)
    return pd.DataFrame(rows)


def train_model() -> tuple[dict[str, Any], dict[str, Any]]:
    df = load_feature_rows()
    rows_before = len(df)
    complete = df.dropna(subset=FEATURE_ORDER).copy()
    dropped_rows = rows_before - len(complete)

    pair_ids = complete["pair_id"].drop_duplicates().tolist()
    train_pairs, validation_pairs = train_test_split(
        pair_ids,
        test_size=VALIDATION_TEST_SIZE,
        random_state=SEED,
    )
    train_pairs = set(train_pairs)
    validation_pairs = set(validation_pairs)
    train_df = complete[complete["pair_id"].isin(train_pairs)].copy()
    validation_df = complete[complete["pair_id"].isin(validation_pairs)].copy()

    if not train_pairs.isdisjoint(validation_pairs):
        raise RuntimeError("Pair-aware split failed; train/validation overlap detected.")
    if set(train_df["label"]) != {0, 1} or set(validation_df["label"]) != {0, 1}:
        raise RuntimeError("Both classes must be present in train and validation splits.")

    scaler = StandardScaler()
    classifier = LogisticRegression(random_state=SEED, max_iter=1000)
    train_x = train_df[FEATURE_ORDER]
    scaler.fit(train_x)
    classifier.fit(scaler.transform(train_x), train_df["label"])

    payload = {
        "feature_order": FEATURE_ORDER,
        "scaler": scaler,
        "classifier": classifier,
    }

    exp006 = _load_json(EXP006_RESULTS_PATH)
    exp010 = _load_json(EXP010_RESULTS_PATH)
    verification = build_known_validation_verification(payload, validation_df, exp010)

    metadata = {
        "artifact_version": "production-four-feature-logreg-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_order": FEATURE_ORDER,
        "model_type": {
            "scaler": "StandardScaler",
            "classifier": "LogisticRegression",
        },
        "random_seed": SEED,
        "configuration": {
            "classifier": {
                "random_state": SEED,
                "max_iter": 1000,
            },
            "scaler": "StandardScaler()",
            "development_split": {
                "pair_aware": True,
                "test_size": VALIDATION_TEST_SIZE,
                "random_state": SEED,
            },
        },
        "source_experiment": "EXP-006",
        "feature_definition_source": "EXP-004",
        "training_source": str(EXP005_RESULTS_PATH),
        "rows_before_feature_filter": rows_before,
        "rows_dropped_for_missing_features": dropped_rows,
        "training_pair_count": len(train_pairs),
        "training_row_count": len(train_df),
        "validation_pair_count": len(validation_pairs),
        "validation_row_count": len(validation_df),
        "reference_validation_metrics": exp006["models"]["all_features"]["metrics"],
        "known_validation_row_verification": verification,
        "sklearn_version": sklearn.__version__,
        "interpretation_guardrail": (
            "Classifier probabilities are model scores for machine association within the "
            "EXP-005/EXP-006 distribution, not calibrated authorship certainty."
        ),
    }
    return payload, metadata


def _score_payload(payload: dict[str, Any], row: pd.DataFrame) -> tuple[int, float]:
    scaled = payload["scaler"].transform(row[FEATURE_ORDER])
    probability = float(payload["classifier"].predict_proba(scaled)[0, 1])
    prediction = int(payload["classifier"].predict(scaled)[0])
    return prediction, probability


def build_known_validation_verification(
    payload: dict[str, Any],
    validation_df: pd.DataFrame,
    exp010: dict[str, Any],
) -> dict[str, Any]:
    row_info = exp010["row_level_validation_predictions"][0]
    pair_id = str(row_info["pair_id"])
    label = int(row_info["label"])
    row = validation_df[(validation_df["pair_id"] == pair_id) & (validation_df["label"] == label)]
    if len(row) != 1:
        raise RuntimeError(f"Known validation row not found once in split: pair_id={pair_id} label={label}")

    prediction, probability = _score_payload(payload, row)
    expected_probability = float(row_info["ai_probability"])
    expected_prediction = int(row_info["prediction"])
    return {
        "pair_id": pair_id,
        "label": label,
        "feature_values": {
            feature: float(row.iloc[0][feature])
            for feature in FEATURE_ORDER
            if _finite(row.iloc[0][feature])
        },
        "expected_prediction": expected_prediction,
        "observed_prediction": prediction,
        "expected_ai_probability": expected_probability,
        "observed_ai_probability": probability,
        "absolute_probability_delta": abs(probability - expected_probability),
        "matches_exp010_row": prediction == expected_prediction and abs(probability - expected_probability) <= 1e-12,
    }


def persist(
    artifact_path: Path = DEFAULT_MODEL_ARTIFACT_PATH,
    metadata_path: Path = DEFAULT_MODEL_METADATA_PATH,
) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    payload, metadata = train_model()
    joblib.dump(payload, artifact_path)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {
        "artifact_path": str(artifact_path),
        "metadata_path": str(metadata_path),
        "verification": metadata["known_validation_row_verification"],
    }


def main() -> None:
    print(json.dumps(persist(), indent=2))


if __name__ == "__main__":
    main()
