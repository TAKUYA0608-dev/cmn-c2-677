"""CMN-C2-677 — inner workflow step 2: versioned_kb_retrieve.

Deterministic retrieval over the **versioned** config-drift diagnostic guidance KB, keyed on the
classified drift dimensions + query tags. Sets `retrieval_hit_count`; **0 hits (rejected / no intent /
no match) routes to the out-of-scope safe answer** — no diagnosis is fabricated without grounded,
cited, versioned guidance.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.services.service import DriftGuidanceKB
from src.utils.audit import emit_trace_event


class VersionedKbRetrieveNode(FunctionNode):
    """Retrieve grounded, versioned guidance for the classified drift dimensions."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        dims_list = json.loads(state.get("drift_intent") or "[]")
        scope = json.loads(state.get("validated_input") or "{}")
        if state.get("error_code") or not dims_list:
            emit_trace_event("versioned_kb_retrieve.skip", {"reason": state.get("error_code") or "no_intent"}, state)
            return {
                "retrieved_guidance": "[]",
                "retrieval_hit_count": 0,
                "error_code": state.get("error_code") or "NO_GUIDANCE",
                "status": AgentStatus.SUCCESS.value,
            }

        dimensions = [d["dimension"] for d in dims_list]
        guidance = DriftGuidanceKB.retrieve(scope.get("query", ""), dimensions)
        emit_trace_event(
            "versioned_kb_retrieve.complete",
            {"hit_count": len(guidance), "kb_versions": sorted({g["kb_version"] for g in guidance})},
            state,
        )
        out = {
            "retrieved_guidance": json.dumps(guidance, ensure_ascii=False),
            "retrieval_hit_count": len(guidance),
            "status": AgentStatus.SUCCESS.value,
        }
        if not guidance:
            out["error_code"] = "NO_GUIDANCE"
        return out
