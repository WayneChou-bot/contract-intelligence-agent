"""Tests for deterministic routing logic (no LLM/ADK required)."""

from skills.contract_review.logic import is_high_risk, needs_human_review, render_report


def test_high_risk_clause_detected():
    assert is_high_risk({"risk_level": "high"}) is True
    assert is_high_risk({"risk_level": "medium"}) is False
    assert is_high_risk({"risk_level": "low"}) is False
    assert is_high_risk({}) is False  # missing defaults to low


def test_security_flag_forces_human_review():
    review = {"security_flag": True, "clauses": [{"risk_level": "low"}]}
    assert needs_human_review(review) is True


def test_any_high_risk_clause_escalates():
    review = {
        "security_flag": False,
        "clauses": [{"risk_level": "low"}, {"risk_level": "high"}],
    }
    assert needs_human_review(review) is True


def test_all_low_risk_auto_approves():
    review = {
        "security_flag": False,
        "clauses": [{"risk_level": "low"}, {"risk_level": "medium"}],
    }
    assert needs_human_review(review) is False


def test_report_includes_security_banner_and_disclaimer():
    review = {
        "security_flag": True,
        "redacted_categories": ["身分證"],
        "clauses": [],
        "summary": "偵測到注入。",
    }
    report = render_report(review, human_decision="reject")
    assert "安全事件" in report
    assert "身分證" in report
    assert "reject" in report
    assert "法律意見" in report  # disclaimer present


def test_report_renders_clause_table():
    review = {
        "security_flag": False,
        "clauses": [
            {
                "clause_type": "自動續約",
                "risk_level": "high",
                "reason": "未通知即續約",
                "suggested_action": "要求加入退出條款",
            }
        ],
    }
    report = render_report(review)
    assert "自動續約" in report
    assert "| 條款類型 | 風險 |" in report
