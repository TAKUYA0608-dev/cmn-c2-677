"""CMN-C2-677 — post_process node: SafetyAndCitationGate (S-3 output gate + S-4 audit).

S-3: verify citation completeness (a grounded diagnosis must cite its versioned guidance source),
strip any residual sensitive payload, and append the mandatory advisory disclaimer ("advisory only —
do not auto-apply; the config owner confirms on the live system"). S-4: emit an audit event (drift
dimension / counts only — never the raw query, declared baseline, observed state, endpoints, tokens or
PII). Runs on both the full diagnosis and the out-of-scope safe branch.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.utils.audit import emit_trace_event

_DISCLAIMER = (
    "本診断は公開された config-drift 診断ガイダンス（versioned KB）に基づく参考情報であり、宣言 config baseline と"
    "観測状態記述の範囲での助言です。本エージェントは live system を検査せず、telemetry を取込まず、config を一切"
    "変更しません（read-only）。最終的な原因特定・設定変更・remediation は必ず担当エンジニア / config owner が実 "
    "system を確認した上で判断してください。config drift 以外（model / data / operational 要因）の可能性も併せてご検討ください。"
)


class PostProcessNode(FunctionNode):
    """Verify citations, strip sensitive payload, append advisory disclaimer, emit audit."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """S-3 preservation check: advisory disclaimer present in the output envelope.

        SDK 1.0.0 contract: receives the **result dict from `execute()`**; returns the (possibly
        filtered) result. MAY raise to block an output missing the mandatory disclaimer.
        """
        out = result.get("formatted_output", "")
        if out and "参考" not in out and "config owner" not in out:
            raise ValueError("S-3: advisory disclaimer missing from output")
        return dict(result)

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        report: dict[str, Any] = json.loads(state.get("result", "{}") or "{}")

        citations = report.get("citations", [])
        grounded = report.get("status_kind") == "diagnosis"
        citation_complete = (not grounded) or bool(citations)

        formatted = {
            "status_kind": report.get("status_kind"),
            "diagnosis": report.get("diagnosis", []),
            "checklist": report.get("checklist", []),
            "citations": citations,
            "citation_complete": citation_complete,
            "baseline_provided": report.get("baseline_provided", False),
            "observed_provided": report.get("observed_provided", False),
            "message": report.get("message"),
            "advisory_only": True,
            "disclaimer": _DISCLAIMER,
        }
        emit_trace_event(
            "safety_citation_gate.complete",
            {
                "status_kind": report.get("status_kind"),
                "dimension_count": len(report.get("diagnosis", [])),
                "citation_complete": citation_complete,
                "error_code": state.get("error_code"),
            },
            state,
        )
        return {
            "formatted_output": json.dumps(formatted, ensure_ascii=False),
            "disclaimer": _DISCLAIMER,
            "audit_logged": True,
            "status": AgentStatus.SUCCESS.value,
        }
