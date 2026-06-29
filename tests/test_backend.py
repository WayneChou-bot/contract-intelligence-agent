"""Backend-selection logic (offline; does not call any model)."""
from skills import llm_backend
from app import model as app_model


def test_default_backend_is_gemini(monkeypatch):
    monkeypatch.delenv("MODEL_BACKEND", raising=False)
    assert llm_backend.backend() == "gemini"
    assert app_model.backend() == "gemini"
    assert llm_backend.is_local() is False


def test_local_backend_selected(monkeypatch):
    monkeypatch.setenv("MODEL_BACKEND", "local")
    assert llm_backend.is_local() is True
    assert app_model.backend() == "local"


def test_engine_label_tracks_backend(monkeypatch):
    monkeypatch.setenv("MODEL_BACKEND", "local")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma4")
    assert llm_backend.engine_label() == "ollama:gemma4"
    monkeypatch.setenv("MODEL_BACKEND", "gemini")
    assert llm_backend.engine_label() == "gemini-flash-latest"


def test_cloud_needs_key_local_does_not(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("MODEL_BACKEND", "gemini")
    assert llm_backend.unavailable_reason() is not None   # needs a key
    monkeypatch.setenv("MODEL_BACKEND", "local")
    assert llm_backend.unavailable_reason() is None        # local needs no key
