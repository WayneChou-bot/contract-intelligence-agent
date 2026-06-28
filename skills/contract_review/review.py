"""Deterministic, bilingual (ZH/EN) risk review.

Splits a contract into clause-sized segments and flags high-risk clause types in
both Chinese and English using a curated keyword taxonomy. No LLM is involved, so
the result is reproducible and unit-testable. Reasons/suggestions are written in
English; the agent's presentation layer localizes them to the conversation.
"""

from __future__ import annotations

import re
from typing import Dict, List

# clause_type (bilingual label) -> (keywords[zh+en], risk_level, reason, action)
_CLAUSE_RULES = {
    "自動續約 (auto-renewal)": (
        ["自動續約", "自動延長", "期滿自動", "視為同意調整",
         "auto-renew", "automatically renew", "renew automatically", "renews automatically"],
        "high",
        "Renews automatically; you may miss the cancellation window.",
        "Add a pre-expiry opt-out, or require fresh written consent to renew.",
    ),
    "高額違約金 (high penalty)": (
        ["違約金", "賠償金", "懲罰性", "倍之", "倍違約",
         "penalty", "liquidated damages", "early termination fee"],
        "high",
        "Early termination triggers a steep penalty.",
        "Cap the penalty or reduce it to actual damages.",
    ),
    "單方終止 (unilateral termination)": (
        ["單方終止", "單方", "得隨時終止", "逕行終止", "隨時以書面單方",
         "sole discretion to terminate", "terminate at its sole discretion",
         "unilaterally terminate", "terminate this agreement at any time"],
        "high",
        "The counterparty can terminate at will; the right is not reciprocal.",
        "Require mutual termination rights and a reasonable notice period.",
    ),
    "連帶保證 (joint guarantee)": (
        ["連帶保證", "連帶責任", "保證人",
         "joint and several", "jointly and severally", "guarantor"],
        "high",
        "You may be jointly and severally liable for another party's debt.",
        "Avoid it, or cap the guarantee scope and amount.",
    ),
    "智財權歸屬 (IP assignment)": (
        ["智慧財產", "著作權", "專利權", "無償歸", "成果歸屬",
         "assigns all right", "assign all intellectual", "sole property of",
         "work made for hire", "belong exclusively to"],
        "high",
        "Your work product may be assigned to the other party for free.",
        "Define ownership for work outside the engagement scope.",
    ),
    "無限期保密 (perpetual confidentiality)": (
        ["永久保密", "無限期", "永久",
         "in perpetuity", "perpetual", "survive indefinitely", "indefinitely"],
        "high",
        "Indefinite confidentiality is hard to comply with and risky.",
        "Limit the confidentiality term to a reasonable period (e.g. 2-5 years).",
    ),
    "境外管轄 (foreign jurisdiction)": (
        ["準據法", "管轄法院", "外國法院", "國際仲裁", "新加坡法律", "境外仲裁",
         "governed by the laws of", "exclusive jurisdiction", "arbitration in"],
        "high",
        "Disputes must be handled abroad - costly and slow.",
        "Seek your local courts / law as the governing forum.",
    ),
    "免責或責任上限 (liability cap / disclaimer)": (
        ["免責", "不負任何責任", "責任上限", "概不負責",
         "limitation of liability", "shall not be liable", "disclaims all", "in no event"],
        "high",
        "Broad disclaimers can leave you with no recourse.",
        "Carve out gross negligence and willful misconduct.",
    ),
}

# Strip everything except letters/digits/CJK so "Penalty", "Penalty:", "PENALTY-"
# all normalize to the same token for the heading check below.
_NORM = re.compile(r"[^0-9a-z一-鿿]+")


def _norm(s: str) -> str:
    return _NORM.sub("", s.lower())


def split_clauses(text: str) -> List[str]:
    """Split contract text into clause-sized segments (handles ZH and EN)."""
    parts = re.split(r"[。\n；;.]+", text)
    return [p.strip() for p in parts if p.strip()]


def heuristic_risk_review(clean_text: str) -> Dict:
    """Return a ContractReview-shaped dict (clauses + summary), no LLM.

    Reports each high-risk clause *type* at most once: a single logical clause
    can trip two keywords (e.g. "governed by the laws of ..." and "exclusive
    jurisdiction") or be OCR-split across sentences, which must not double-count.
    """
    clauses: List[Dict] = []
    seen: set = set()
    for segment in split_clauses(clean_text):
        seg_l = segment.lower()
        seg_norm = _norm(segment)
        for clause_type, (keywords, level, reason, action) in _CLAUSE_RULES.items():
            matched = next(
                (kw for kw in keywords if (kw in segment) or (kw.lower() in seg_l)),
                None,
            )
            if matched is None:
                continue
            # Ignore section headings: a segment that is *only* the keyword
            # (e.g. the heading "Penalty" from "3. Penalty.") is not a clause.
            if seg_norm == _norm(matched):
                continue
            # Report each risk type once (dedupe duplicate / OCR-split hits).
            if clause_type in seen:
                continue
            seen.add(clause_type)
            clauses.append({
                "clause_type": clause_type,
                "text": segment,
                "risk_level": level,
                "reason": reason,
                "suggested_action": action,
            })
            break  # one new type per segment

    high = [c for c in clauses if c["risk_level"] == "high"]
    if high:
        summary = f"Found {len(high)} high-risk clause(s); human review recommended."
    else:
        summary = "No obvious high-risk clauses detected."
    return {"clauses": clauses, "summary": summary}
