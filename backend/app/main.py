from __future__ import annotations

from fastapi import FastAPI

from backend.app.api.analyze import router as analyze_router


app = FastAPI(title="Callus Authorship Detector API")
app.include_router(analyze_router, prefix="/api")
