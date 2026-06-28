"""Translation capability. Uses Gemini via google-genai when a key is set;
returns a clear note otherwise. Demonstrates an LLM-backed skill."""
from __future__ import annotations
import os
from typing import Dict


def translate(text: str, target_language: str = "English") -> Dict:
    """Translate contract text into the target language (default English)."""
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        return {"translated": None,
                "note": "Translation needs GOOGLE_API_KEY / GEMINI_API_KEY in the environment."}
    try:
        from google import genai
        client = genai.Client()
        prompt = (f"Translate the following contract into {target_language}. "
                  f"Preserve the clause structure and numbering; output only the translation.\n\n{text}")
        resp = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
        return {"translated": resp.text, "target_language": target_language, "engine": "gemini-flash-latest"}
    except Exception as e:  # pragma: no cover - depends on env/network
        return {"translated": None, "note": f"Translation error: {e}"}
