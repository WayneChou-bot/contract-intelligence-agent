"""Pydantic schemas shared across the workflow.

Using strict, typed schemas (rather than passing around loose dicts) is one of
the secure-coding "paved roads": every LLM output and every tool boundary is
validated, which prevents malformed or injected data from flowing downstream.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high"]


class Clause(BaseModel):
    """A single contract clause with its assessed risk."""

    clause_type: str = Field(
        description="條款類型，例如 自動續約 / 高額違約金 / 單方終止"
    )
    text: str = Field(description="條款原文（已遮蔽 PII）")
    risk_level: RiskLevel = Field(description="low / medium / high")
    reason: str = Field(description="判定此風險等級的理由")
    suggested_action: str = Field(description="給使用者的具體建議")


class ContractReview(BaseModel):
    """The full structured output of the risk-review stage."""

    clauses: List[Clause] = Field(default_factory=list)
    summary: str = Field(default="", description="一段話總結整份合約的風險")
    security_flag: bool = Field(
        default=False,
        description="是否偵測到提示注入或敏感資料事件",
    )
    redacted_categories: List[str] = Field(
        default_factory=list,
        description="security_screen 遮蔽掉的個資類別",
    )
