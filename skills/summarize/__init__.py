"""Executive-summary capability built on top of contract_review (deterministic)."""
from __future__ import annotations
from typing import Dict
from skills.contract_review import review


def summarize(contract_text: str) -> Dict:
    """Return a short, structured executive summary of a contract."""
    r = review(contract_text)
    highs = [c for c in r["clauses"] if c["risk_level"] == "high"]
    high_types = sorted({c["clause_type"] for c in highs})
    if r["security_flag"]:
        headline = "Security event: prompt injection detected — escalated to a human."
    elif highs:
        headline = f"{len(highs)} high-risk clause(s) found — human review recommended."
    else:
        headline = "No high-risk clauses found — low risk."
    return {
        "headline": headline,
        "high_risk_count": len(highs),
        "high_risk_types": high_types,
        "redacted_categories": r["redacted_categories"],
        "route": r["route"],
        "recommendation": "Escalate to a human." if r["route"] == "human_review" else "Safe to auto-approve.",
    }
