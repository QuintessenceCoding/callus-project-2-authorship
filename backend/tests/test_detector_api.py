from __future__ import annotations

import math
from typing import Any

import pytest

from backend.app.detector.engine import AuthorshipDetector
from backend.app.detector.model_artifact import ModelPrediction, load_model_artifact
from backend.app.features.extraction import (
    FEATURE_ORDER,
    FeatureExtractionResult,
    FeatureMeasurement,
    ProductionFeatureExtractor,
    TextStatistics,
)
from backend.app.features.experiment_reuse import load_exp004_module


class FakeArtifact:
    metadata = {
        "artifact_version": "test-artifact",
        "feature_order": FEATURE_ORDER,
        "source_experiment": "EXP-006",
    }

    def score(self, feature_values: dict[str, float]) -> ModelPrediction:
        return ModelPrediction(
            label="ai_associated",
            numeric_label=1,
            ai_probability=0.75,
        )


class RaisingExtractor:
    def extract(self, text: str) -> FeatureExtractionResult:
        raise AssertionError("feature extractor should not be called for invalid input")


class StaticExtractor:
    def __init__(self, result: FeatureExtractionResult) -> None:
        self.result = result

    def extract(self, text: str) -> FeatureExtractionResult:
        return self.result


class FakeTokenIds:
    def __init__(self, token_count: int) -> None:
        self.shape = (1, token_count)


class FakeTokenizer:
    def __call__(self, text: str, return_tensors: str, add_special_tokens: bool) -> dict[str, Any]:
        return {"input_ids": FakeTokenIds(max(len(text.split()), 0))}


def measurement(name: str, value: float | None, reason: str | None = None) -> FeatureMeasurement:
    available = value is not None
    return FeatureMeasurement(
        name=name,
        value=value,
        available=available,
        reason=None if available else reason or f"{name}_unavailable",
        metadata={"available": available, "reason": None if available else reason},
    )


def extraction_result(
    features: dict[str, FeatureMeasurement] | None = None,
    sentence_count: int = 3,
) -> FeatureExtractionResult:
    feature_map = features or {
        "perplexity": measurement("perplexity", 42.0),
        "sentence_length_cv": measurement("sentence_length_cv", 0.25),
        "mattr": measurement("mattr", 0.9),
        "pos_3gram_entropy": measurement("pos_3gram_entropy", 5.0),
    }
    return FeatureExtractionResult(
        features=feature_map,
        sentence_texts=["One.", "Two.", "Three."][:sentence_count],
        text_statistics=TextStatistics(
            char_count=120,
            word_count=24,
            sentence_count=sentence_count,
            lexical_token_count=24,
            spacy_token_count=27,
            language_model_token_count=30,
        ),
    )


def test_empty_input_returns_insufficient_evidence() -> None:
    detector = AuthorshipDetector(feature_extractor=RaisingExtractor(), model_artifact=FakeArtifact())
    result = detector.analyze("")
    assert result.state == "insufficient_evidence"
    assert result.label is None
    assert result.ai_probability is None
    assert all(feature["available"] is False for feature in result.features)
    assert {feature["reason"] for feature in result.features} == {"empty_input"}


def test_whitespace_only_input_returns_insufficient_evidence() -> None:
    detector = AuthorshipDetector(feature_extractor=RaisingExtractor(), model_artifact=FakeArtifact())
    result = detector.analyze("   \n\t  ")
    assert result.state == "insufficient_evidence"
    assert result.label is None
    assert {feature["reason"] for feature in result.features} == {"whitespace_only_input"}


def test_very_short_input_with_unavailable_required_feature_abstains() -> None:
    features = {
        "perplexity": measurement("perplexity", None, "no_valid_sentence_perplexity_values"),
        "sentence_length_cv": measurement("sentence_length_cv", None, "insufficient_sentences_for_cv: require_at_least=2"),
        "mattr": measurement("mattr", None, "insufficient_tokens_for_window: have=1 require_at_least=25"),
        "pos_3gram_entropy": measurement("pos_3gram_entropy", None, "insufficient_pos_tags_for_3grams: have=1 require_at_least=3"),
    }
    detector = AuthorshipDetector(
        feature_extractor=StaticExtractor(extraction_result(features, sentence_count=1)),
        model_artifact=FakeArtifact(),
    )
    result = detector.analyze("Hi.")
    assert result.state == "insufficient_evidence"
    assert result.ai_probability is None
    assert [feature["name"] for feature in result.features] == FEATURE_ORDER
    assert all(feature["value"] is None for feature in result.features)


def test_normal_multi_sentence_input_classifies_when_all_features_available() -> None:
    detector = AuthorshipDetector(
        feature_extractor=StaticExtractor(extraction_result()),
        model_artifact=FakeArtifact(),
    )
    result = detector.analyze("One sentence. Another sentence. A final sentence.")
    assert result.state == "classified"
    assert result.label == "ai_associated"
    assert result.ai_probability == 0.75
    assert all(feature["available"] is True for feature in result.features)


