from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class AnalyzeRequest(BaseModel):
    text: StrictStr = Field(..., description="Raw essay text to analyze.")


class FeatureEvidence(BaseModel):
    name: Literal["perplexity", "sentence_length_cv", "mattr", "pos_3gram_entropy"]
    value: float | None
    available: bool
    reason: str | None
    metadata: dict[str, Any]


class TextStatistics(BaseModel):
    char_count: int
    word_count: int
    sentence_count: int
    lexical_token_count: int
    spacy_token_count: int
    language_model_token_count: int | None


class SentenceEvidence(BaseModel):
    sentence_id: int
    text: str
    perplexity: float | None
    available: bool
    reason: str | None
    

class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    state: Literal["insufficient_evidence", "classified"]
    label: Literal["human_associated", "ai_associated"] | None
    ai_probability: float | None
    features: list[FeatureEvidence]
    sentence_evidence: list[SentenceEvidence]
    text_statistics: TextStatistics
    model_metadata: dict[str, Any]


