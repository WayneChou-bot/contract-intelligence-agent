"""Contract review capability: PII redaction, prompt-injection defense, clause
risk scoring, and routing. Deterministic and unit-tested; no LLM required."""
from __future__ import annotations
from typing import Dict
from .security import screen
from .review import heuristic_risk_review
from .logic import needs_human_review, render_report


def review(contract_text: str) -> Dict:
    """Run the full contract-review pipeline and return a structured result."""
    result = screen(contract_text)
    if result.injection_detected:
        rev = {
            "clauses": [],
            "summary": "Prompt injection detected; AI review skipped.",
            "security_flag": True,
            "redacted_categories": result.redacted_categories,
        }
    else:
        core = heuristic_risk_review(result.clean_text)
        rev = {**core, "security_flag": False,
               "redacted_categories": result.redacted_categories}
    rev["route"] = "human_review" if needs_human_review(rev) else "auto_approve"
    rev["injection_reasons"] = result.injection_reasons
    rev["report_markdown"] = render_report(rev)
    return rev
