from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.app.paths import EXP001_RUN_PATH, EXP004_RUN_PATH


def _load_module(module_path: Path, module_name: str) -> Any:
    if not module_path.exists():
        raise FileNotFoundError(f"Validated experiment module not found: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_exp001_module() -> Any:
    module = _load_module(EXP001_RUN_PATH, "production_exp001_run")
    if not hasattr(module, "calculate_perplexity"):
        raise RuntimeError("EXP-001 module does not expose calculate_perplexity.")
    return module


@lru_cache(maxsize=1)
def load_exp004_module() -> Any:
    module = _load_module(EXP004_RUN_PATH, "production_exp004_run")
    required = [
        "MODEL_ID",
        "SPACY_MODEL",
        "MATTR_WINDOW",
        "tokenize_for_lexical_features",
        "sentence_length_cv",
        "mattr",
        "pos_trigram_entropy",
    ]
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        raise RuntimeError(f"EXP-004 module missing required symbols: {missing}")
    return module
