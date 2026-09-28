"""CMN-C2-677 — inner workflow step 1: drift_intent_classify.

Deterministic classification of the drift dimension(s) of interest — prompt/version, tool-manifest,
model-parameter, policy, deployment-environment — from the (redacted) query. **0 classified dimensions
(rejected input or an out-of-scope question) routes to the out-of-scope safe answer** — the agent never
fabricates a diagnosis that is not grounded in the versioned guidance KB.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.services.service import DriftGuidanceKB
from src.utils.audit import emit_trace_event


class DriftIntentClassifyNode(FunctionNode):
    """Classify the drift dimensions the caller is asking about."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        scope = json.loads(state.get("validated_input") or state.get("user_input") or "{}")
        canonical = json.dumps(scope, ensure_ascii=False)
        if state.get("error_code") or not scope.get("query"):
            emit_trace_event("drift_intent_classify.skip", {"reason": state.get("error_code") or "empty_query"}, state)
            return {
                "validated_input": canonical,
                "drift_intent": "[]",
                "retrieval_hit_count": 0,
                "error_code": state.get("error_code") or "NO_INTENT",
                "status": AgentStatus.SUCCESS.value,
            }

        dims = DriftGuidanceKB.classify_dimensions(scope["query"])
        emit_trace_event("drift_intent_classify.complete", {"dimension_count": len(dims)}, state)
        out = {
            "validated_input": canonical,
            "drift_intent": json.dumps(dims, ensure_ascii=False),
            "status": AgentStatus.SUCCESS.value,
        }
        if not dims:
            out["retrieval_hit_count"] = 0
            out["error_code"] = "NO_INTENT"
        return out
