"""Translation capability. Runs on the active model backend (cloud Gemini or a
local Ollama model). Demonstrates an LLM-backed skill that still honors the
data-localization switch."""
from __future__ import annotations
from typing import Dict

from skills import llm_backend


def translate(text: str, target_language: str = "English") -> Dict:
    """Translate contract text into the target language (default English)."""
    reason = llm_backend.unavailable_reason()
    if reason:
        return {"translated": None, "note": reason}
    try:
        prompt = (f"Translate the following contract into {target_language}. "
                  "Preserve the clause structure and numbering; output only the "
                  "translation.\n\n" + text)
        out = llm_backend.generate_text(prompt)
        return {"translated": out, "target_language": target_language,
                "engine": llm_backend.engine_label()}
    except Exception as e:  # pragma: no cover - depends on env/network
        return {"translated": None, "note": f"Translation error: {e}"}
