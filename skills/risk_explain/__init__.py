"""Plain-language risk explanation + recommendations (deterministic)."""
from __future__ import annotations
from typing import Dict, List
from skills.contract_review import review


def explain(contract_text: str) -> Dict:
    """Explain why each flagged clause is risky and how to fix it."""
    r = review(contract_text)
    items: List[Dict] = []
    for c in r["clauses"]:
        if c["risk_level"] == "high":
            items.append({
                "clause_type": c["clause_type"],
                "why_it_matters": c["reason"],
                "recommendation": c["suggested_action"],
            })
    if not items and not r["security_flag"]:
        headline = "No high-risk clauses to explain — this contract looks low risk."
    elif r["security_flag"]:
        headline = "This document contained a prompt-injection attempt; it was blocked and escalated."
    else:
        headline = f"{len(items)} clause(s) need your attention before signing."
    return {"headline": headline, "explanations": items}
