"""Cloud/local model switch for the LLM-backed skills (currently: translate).

MODEL_BACKEND=gemini (default) -> Google Gemini via google-genai (cloud).
MODEL_BACKEND=local            -> a local model via Ollama + LiteLLM (on-device).

Deterministic skills (contract_review, read_document) never use this — they are
pure Python and always run locally.
"""
from __future__ import annotations

import os
from typing import Optional


def backend() -> str:
    return os.environ.get("MODEL_BACKEND", "gemini").strip().lower()


def is_local() -> bool:
    return backend() == "local"


def ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "gemma4").strip()


def engine_label() -> str:
    return f"ollama:{ollama_model()}" if is_local() else "gemini-flash-latest"


def unavailable_reason() -> Optional[str]:
    """None if the active backend is usable, else a human-readable reason."""
    if is_local():
        return None  # assume a running Ollama; real errors surface at call time
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        return ("Cloud backend needs GOOGLE_API_KEY / GEMINI_API_KEY "
                "(or set MODEL_BACKEND=local to run on a local model).")
    return None


def generate_text(prompt: str) -> str:
    """Single-prompt text generation on the active backend."""
    if is_local():
        import litellm
        resp = litellm.completion(
            model=f"ollama_chat/{ollama_model()}",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp["choices"][0]["message"]["content"]
    from google import genai
    client = genai.Client()
    return client.models.generate_content(
        model="gemini-flash-latest", contents=prompt).text
