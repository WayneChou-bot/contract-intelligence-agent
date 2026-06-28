"""Deterministic business logic for routing decisions.

Kept separate from the ADK graph wiring so it can be unit-tested without any
LLM or ADK runtime (see tests/test_logic.py). The graph in agent.py simply
calls these helpers to decide which edge to take.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .config import ESCALATION_RISK_LEVEL, LEGAL_DISCLAIMER

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def is_high_risk(clause: Dict[str, Any]) -> bool:
    """True if a clause meets/exceeds the escalation risk level."""
    level = str(clause.get("risk_level", "low")).lower()
    return _RISK_ORDER.get(level, 0) >= _RISK_ORDER[ESCALATION_RISK_LEVEL]


def needs_human_review(review: Dict[str, Any]) -> bool:
    """Decide whether a reviewed contract must go to a human.

    Escalate if a security event was flagged OR any clause is high risk.
    """
    if review.get("security_flag"):
        return True
    clauses: List[Dict[str, Any]] = review.get("clauses", []) or []
    return any(is_high_risk(c) for c in clauses)


def render_report(review: Dict[str, Any], human_decision: str | None = None) -> str:
    """Render a Markdown risk report from a review dict."""
    lines: List[str] = ["# 合約風險體檢報告", ""]

    if review.get("security_flag"):
        lines.append(
            "> ⚠️ 安全事件：偵測到提示注入或敏感資料，已跳過 AI 判讀並轉人工。"
        )
        lines.append("")

    redacted = review.get("redacted_categories") or []
    if redacted:
        lines.append(f"已遮蔽個資類別：{', '.join(redacted)}")
        lines.append("")

    summary = review.get("summary")
    if summary:
        lines.append(f"摘要：{summary}")
        lines.append("")

    clauses = review.get("clauses", []) or []
    if clauses:
        lines.append("| 條款類型 | 風險 | 理由 | 建議 |")
        lines.append("|---|---|---|---|")
        for c in clauses:
            lines.append(
                f"| {c.get('clause_type','')} | {c.get('risk_level','')} | "
                f"{c.get('reason','')} | {c.get('suggested_action','')} |"
            )
        lines.append("")

    if human_decision:
        lines.append(f"人工覆核結果：{human_decision}")
        lines.append("")

    lines.append(f"_{LEGAL_DISCLAIMER}_")
    return "\n".join(lines)
