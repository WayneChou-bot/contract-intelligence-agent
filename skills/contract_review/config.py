"""Central configuration for the ClauseGuard contract-risk agent.

All tunable business rules live here so the LLM is never the source of
truth for routing decisions. Keeping thresholds and clause taxonomy in
code (not in prompts) makes the agent deterministic, testable, and cheap.
"""

from __future__ import annotations

# --- Models -----------------------------------------------------------------
# Fast model for extraction / classification; same family for the risk judge.
# Swap MODEL_JUDGE to a "pro" tier if you need deeper reasoning at higher cost.
MODEL_FAST = "gemini-3.1-flash-lite"
MODEL_JUDGE = "gemini-3.1-flash-lite"

# --- Risk taxonomy ----------------------------------------------------------
# Clause types that, if present at "high" risk, force human-in-the-loop review.
# These are the clauses laypeople most often overlook in everyday contracts
# (leases, employment, SaaS terms).
HIGH_RISK_CLAUSE_TYPES = [
    "自動續約",        # auto-renewal
    "高額違約金",      # excessive penalty / liquidated damages
    "單方終止",        # unilateral termination
    "連帶保證",        # joint guarantee
    "智財權歸屬",      # IP assignment
    "無限期保密",      # perpetual confidentiality
    "境外管轄",        # foreign jurisdiction / governing law
    "免責或責任上限",  # liability cap / disclaimer
]

# Any clause scored at or above this level escalates the whole contract to a human.
ESCALATION_RISK_LEVEL = "high"

# --- Disclaimer -------------------------------------------------------------
# Appended to every report. This is decision-support, not legal advice.
LEGAL_DISCLAIMER = (
    "本報告由 AI 自動產生，僅供參考，不構成法律意見。"
    "重大決定前請諮詢合格律師。"
)
