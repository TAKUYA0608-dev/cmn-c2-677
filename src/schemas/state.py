"""CMN-C2-677 — Agent state (AI Agent Configuration Drift Diagnosis, Cat 2).

ADR-005: State is a flat TypedDict — never a validation/BaseModel instance. Complex fields are stored
as JSON strings (``NotRequired[str]`` + ``# JSON:``); nodes ``json.dumps`` on write / ``json.loads`` on read.

S-5 / State Safety: **no secrets, endpoints, tokens or PII are persisted** — the caller's declared
config baseline / observed-state description are sanitised (endpoint / token / credential / PII
redacted) at pre_process before anything is written to ``validated_input``. The agent is advisory-only
(read-only): it never inspects a live system, ingests telemetry, or changes any configuration.

All agent-specific fields are NotRequired (populated progressively; absent at empty-start invoke).
"""

from __future__ import annotations


from framework.schemas.agent_state import AgentState


class State(AgentState):
    """Agent state for the configuration-drift diagnosis workflow."""

    # ── pre_process (InputValidate — S-1/S-2 validated + redacted request) ────
    validated_input: str  # JSON: {query, declared_baseline, observed_state, drift_hint}
    input_format: str  # "json" | "text" | "empty"
    enriched_context: str  # JSON: {source, channel} (read-only caller context)

    # ── inner workflow (intent_classify → kb_retrieve → diagnosis_synthesize) ─
    drift_intent: str  # JSON: [{dimension, evidence}] classified drift dimensions
    retrieved_guidance: str  # JSON: [{dim_id, dimension, title, source, version, score, ...}]
    retrieval_hit_count: int  # versioned guidance entries retrieved (0 → out-of-scope safe answer)
    diagnosis: str  # JSON: [{dimension, comparison_method, interpretation, disambiguation, citation}]
    checklist: str  # JSON: [diagnosis verification checklist items]
    result: str  # JSON: assembled Configuration Drift Diagnosis Package

    # ── post_process (S-3 gate + S-4 audit) ──────────────────────────────────
    formatted_output: str  # JSON: final response envelope (package + advisory disclaimer)
    disclaimer: str  # mandatory advisory ("consult the config owner / do not auto-apply") disclaimer
    audit_logged: bool  # True once the terminal audit event is emitted

    # ── degraded-path signalling (SUCCESS + error_code, never status=ERROR) ──
    error_code: str  # INJECTION_REJECTED | INPUT_TOO_LONG | INPUT_REJECTED | NO_INTENT | NO_GUIDANCE
    error_message: str  # operator-facing detail
