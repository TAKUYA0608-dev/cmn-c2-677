"""CMN-C2-677 — inner domain workflow graph (Cat 2).

Instantiated by DriftDiagnosisWorkflowGraphNode.get_subgraph() in graph.py. Linear topology with
per-node skip guards (the portable Cat 2 form; conditional edges don't propagate across the subgraph
boundary):

    START → drift_intent_classify → versioned_kb_retrieve → drift_diagnosis_synthesize → END

On rejected / no-intent / 0-hit input, drift_intent_classify / versioned_kb_retrieve set
retrieval_hit_count=0 (+error_code); drift_diagnosis_synthesize emits the out-of-scope safe answer —
no fabricated diagnosis.
"""

from __future__ import annotations
from typing import Any

from langgraph.graph import END, START

from framework.graph.base_graph import BaseGraph
from framework.schemas.agent_state import AgentState

from src.nodes.drift_diagnosis_synthesize_node import DriftDiagnosisSynthesizeNode
from src.nodes.drift_intent_classify_node import DriftIntentClassifyNode
from src.nodes.versioned_kb_retrieve_node import VersionedKbRetrieveNode
from src.schemas.state import State


class DriftDiagnosisWorkflow(BaseGraph):
    """Inner graph: intent_classify → kb_retrieve → diagnosis_synthesize."""

    @property
    def name(self) -> str:
        return "DriftDiagnosisWorkflow"

    @property
    def state_schema(self) -> type:
        return State

    def _validate_config(self) -> None:
        pass

    def register_nodes(self) -> None:
        # No super() — BaseGraph.register_nodes() is abstract.
        self._nodes["drift_intent_classify"] = DriftIntentClassifyNode()
        self._nodes["versioned_kb_retrieve"] = VersionedKbRetrieveNode()
        self._nodes["drift_diagnosis_synthesize"] = DriftDiagnosisSynthesizeNode()

    def add_edges(self) -> None:
        # Static linear backbone; the rejected / 0-hit skip is handled by per-node guards.
        self._sg.add_edge(START, "drift_intent_classify")
        self._sg.add_edge("drift_intent_classify", "versioned_kb_retrieve")
        self._sg.add_edge("versioned_kb_retrieve", "drift_diagnosis_synthesize")
        self._sg.add_edge("drift_diagnosis_synthesize", END)

    def route(self, state: AgentState) -> str:
        """Required by the BaseGraph ABC. Linear topology → not wired to a conditional edge."""
        if state.get("error_code") or state.get("retrieval_hit_count", 0) == 0:
            return "drift_diagnosis_synthesize"
        return "versioned_kb_retrieve"

    def get_output(self, state: AgentState) -> dict[str, Any]:
        return {
            "output": state.get("result"),
            "status": state.get("status"),
            "retrieval_hit_count": state.get("retrieval_hit_count", 0),
            "error_code": state.get("error_code"),
            "trace_id": state.get("trace_id"),
            "correlation_id": state.get("correlation_id"),
            "node_history": state.get("node_history", []),
        }
