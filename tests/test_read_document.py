"""Tests for the deterministic read_document (OCR) skill."""
import os
import shutil
from pathlib import Path

import pytest

from skills.read_document import read_document

# Tesseract reachable via PATH or TESSERACT_CMD?
_HAS_OCR = bool(shutil.which("tesseract") or os.environ.get("TESSERACT_CMD"))
try:  # PyMuPDF + pytesseract available?
    import fitz  # noqa: F401
    import pytesseract  # noqa: F401
except Exception:  # pragma: no cover
    _HAS_OCR = False

_needs_ocr = pytest.mark.skipif(not _HAS_OCR, reason="tesseract / OCR libs not installed")


def test_missing_file_returns_note():
    r = read_document("samples/does_not_exist.pdf")
    assert r["text"] is None
    assert "not found" in r["note"].lower()


def test_unsupported_type_returns_note(tmp_path):
    p = tmp_path / "contract.docx"
    p.write_text("hello")
    r = read_document(str(p))
    assert r["text"] is None
    assert "unsupported" in r["note"].lower()


def test_supported_pdf_sample_exists():
    assert Path("samples/contract_scan.pdf").is_file()


@_needs_ocr
def test_ocr_reads_scanned_pdf():
    r = read_document("samples/contract_scan.pdf")
    assert r["text"]
    assert "tesseract" in r["engine"]            # deterministic OCR, not a model
    low = r["text"].lower()
    assert "singapore" in low and "penalty" in low and "perpetuity" in low


@_needs_ocr
def test_ocr_then_review_chain_flags_and_redacts():
    from skills.contract_review import review
    text = read_document("samples/contract_scan.pdf")["text"]
    r = review(text)
    highs = [c for c in r["clauses"] if c["risk_level"] == "high"]
    assert len(highs) == 5
    assert "SSN" in r["redacted_categories"]
    assert r["route"] == "human_review"
