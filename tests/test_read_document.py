"""Deterministic tests for the read_document (OCR) skill.

The Gemini call needs a key + network, so we test the guard paths that run
*before* any model call: missing file, unsupported type, and no API key.
"""
from pathlib import Path

from skills.read_document import read_document


def test_missing_file_returns_note():
    r = read_document("samples/does_not_exist.pdf")
    assert r["text"] is None
    assert "not found" in r["note"].lower()


def test_unsupported_type_returns_note(tmp_path):
    p = tmp_path / "contract.txt"
    p.write_text("hello")
    r = read_document(str(p))
    assert r["text"] is None
    assert "unsupported" in r["note"].lower()


def test_no_api_key_returns_note(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    p = tmp_path / "scan.png"
    p.write_bytes(b"\x89PNG\r\n")  # file exists & .png supported; bytes unused (no key)
    r = read_document(str(p))
    assert r["text"] is None
    assert "key" in r["note"].lower()


def test_supported_pdf_sample_exists():
    assert Path("samples/contract_scan.pdf").is_file()
