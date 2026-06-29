"""Document ingestion (deterministic OCR / text extraction).

Turns a PDF or image into plain text using **Tesseract** (and PyMuPDF for PDFs).
This step is deliberately deterministic and model-free: it exists so the
deterministic security screen (PII redaction + prompt-injection detection) and
the rule-based reviewer have *text* to work on. It runs entirely on-device, so a
scanned contract never has to be sent to any model just to be read.

Pipeline role:  document -> [deterministic OCR] -> [deterministic screen] -> model only for judgment.

Needs the 'ocr' extra (pip install '.[ocr]') and the Tesseract binary. For
Traditional Chinese contracts also install the language pack (tesseract chi_tra).
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Dict, Tuple

import re as _re

def _normalize(text: str) -> str:
    """De-wrap OCR output: join soft-wrapped lines within a paragraph (so a
    keyword is never split across a line break), keep paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paras = _re.split(r"\n\s*\n", text)
    out = []
    for para in paras:
        joined = " ".join(ln.strip() for ln in para.split("\n") if ln.strip())
        if joined:
            out.append(joined)
    return "\n".join(out)


_MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}
_DESIRED_LANGS = ["eng", "chi_tra", "chi_sim"]


def _ocr_lang() -> str:
    """Use OCR_LANG if set, else the installed subset of eng/chi_tra/chi_sim."""
    override = os.environ.get("OCR_LANG")
    if override:
        return override.strip()
    try:
        import pytesseract
        available = set(pytesseract.get_languages(config=""))
    except Exception:
        available = set()
    langs = [l for l in _DESIRED_LANGS if l in available] or ["eng"]
    return "+".join(langs)


def _configure_tesseract() -> None:
    """Point pytesseract at a specific binary via TESSERACT_CMD (handy on
    Windows where tesseract.exe is often not on PATH)."""
    cmd = os.environ.get("TESSERACT_CMD")
    if cmd:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = cmd


def _ocr_image_bytes(data: bytes, lang: str) -> str:
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(io.BytesIO(data)), lang=lang)


def _read_pdf(path: Path, lang: str) -> Tuple[str, str]:
    import fitz  # PyMuPDF
    doc = fitz.open(str(path))
    # 1) digital PDF: use the embedded text layer (exact, no OCR needed)
    layer = "\n".join(page.get_text() for page in doc).strip()
    if len(layer) >= 40:
        return layer, "pdf-text-layer"
    # 2) scanned PDF: rasterize each page and OCR it locally
    pages = [_ocr_image_bytes(page.get_pixmap(dpi=200).tobytes("png"), lang)
             for page in doc]
    return "\n".join(pages), f"tesseract({lang})"


def read_document(file_path: str) -> Dict:
    """Extract text from a PDF or image at `file_path` with deterministic OCR.

    Returns {"text": ...} on success, or {"text": None, "note": ...} when the
    file is missing, the type is unsupported, or OCR tooling is not installed.
    """
    path = Path(file_path)
    if not path.is_file():
        return {"text": None, "note": f"File not found: {file_path}"}

    mime = _MIME.get(path.suffix.lower())
    if mime is None:
        return {"text": None,
                "note": f"Unsupported file type '{path.suffix}'. "
                        f"Supported: {', '.join(sorted(_MIME))}."}

    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return {"text": None,
                "note": "OCR needs the 'ocr' extra: pip install '.[ocr]' "
                        "(and the Tesseract binary)."}
    if mime == "application/pdf":
        try:
            import fitz  # noqa: F401
        except ImportError:
            return {"text": None,
                    "note": "PDF OCR needs PyMuPDF: pip install '.[ocr]'."}

    _configure_tesseract()
    lang = _ocr_lang()
    try:
        if mime == "application/pdf":
            raw, engine = _read_pdf(path, lang)
        else:
            raw, engine = _ocr_image_bytes(path.read_bytes(), lang), f"tesseract({lang})"
        text = _normalize(raw).strip()
        return {"text": text, "source": str(path),
                "mime_type": mime, "engine": engine, "ocr_lang": lang}
    except Exception as e:  # e.g. Tesseract binary missing / unreadable file
        return {"text": None, "note": f"OCR error: {e}"}
