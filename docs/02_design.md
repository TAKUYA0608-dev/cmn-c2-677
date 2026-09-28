# Template Design Specification — CMN-C2-677

AI Agent Configuration Drift Diagnosis Q&A Agent (Cat 2).

## Position in AgentCore Architecture

- **Agent Class**: `ConfigurationDriftDiagnosisAgent` (module-level alias of `Graph`)
- **L1 Base**: **AgentBaseGraph** (Cat 2 — outer 5-node backbone; direct L1 inheritance, no L2)
- **Category**: Cat 2 — a multi-step domain workflow (validate → intent-classify → versioned-KB
  retrieve → diagnosis-synthesize → safety/citation gate) producing a **Configuration Drift Diagnosis
  Package**; CMN industry (AI engineering infrastructure)
- **Three-Layer Separation**: State = flat TypedDict; Node = L1 inheritance (`execute` override only);
  Graph = outer `AgentBaseGraph` + **`GraphNode` in the `main` slot** wrapping an inner `BaseGraph`

## Architecture Overview

Cat 2 pattern — the `main` slot is a **`GraphNode`** (`DriftDiagnosisWorkflowGraphNode`, **subgraph
cached**) that wraps the inner `DriftDiagnosisWorkflow` (`BaseGraph`). Inner graph is a **static linear
backbone with per-node skip guards**. **Advisory-only (read-only): no live system is inspected, no
telemetry is ingested, and no configuration is changed — endpoints / tokens / credentials / PII in the
caller's declared baseline and observed-state description are redacted at pre_process (S-1/S-2).**

### Node Configuration

| Node | Responsibility | Input State | Output State | Inherits/Overrides |
|------|---------------|-------------|--------------|-------------------|
| initialize | schema_version, session_id, trust_level | user_input | (framework) | InitializeNode (default) |
| pre_process | `PreProcessNode` (InputValidate) — S-1/S-2, redact endpoint/token/credential/PII, normalize declared baseline + observed state, extract `{query, declared_baseline, observed_state, drift_hint}` | user_input | validated_input, input_format, enriched_context | FunctionNode.execute |
| main | `DriftDiagnosisWorkflowGraphNode` (GraphNode) → inner workflow | validated_input | result, retrieval_hit_count | GraphNode |
| post_process | `PostProcessNode` (SafetyAndCitationGate) — S-3 strip sensitive payloads + citation completeness + mandatory advisory disclaimer + S-4 audit | result | formatted_output, disclaimer, audit_logged | FunctionNode.execute |
| finalize | response_metadata, total_time_ms | | (framework) | FinalizeNode (default) |

**Inner workflow (`DriftDiagnosisWorkflow` : BaseGraph):**

```
START → drift_intent_classify → versioned_kb_retrieve → drift_diagnosis_synthesize → END
```

| Inner node | Responsibility |
|---|---|
| DriftIntentClassify | **deterministic** classification of the drift dimension(s) of interest — prompt/version, tool-manifest, model-parameter, policy, deployment-environment |
| VersionedKBRetrieve | deterministic retrieval over the **versioned** config-drift / change-management diagnostic guidance KB; 0-hit → out-of-scope safe answer |
| DriftDiagnosisSynthesize | synthesise the advisory diagnosis map (per-dimension comparison method + interpretation + config-drift-vs-other-cause disambiguation) + verification checklist, grounded in the KB with source citation |

### Data Flow

```
START → initialize → pre_process → main(GraphNode → inner linear workflow) → post_process → finalize → END
                                     ↓ (retry, max 3)
                                   pre_process
```

Rejected / 0-hit input sets `error_code` + `retrieval_hit_count=0`; the retrieve node no-ops and
`drift_diagnosis_synthesize` emits the out-of-scope safe answer — no fabricated diagnosis.

### State Definition

| Field | Type | Purpose |
|-------|------|---------|
| validated_input | str (JSON) | `{query, declared_baseline, observed_state, drift_hint}` (redacted; no secrets/PII) |
| drift_intent | str (JSON) | `[{dimension, evidence}]` classified drift dimensions |
| retrieved_guidance / retrieval_hit_count | str/int | versioned KB matches / 0 → out-of-scope safe answer |
| diagnosis / checklist | str (JSON) | per-dimension diagnosis map / verification checklist |
| result / formatted_output | str (JSON) | inner package / final envelope |
| disclaimer / audit_logged | str/bool | mandatory advisory disclaimer + terminal audit |
| error_code / error_message | str | degraded path (SUCCESS + error_code, never status=ERROR) |

**State Constraints:** flat TypedDict; JSON strings for complex fields; **no endpoints / tokens /
credentials / PII persisted** (redacted at S-1/S-2); `enriched_context` is a JSON string (ADR-005).

## Framework Utilization

- [x] **GraphNode-in-main** (Cat 2 composition, criterion #9) — `error_strategy="propagate"`, `propagate_hitl=False`, **subgraph cached**
- [x] S-1 `required_trust_level=VERIFIED_EXTERNAL` on all FunctionNode subclasses (pre / post / inner)
- [x] S-2 `_extra_security_gate_input()` (pre) — **no-op hook: returns the state unchanged, never raises** (SDK 1.0.0). Injection markers + size cap are enforced deterministically **inside `execute()` (always runs)** as a **degraded `status=SUCCESS + error_code` (INJECTION_REJECTED / INPUT_TOO_LONG)** path — never `status=ERROR`, which would short-circuit `__call__` and skip main / post_process (disclaimer / redaction / audit)
- [x] S-3 `_extra_security_gate_output()` (post) — mandatory-disclaimer preservation; **may raise** (SDK 1.0.0)
- [x] S-4 `emit_trace_event()` in every `execute()` (drift dimension / counts only — no secrets/PII); terminal audit always fires

## Import Isolation Confirmation
- [x] No `agenticstar` SDK (Level 0) import — PB-4
- [x] Import targets: `framework/`, `langgraph`, and `src.` only

## Design Decision Record

| Decision | Chosen | Rationale |
|----------|--------|-----------|
| L1 base type | AgentBaseGraph | Fixed pipeline, no autonomous loop |
| Composition | **GraphNode-in-main + inner BaseGraph (cached)** | Cat 2 multi-step domain workflow |
| Inner topology | **Linear + per-node skip guards** | Conditional edges don't propagate across the subgraph boundary |
| Intent classify / retrieve / synthesize | **Deterministic — no LLM anywhere in the execution path** | Auditable dimension matching + versioned KB grounding; the diagnosis synthesis conditions on the caller's declared baseline / observed state (not a generative call, not a static lookup) |
| Advisory scope | **Read-only — no live inspection, no telemetry, no config change** | Diagnosis guidance only; final action is a human's |
| Rejection signalling | SUCCESS + error_code | Guarantees post_process S-3/S-4 always run (SDK 1.0.0) |

## Open Items (Stage ③ implementation MR)
- Node implementations + inner workflow graph (shipped in the implementation MR).
- Seeded, **versioned** `DriftGuidanceKB` (guidance across the 5 drift dimensions).
- Unit + integration + PB tests; coverage ≥ 80%.
- **Design commitment (Self-Assessment make-or-break):** `DriftDiagnosisSynthesize` must condition its
  output on versioned guidance + the declared baseline (not a static dictionary lookup); KB provenance
  and version-update process are recorded with each entry.
