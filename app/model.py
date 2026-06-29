"""Model backend selection for the ClauseLens agent.

MODEL_BACKEND=gemini (default) -> Google Gemini via google-genai (cloud).
MODEL_BACKEND=local            -> a local model served by Ollama, through ADK's
                                  LiteLlm bridge. Nothing leaves the machine,
                                  which is what makes the data-localization /
                                  on-prem ("enterprise") story actually true.

Local mode needs:  pip install google-adk[extensions]   (pulls LiteLLM)
                   ollama pull gemma4 ; ollama serve
"""
from __future__ import annotations

import os

from google.adk.models import Gemini
from google.genai import types


def backend() -> str:
    return os.environ.get("MODEL_BACKEND", "gemini").strip().lower()


def ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "gemma4").strip()


def build_agent_model():
    """Return the model object to hand to the ADK Agent."""
    if backend() == "local":
        # imported lazily so the cloud path needs no extra dependency
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model=f"ollama_chat/{ollama_model()}")
    return Gemini(
        model=os.environ.get("GEMINI_MODEL", "gemini-flash-latest"),
        retry_options=types.HttpRetryOptions(attempts=3),
    )
