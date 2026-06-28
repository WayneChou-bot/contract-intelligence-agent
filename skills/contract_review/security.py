"""Pre-LLM security screen: PII redaction + prompt-injection detection.

Bilingual (Chinese + English). Deterministic (pure regex/string logic, no LLM),
so it runs BEFORE any text reaches the model and is fully unit-tested.

  * PII (TW national ID, US SSN, credit cards, phones, emails) is masked before
    it can be sent to the model or written to logs.
  * Adversarial instructions hidden in the contract body (prompt injection, EN/ZH)
    are detected and the document is short-circuited straight to a human.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

# --- PII patterns -----------------------------------------------------------
# (label, mask token, compiled pattern). Order matters: broader / longer
# numeric patterns first so they aren't partially consumed by a later one.
_PII_PATTERNS: List[Tuple[str, str, "re.Pattern"]] = [
    ("credit card", "[REDACTED: credit card]",
     re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{1,4}\b")),
    ("national ID", "[REDACTED: national ID]",   # Taiwan national ID
     re.compile(r"\b[A-Z][12]\d{8}\b")),
    ("SSN", "[REDACTED: SSN]",                    # US Social Security Number
     re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("email", "[REDACTED: email]",
     re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("phone", "[REDACTED: phone]",                # TW mobile
     re.compile(r"\b09\d{8}\b")),
    ("phone", "[REDACTED: phone]",                # TW landline
     re.compile(r"\b0\d{1,2}-?\d{6,8}\b")),
    ("phone", "[REDACTED: phone]",                # US phone
     re.compile(r"\b(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b")),
]

# --- Prompt-injection patterns ----------------------------------------------
_INJECTION_PATTERNS: List[Tuple[str, "re.Pattern"]] = [
    ("override instructions (ignore previous)",
     re.compile(r"ignore\s+(all\s+|the\s+|any\s+)?(previous|above|prior|earlier)\s+(instruction|rule|prompt)", re.I)),
    ("override instructions (disregard above)",
     re.compile(r"disregard\s+(all\s+|the\s+)?(previous|above|prior)", re.I)),
    ("override instructions (中文：忽略規則)",
     re.compile(r"忽略(以上|上述|前面|先前|這些)?.{0,8}(規則|指示|指令|提示|設定)")),
    ("force no-risk / auto-approve verdict",
     re.compile(r"(mark|標記|judge|classify|rate|score|set|視為|當作).{0,14}(no[\s-]*risk|low[\s-]*risk|無風險|低風險|safe|安全|auto[\s-]*approve|自動(核准|通過|批准))", re.I)),
    ("role injection (system/assistant)",
     re.compile(r"(you are now|系統指示|<\s*system\s*>|\b(?:system|assistant)\s*:)", re.I)),
    ("suppress safety (do not flag)",
     re.compile(r"(do not|don't|不要|請勿|別).{0,10}(flag|標記|raise|報告|alert|警示|escalat)", re.I)),
    ("set risk to low/no",
     re.compile(r"set\s+risk\s+to\s+(low|no|none|minimal)", re.I)),
    ("auto-approve request",
     re.compile(r"(auto[\s-]*approve|自動(核准|通過|批准|放行))", re.I)),
]


@dataclass
class ScreenResult:
    clean_text: str
    redacted_categories: List[str] = field(default_factory=list)
    injection_detected: bool = False
    injection_reasons: List[str] = field(default_factory=list)


def redact_pii(text: str) -> Tuple[str, List[str]]:
    """Mask PII in `text`. Returns (redacted_text, sorted_unique_categories)."""
    categories: List[str] = []
    redacted = text
    for label, token, pattern in _PII_PATTERNS:
        if pattern.search(redacted):
            categories.append(label)
            redacted = pattern.sub(token, redacted)
    return redacted, sorted(set(categories))


def detect_injection(text: str) -> Tuple[bool, List[str]]:
    """Detect prompt-injection attempts. Returns (detected, reasons)."""
    reasons: List[str] = []
    for reason, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            reasons.append(reason)
    return (len(reasons) > 0), reasons


def screen(text: str) -> ScreenResult:
    """Run the full pre-LLM screen. Injection is checked on the original text
    (so masking can't hide an attack); clean_text always has PII removed."""
    injection_detected, injection_reasons = detect_injection(text)
    clean_text, categories = redact_pii(text)
    return ScreenResult(
        clean_text=clean_text,
        redacted_categories=categories,
        injection_detected=injection_detected,
        injection_reasons=injection_reasons,
    )
