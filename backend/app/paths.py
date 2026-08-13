from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
ARTIFACT_DIR = BACKEND_DIR / "artifacts"

DEFAULT_MODEL_ARTIFACT_PATH = ARTIFACT_DIR / "authorship_detector.joblib"
DEFAULT_MODEL_METADATA_PATH = ARTIFACT_DIR / "authorship_detector.metadata.json"

EXP001_RUN_PATH = ROOT / "experiments" / "EXP-001-perplexity-feasibility" / "run.py"
EXP004_RUN_PATH = ROOT / "experiments" / "EXP-004-feature-extraction" / "run.py"
EXP005_RESULTS_PATH = ROOT / "experiments" / "EXP-005-feature-distribution" / "results" / "results.json"
EXP006_RESULTS_PATH = ROOT / "experiments" / "EXP-006-baseline-classification" / "results" / "results.json"
EXP010_RESULTS_PATH = ROOT / "experiments" / "EXP-010-evidence-sufficiency" / "results" / "results.json"
