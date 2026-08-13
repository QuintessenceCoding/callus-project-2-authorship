from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends

from backend.app.detector.engine import AuthorshipDetector
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse


router = APIRouter()


@lru_cache(maxsize=1)
def get_detector() -> AuthorshipDetector:
    return AuthorshipDetector()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: AnalyzeRequest,
    detector: AuthorshipDetector = Depends(get_detector),
) -> AnalyzeResponse:
    return AnalyzeResponse.model_validate(detector.analyze(request.text).__dict__)
