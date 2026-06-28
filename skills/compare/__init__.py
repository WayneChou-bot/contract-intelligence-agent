"""Compare two contracts and say which is riskier (deterministic)."""
from __future__ import annotations
from typing import Dict
from skills.contract_review import review


def compare(contract_a: str, contract_b: str) -> Dict:
    """Compare two contracts by their high-risk clauses."""
    ra, rb = review(contract_a), review(contract_b)
    ha = {c["clause_type"] for c in ra["clauses"] if c["risk_level"] == "high"}
    hb = {c["clause_type"] for c in rb["clauses"] if c["risk_level"] == "high"}
    if len(ha) > len(hb):
        riskier = "A"
    elif len(hb) > len(ha):
        riskier = "B"
    else:
        riskier = "tie"
    return {
        "a_high_risk": sorted(ha),
        "b_high_risk": sorted(hb),
        "only_in_a": sorted(ha - hb),
        "only_in_b": sorted(hb - ha),
        "shared": sorted(ha & hb),
        "riskier": riskier,
        "verdict": (f"Contract {riskier} carries more high-risk clauses."
                    if riskier != "tie" else "Both contracts carry similar risk."),
    }
