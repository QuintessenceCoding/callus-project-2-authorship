from __future__ import annotations

from functools import lru_cache
from typing import Any

import spacy
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from backend.app.features.experiment_reuse import load_exp004_module


@lru_cache(maxsize=1)
def load_spacy_model() -> Any:
    exp004 = load_exp004_module()
    return spacy.load(exp004.SPACY_MODEL)


@lru_cache(maxsize=1)
def load_language_model_resources() -> tuple[Any, Any, torch.device]:
    exp004 = load_exp004_module()
    torch.manual_seed(0)
    torch.set_num_threads(max(torch.get_num_threads(), 1))
    device = torch.device("cpu")

    tokenizer = AutoTokenizer.from_pretrained(exp004.MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(exp004.MODEL_ID)
    model.to(device)
    model.eval()
    return tokenizer, model, device
