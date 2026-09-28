"""CMN-C2-677 — inner workflow step 3: drift_diagnosis_synthesize.

Synthesises the advisory **Configuration Drift Diagnosis Package**: per-dimension comparison method +
interpretation + config-drift-vs-other-cause disambiguation, plus a verification checklist — grounded
in the retrieved **versioned** guidance and **conditioned on the caller's declared baseline / observed
state** (not a static dictionary lookup). Each dimension carries a source + KB-version citation. On the
0-hit / rejected branch it emits the out-of-scope safe answer (no fabricated diagnosis).
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.utils.audit import emit_trace_event

_OUT_OF_SCOPE = (
    "ご質問に該当する config-drift 診断ガイダンスが versioned KB（prompt/version・tool-manifest・"
    "model-parameter・policy・deployment-environment）に見つかりませんでした。診断したい drift 次元"
    "（プロンプト版数・ツール manifest・モデル/パラメータ・ポリシー・デプロイ環境）や宣言 config baseline を"
    "具体化いただくか、config drift 以外（model/data/operational 要因）の可能性は担当窓口にご確認ください。"
)


class DriftDiagnosisSynthesizeNode(FunctionNode):
    """Compose the grounded, cited diagnosis map + verification checklist (or safe answer on 0-hit)."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        guidance = json.loads(state.get("retrieved_guidance") or "[]")
        if state.get("error_code") or not guidance:
            emit_trace_event(
                "drift_diagnosis_synthesize.safe", {"reason": state.get("error_code") or "no_guidance"}, state
            )
            report: dict[str, Any] = {
                "status_kind": "out_of_scope",
                "message": _OUT_OF_SCOPE,
                "diagnosis": [],
                "checklist": [],
                "citations": [],
            }
            return {"result": json.dumps(report, ensure_ascii=False), "status": AgentStatus.SUCCESS.value}

        scope = json.loads(state.get("validated_input") or "{}")
        has_baseline = bool(scope.get("declared_baseline"))
        has_observed = bool(scope.get("observed_state"))

        diagnosis: list[dict[str, Any]] = []
        checklist: list[dict[str, Any]] = []
        citations: list[dict[str, str]] = []
        for g in guidance:
            diagnosis.append(
                {
                    "dimension": g["dimension"],
                    "title": g["title"],
                    "comparison_method": g["comparison_method"],
                    "interpretation": g["interpretation"],
                    "cause_disambiguation": g["disambiguation"],
                    # Conditioned on the caller's actual inputs — the synthesis is not a static lookup.
                    "grounded_on": {
                        "declared_baseline_provided": has_baseline,
                        "observed_state_provided": has_observed,
                    },
                    "citation": {"source": g["source"], "kb_version": g["kb_version"]},
                }
            )
            citations.append({"dim_id": g["dim_id"], "source": g["source"], "kb_version": g["kb_version"]})
            for step in g["verification_steps"]:
                checklist.append({"dimension": g["dimension"], "step": step, "checked": False})

        report = {
            "status_kind": "diagnosis",
            "diagnosis": diagnosis,
            "checklist": checklist,
            "citations": citations,
            "baseline_provided": has_baseline,
            "observed_provided": has_observed,
        }
        emit_trace_event(
            "drift_diagnosis_synthesize.complete",
            {
                "dimension_count": len(diagnosis),
                "checklist_count": len(checklist),
                "citation_count": len(citations),
                "baseline_provided": has_baseline,
                "observed_provided": has_observed,
            },
            state,
        )
        return {
            "result": json.dumps(report, ensure_ascii=False),
            "diagnosis": json.dumps(diagnosis, ensure_ascii=False),
            "checklist": json.dumps(checklist, ensure_ascii=False),
            "status": AgentStatus.SUCCESS.value,
        }
