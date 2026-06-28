"""Tests for the deterministic bilingual demo risk reviewer."""

from skills.contract_review.review import heuristic_risk_review, split_clauses


def _types(review):
    return [c["clause_type"] for c in review["clauses"]]


def test_split_clauses_zh_and_en():
    assert len(split_clauses("第一條。第二條；第三條\n第四條")) == 4
    assert len(split_clauses("Clause one. Clause two; clause three")) == 3


def test_flags_auto_renewal_zh():
    review = heuristic_risk_review("除非到期前三十日書面通知，否則自動續約一年。")
    assert any("自動續約" in t for t in _types(review))
    assert any(c["risk_level"] == "high" for c in review["clauses"])


def test_flags_english_clauses():
    text = ("This Agreement renews automatically for successive terms. "
            "Vendor may terminate this agreement at any time. "
            "Governed by the laws of Singapore.")
    review = heuristic_risk_review(text)
    joined = " ".join(_types(review))
    assert "auto-renewal" in joined
    assert "unilateral termination" in joined
    assert "foreign jurisdiction" in joined


def test_flags_penalty_and_foreign_jurisdiction_zh():
    review = heuristic_risk_review("提前終止應給付三倍之違約金。本合約準據法為新加坡法律。")
    joined = " ".join(_types(review))
    assert "高額違約金" in joined
    assert "境外管轄" in joined


def test_clean_contract_has_no_high_risk():
    review = heuristic_risk_review("租期一年，押金兩個月，期滿雙方另行協議。")
    assert all(c["risk_level"] != "high" for c in review["clauses"])
    assert "No obvious" in review["summary"]
