from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

from backend.app.features.extraction import FEATURE_ORDER
from backend.app.paths import DEFAULT_MODEL_ARTIFACT_PATH, DEFAULT_MODEL_METADATA_PATH


@dataclass(frozen=True)
class ModelPrediction:
    label: str
    numeric_label: int
    ai_probability: float


@dataclass(frozen=True)
class LoadedModelArtifact:
    scaler: Any
    classifier: Any
    metadata: dict[str, Any]

    def score(self, feature_values: Mapping[str, float]) -> ModelPrediction:
        row = pd.DataFrame(
            [[float(feature_values[name]) for name in FEATURE_ORDER]],
            columns=FEATURE_ORDER,
        )
        scaled = self.scaler.transform(row)
        ai_probability = float(self.classifier.predict_proba(scaled)[0, 1])
        numeric_label = int(self.classifier.predict(scaled)[0])
        label = "ai_associated" if numeric_label == 1 else "human_associated"
        return ModelPrediction(
            label=label,
            numeric_label=numeric_label,
            ai_probability=ai_probability,
        )


def _load_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Model metadata not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_model_artifact(
    artifact_path: Path = DEFAULT_MODEL_ARTIFACT_PATH,
    metadata_path: Path = DEFAULT_MODEL_METADATA_PATH,
) -> LoadedModelArtifact:
    if not artifact_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {artifact_path}")

    payload = joblib.load(artifact_path)
    if not isinstance(payload, dict):
        raise ValueError("Model artifact payload must be a dictionary.")

    feature_order = payload.get("feature_order")
    if feature_order != FEATURE_ORDER:
        raise ValueError(f"Unexpected artifact feature order: {feature_order}")

    scaler = payload.get("scaler")
    classifier = payload.get("classifier")
    if scaler is None or classifier is None:
        raise ValueError("Model artifact must contain scaler and classifier.")

    metadata = _load_metadata(metadata_path)
    if metadata.get("feature_order") != FEATURE_ORDER:
        raise ValueError(f"Unexpected metadata feature order: {metadata.get('feature_order')}")

    return LoadedModelArtifact(scaler=scaler, classifier=classifier, metadata=metadata)


@lru_cache(maxsize=1)
def get_default_model_artifact() -> LoadedModelArtifact:
    return load_model_artifact()