def test_exact_feature_ordering() -> None:
    assert FEATURE_ORDER == [
        "perplexity",
        "sentence_length_cv",
        "mattr",
        "pos_3gram_entropy",
    ]
    assert [feature["name"] for feature in AuthorshipDetector(
        feature_extractor=StaticExtractor(extraction_result()),
        model_artifact=FakeArtifact(),
    ).analyze("Enough text. Enough text again. Enough text finally.").features] == FEATURE_ORDER


def test_production_feature_definitions_match_exp004_for_non_lm_features() -> None:
    exp004 = load_exp004_module()
    nlp = __import__("spacy").load(exp004.SPACY_MODEL)

    def fake_perplexity(sentence: str, tokenizer: Any, model: Any, device: Any) -> dict[str, Any]:
        return {
            "status": "ok",
            "perplexity": float(len(sentence) + 1),
            "token_count": len(sentence.split()),
            "usable_prediction_token_count": max(len(sentence.split()) - 1, 0),
            "warnings": [],
        }

    text = (
        "I learned to listen before solving the problem. "
        "The habit changed how our team wrote, tested, and revised every plan. "
        "By spring we had built a routine that other students could maintain."
    )
    extractor = ProductionFeatureExtractor(
        nlp=nlp,
        tokenizer=FakeTokenizer(),
        model=object(),
        device=object(),
        perplexity_calculator=fake_perplexity,
    )
    result = extractor.extract(text)
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    lengths = [
        len([tok for tok in nlp.make_doc(sentence) if not tok.is_space and not tok.is_punct])
        for sentence in sentences
    ]
    cv_value, _ = exp004.sentence_length_cv(lengths)
    lexical_tokens = exp004.tokenize_for_lexical_features(doc)
    mattr_value, _ = exp004.mattr(lexical_tokens, exp004.MATTR_WINDOW)
    pos_value, _ = exp004.pos_trigram_entropy(doc)

    assert result.sentence_texts == sentences
    assert math.isclose(result.features["sentence_length_cv"].value or 0.0, cv_value)
    assert math.isclose(result.features["mattr"].value or 0.0, mattr_value)
    assert math.isclose(result.features["pos_3gram_entropy"].value or 0.0, pos_value)
    assert result.features["perplexity"].metadata["sentence_perplexity_aggregation"] == "median_of_valid_sentence_perplexities"


def test_model_artifact_loading() -> None:
    artifact = load_model_artifact()
    assert artifact.metadata["feature_order"] == FEATURE_ORDER
    assert artifact.metadata["model_type"]["scaler"] == "StandardScaler"
    assert artifact.metadata["model_type"]["classifier"] == "LogisticRegression"


def test_deterministic_repeated_inference_with_saved_artifact() -> None:
    artifact = load_model_artifact()
    verification = artifact.metadata["known_validation_row_verification"]
    extractor = StaticExtractor(
        extraction_result(
            {
                name: measurement(name, float(value))
                for name, value in verification["feature_values"].items()
            }
        )
    )
    detector = AuthorshipDetector(feature_extractor=extractor, model_artifact=artifact)
    first = detector.analyze("Stable input. Stable input again. Stable input finally.")
    second = detector.analyze("Stable input. Stable input again. Stable input finally.")
    assert first.state == "classified"
    assert second.state == "classified"
    assert first.label == second.label
    assert first.ai_probability == second.ai_probability


def test_known_validation_row_prediction_using_saved_model_artifact() -> None:
    artifact = load_model_artifact()
    verification = artifact.metadata["known_validation_row_verification"]
    prediction = artifact.score(verification["feature_values"])
    assert prediction.numeric_label == verification["expected_prediction"]
    assert prediction.label == "human_associated"
    assert prediction.ai_probability == pytest.approx(verification["expected_ai_probability"], abs=1e-12)
    assert verification["matches_exp010_row"] is True


def test_api_request_validation_and_response_serialization() -> None:
    from fastapi.testclient import TestClient

    from backend.app.api.analyze import get_detector
    from backend.app.main import app

    detector = AuthorshipDetector(
        feature_extractor=StaticExtractor(extraction_result()),
        model_artifact=FakeArtifact(),
    )
    app.dependency_overrides[get_detector] = lambda: detector
    try:
        client = TestClient(app)
        invalid = client.post("/api/analyze", json={})
        assert invalid.status_code == 422

        response = client.post("/api/analyze", json={"text": "One. Two. Three."})
        assert response.status_code == 200
        payload = response.json()
        assert payload["state"] == "classified"
        assert payload["label"] == "ai_associated"
        assert payload["ai_probability"] == 0.75
        assert [feature["name"] for feature in payload["features"]] == FEATURE_ORDER
        assert payload["text_statistics"]["sentence_count"] == 3
        assert payload["model_metadata"]["feature_order"] == FEATURE_ORDER
    finally:
        app.dependency_overrides.clear()
