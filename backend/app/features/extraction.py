from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Callable

from backend.app.features.experiment_reuse import load_exp001_module, load_exp004_module
from backend.app.features.resources import load_language_model_resources, load_spacy_model


FEATURE_ORDER = [
    "perplexity",
    "sentence_length_cv",
    "mattr",
    "pos_3gram_entropy",
]


@dataclass(frozen=True)
class FeatureMeasurement:
    name: str
    value: float | None
    available: bool
    reason: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class TextStatistics:
    char_count: int
    word_count: int
    sentence_count: int
    lexical_token_count: int
    spacy_token_count: int
    language_model_token_count: int | None


@dataclass(frozen=True)
class FeatureExtractionResult:
    features: dict[str, FeatureMeasurement]
    sentence_texts: list[str]
    text_statistics: TextStatistics

    def feature_vector(self) -> dict[str, float] | None:
        values: dict[str, float] = {}
        for name in FEATURE_ORDER:
            measurement = self.features[name]
            if not measurement.available or measurement.value is None:
                return None
            values[name] = measurement.value
        return values


PerplexityCalculator = Callable[[str, Any, Any, Any], dict[str, Any]]


def _finite_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _availability_from_meta(name: str, value: Any, meta: dict[str, Any]) -> FeatureMeasurement:
    finite_value = _finite_or_none(value)
    available = bool(meta.get("available")) and finite_value is not None
    reason = None if available else str(meta.get("reason") or f"{name}_unavailable")
    return FeatureMeasurement(
        name=name,
        value=finite_value if available else None,
        available=available,
        reason=reason,
        metadata=dict(meta),
    )


class ProductionFeatureExtractor:
    """Production wrapper around the validated EXP-001/EXP-004 feature math."""

    def __init__(
        self,
        nlp: Any | None = None,
        tokenizer: Any | None = None,
        model: Any | None = None,
        device: Any | None = None,
        perplexity_calculator: PerplexityCalculator | None = None,
    ) -> None:
        self._nlp = nlp
        self._tokenizer = tokenizer
        self._model = model
        self._device = device
        self._perplexity_calculator = perplexity_calculator

    @property
    def nlp(self) -> Any:
        if self._nlp is None:
            self._nlp = load_spacy_model()
        return self._nlp

    def _lm_resources(self) -> tuple[Any, Any, Any]:
        if self._tokenizer is None or self._model is None or self._device is None:
            self._tokenizer, self._model, self._device = load_language_model_resources()
        return self._tokenizer, self._model, self._device

    @property
    def perplexity_calculator(self) -> PerplexityCalculator:
        if self._perplexity_calculator is None:
            self._perplexity_calculator = load_exp001_module().calculate_perplexity
        return self._perplexity_calculator

    def extract(self, text: str) -> FeatureExtractionResult:
        exp004 = load_exp004_module()
        doc = self.nlp(text)
        sentence_texts = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

        sentence_lengths_for_cv: list[int] = []
        sentence_perplexities: list[float] = []
        perplexity_status_counts: dict[str, int] = {}
        perplexity_unavailable_reasons: dict[str, int] = {}
        sentence_rows: list[dict[str, Any]] = []

        tokenizer, model, device = self._lm_resources()
        for idx, sentence_text in enumerate(sentence_texts, start=1):
            ppl_result = self.perplexity_calculator(sentence_text, tokenizer, model, device)
            status = str(ppl_result.get("status"))
            perplexity_status_counts[status] = perplexity_status_counts.get(status, 0) + 1

            perplexity_value = _finite_or_none(ppl_result.get("perplexity"))
            if status == "ok" and perplexity_value is not None:
                sentence_perplexities.append(perplexity_value)
            else:
                reason = str(ppl_result.get("reason") or status or "unknown")
                perplexity_unavailable_reasons[reason] = perplexity_unavailable_reasons.get(reason, 0) + 1

            sent_doc = self.nlp.make_doc(sentence_text)
            length_for_cv = len([tok for tok in sent_doc if not tok.is_space and not tok.is_punct])
            sentence_lengths_for_cv.append(length_for_cv)
            sentence_rows.append(
                {
                    "sentence_id": idx,
                    "token_count": ppl_result.get("token_count"),
                    "usable_prediction_token_count": ppl_result.get("usable_prediction_token_count"),
                    "perplexity": perplexity_value,
                    "perplexity_status": status,
                    "perplexity_reason_unavailable": ppl_result.get("reason"),
                    "perplexity_warnings": list(ppl_result.get("warnings", [])),
                }
            )

        if sentence_perplexities:
            perplexity = FeatureMeasurement(
                name="perplexity",
                value=float(statistics.median(sentence_perplexities)),
                available=True,
                reason=None,
                metadata={
                    "available": True,
                    "reason": None,
                    "sentence_count": len(sentence_texts),
                    "valid_sentence_perplexity_count": len(sentence_perplexities),
                    "sentence_perplexity_aggregation": "median_of_valid_sentence_perplexities",
                    "status_counts": perplexity_status_counts,
                    "sentence_measurements": sentence_rows,
                    "source_experiment": "EXP-001",
                    "causal_shift_alignment": "input_ids[:, 1:] labels scored by logits[:, :-1, :]",
                },
            )
        else:
            perplexity = FeatureMeasurement(
                name="perplexity",
                value=None,
                available=False,
                reason="no_valid_sentence_perplexity_values",
                metadata={
                    "available": False,
                    "reason": "no_valid_sentence_perplexity_values",
                    "sentence_count": len(sentence_texts),
                    "valid_sentence_perplexity_count": 0,
                    "status_counts": perplexity_status_counts,
                    "unavailable_reason_counts": perplexity_unavailable_reasons,
                    "sentence_measurements": sentence_rows,
                    "source_experiment": "EXP-001",
                },
            )

        cv_value, cv_meta = exp004.sentence_length_cv(sentence_lengths_for_cv)
        lexical_tokens = exp004.tokenize_for_lexical_features(doc)
        mattr_value, mattr_meta = exp004.mattr(lexical_tokens, exp004.MATTR_WINDOW)
        pos_value, pos_meta = exp004.pos_trigram_entropy(doc)

        language_model_token_count = None
        if self._tokenizer is not None:
            encoded = self._tokenizer(text, return_tensors="pt", add_special_tokens=False)
            language_model_token_count = int(encoded["input_ids"].shape[-1])

        features = {
            "perplexity": perplexity,
            "sentence_length_cv": _availability_from_meta("sentence_length_cv", cv_value, cv_meta),
            "mattr": _availability_from_meta("mattr", mattr_value, mattr_meta),
            "pos_3gram_entropy": _availability_from_meta("pos_3gram_entropy", pos_value, pos_meta),
        }

        stats = TextStatistics(
            char_count=len(text),
            word_count=len(text.split()),
            sentence_count=len(sentence_texts),
            lexical_token_count=len(lexical_tokens),
            spacy_token_count=len([tok for tok in doc if not tok.is_space]),
            language_model_token_count=language_model_token_count,
        )
        return FeatureExtractionResult(
            features=features,
            sentence_texts=sentence_texts,
            text_statistics=stats,
        )
