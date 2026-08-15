from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from backend.app.detector.model_artifact import (
    LoadedModelArtifact,
    get_default_model_artifact,
)
from backend.app.features.extraction import (
    FEATURE_ORDER,
    ProductionFeatureExtractor,
)


@dataclass(frozen=True)
class DetectorResult:
    state: str
    label: str | None
    ai_probability: float | None
    features: list[dict[str, Any]]
    sentence_evidence: list[dict[str, Any]]
    text_statistics: dict[str, Any]
    model_metadata: dict[str, Any]


class AuthorshipDetector:
    def __init__(
        self,
        feature_extractor: ProductionFeatureExtractor | None = None,
        model_artifact: LoadedModelArtifact | None = None,
    ) -> None:
        self.feature_extractor = (
            feature_extractor
            or ProductionFeatureExtractor()
        )
        self.model_artifact = model_artifact

    def _model(self) -> LoadedModelArtifact:
        if self.model_artifact is None:
            self.model_artifact = (
                get_default_model_artifact()
            )
        return self.model_artifact

    @staticmethod
    def _sentence_evidence(
        extraction: Any,
    ) -> list[dict[str, Any]]:
        """
        Expose the sentence-level perplexity measurements
        already produced by the production feature extractor.

        This is evidence presentation data only. It does not
        classify individual sentences as human- or AI-written.
        """
        perplexity_measurement = extraction.features[
            "perplexity"
        ]

        sentence_measurements = (
            perplexity_measurement.metadata.get(
                "sentence_measurements",
                [],
            )
        )

        sentence_texts = extraction.sentence_texts

        evidence: list[dict[str, Any]] = []

        for index, sentence_text in enumerate(
            sentence_texts,
            start=1,
        ):
            measurement = (
                sentence_measurements[index - 1]
                if index - 1 < len(sentence_measurements)
                else {}
            )

            perplexity = measurement.get(
                "perplexity"
            )

            available = (
                isinstance(
                    perplexity,
                    (int, float),
                )
                and not isinstance(
                    perplexity,
                    bool,
                )
                and math.isfinite(
                    float(perplexity)
                )
            )

            evidence.append(
                {
                    "sentence_id": index,
                    "text": sentence_text,
                    "perplexity": (
                        float(perplexity)
                        if available
                        else None
                    ),
                    "available": available,
                    "reason": (
                        None
                        if available
                        else measurement.get(
                            "perplexity_reason_unavailable"
                        )
                        or measurement.get(
                            "reason"
                        )
                        or "perplexity_unavailable"
                    ),
                }
            )

        return evidence

    def analyze(self, text: str) -> DetectorResult:
        base_stats = {
            "char_count": len(text),
            "word_count": len(text.split()),
            "sentence_count": 0,
            "lexical_token_count": 0,
            "spacy_token_count": 0,
            "language_model_token_count": None,
        }

        if text == "":
            return self._insufficient(
                "empty_input",
                base_stats,
            )

        if text.strip() == "":
            return self._insufficient(
                "whitespace_only_input",
                base_stats,
            )

        extraction = self.feature_extractor.extract(
            text
        )

        feature_vector = (
            extraction.feature_vector()
        )

        stats = (
            extraction.text_statistics.__dict__
        )

        features = [
            {
                "name": name,
                "value": extraction.features[
                    name
                ].value,
                "available": extraction.features[
                    name
                ].available,
                "reason": extraction.features[
                    name
                ].reason,
                "metadata": extraction.features[
                    name
                ].metadata,
            }
            for name in FEATURE_ORDER
        ]

        sentence_evidence = (
            self._sentence_evidence(
                extraction
            )
        )

        if feature_vector is None:
            return DetectorResult(
                state="insufficient_evidence",
                label=None,
                ai_probability=None,
                features=features,
                sentence_evidence=(
                    sentence_evidence
                ),
                text_statistics=stats,
                model_metadata=(
                    self._public_metadata()
                ),
            )

        prediction = self._model().score(
            feature_vector
        )

        return DetectorResult(
            state="classified",
            label=prediction.label,
            ai_probability=(
                prediction.ai_probability
            ),
            features=features,
            sentence_evidence=(
                sentence_evidence
            ),
            text_statistics=stats,
            model_metadata=(
                self._public_metadata()
            ),
        )

    def _insufficient(
        self,
        reason: str,
        stats: dict[str, Any],
    ) -> DetectorResult:
        features = [
            {
                "name": name,
                "value": None,
                "available": False,
                "reason": reason,
                "metadata": {
                    "available": False,
                    "reason": reason,
                },
            }
            for name in FEATURE_ORDER
        ]

        return DetectorResult(
            state="insufficient_evidence",
            label=None,
            ai_probability=None,
            features=features,
            sentence_evidence=[],
            text_statistics=stats,
            model_metadata=(
                self._public_metadata()
            ),
        )

    def _public_metadata(self) -> dict[str, Any]:
        if self.model_artifact is None:
            try:
                return (
                    get_default_model_artifact()
                    .metadata
                )
            except FileNotFoundError:
                return {
                    "artifact_available": False,
                    "feature_order": FEATURE_ORDER,
                    "source_experiment": "EXP-006",
                }

        return self.model_artifact.metadata