# CMN-C2-677 — Unit Tests: Cat 2 graph wiring (outer GraphNode + inner workflow)

import pytest

from src.graph.domain_workflow_graph import DriftDiagnosisWorkflow
from src.graph.graph import ConfigurationDriftDiagnosisAgent, DriftDiagnosisWorkflowGraphNode, Graph
from src.schemas.state import State


class TestOuterGraph:
    def test_registry_alias(self):
        assert ConfigurationDriftDiagnosisAgent is Graph

    def test_name_and_state_schema(self):
        g = Graph()
        assert g.name == "ConfigurationDriftDiagnosisAgent"
        assert g.state_schema is State

    def test_main_slot_is_graphnode(self):
        g = Graph()
        g.register_nodes()
        assert isinstance(g._nodes["main"], DriftDiagnosisWorkflowGraphNode)
        for slot in ("pre_process", "main", "post_process"):
            assert slot in g._nodes

    def test_error_strategy_propagate(self):
        assert DriftDiagnosisWorkflowGraphNode.error_strategy == "propagate"

    def test_get_subgraph_is_cached(self):
        node = DriftDiagnosisWorkflowGraphNode()
        assert node.get_subgraph() is node.get_subgraph()

    def test_extract_input_prefers_validated(self):
        node = DriftDiagnosisWorkflowGraphNode()
        assert node.extract_input({"validated_input": "V", "user_input": "U"}) == "V"

    def test_merge_output_maps_fields(self):
        node = DriftDiagnosisWorkflowGraphNode()
        merged = node.merge_output({}, {"output": '{"x":1}', "retrieval_hit_count": 2, "status": "success",
                                        "error_code": None})
        assert merged["result"] == '{"x":1}' and merged["retrieval_hit_count"] == 2


class TestInnerWorkflow:
    def test_inner_registers_three_nodes(self):
        wf = DriftDiagnosisWorkflow(config={})
        wf.register_nodes()
        for slot in ("drift_intent_classify", "versioned_kb_retrieve", "drift_diagnosis_synthesize"):
            assert slot in wf._nodes

    def test_route_zero_hit_to_synthesize(self):
        wf = DriftDiagnosisWorkflow(config={})
        assert wf.route({"retrieval_hit_count": 0}) == "drift_diagnosis_synthesize"

    def test_route_happy_path(self):
        wf = DriftDiagnosisWorkflow(config={})
        assert wf.route({"retrieval_hit_count": 3}) == "versioned_kb_retrieve"

    def test_get_output_surfaces_result(self):
        wf = DriftDiagnosisWorkflow(config={})
        out = wf.get_output({"result": "R", "status": "success", "retrieval_hit_count": 1})
        assert out["output"] == "R" and out["retrieval_hit_count"] == 1


class TestServerModule:
    def test_server_imports(self):
        try:
            import src.api.server as server
        except ModuleNotFoundError as exc:
            pytest.skip(f"platform module unavailable in the local stub env: {exc}")
        assert server.app is not None and server.agent is not None
