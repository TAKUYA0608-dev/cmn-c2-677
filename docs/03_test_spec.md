# Test Specification — CMN-C2-677

## Test Strategy
- Coverage target: **80%+** (achieved 90%+, `--cov=src`)
- Test types: Unit (pre/post + inner nodes + services) / Unit (Cat 2 graph wiring) / Integration / Proof-of-Boundary

## Framework Compliance Tests (Mandatory)

| TC-ID | Test | Expected Result | Result |
|-------|------|----------------|--------|
| TC-01 | State contract: flat TypedDict | `State(AgentState)`, NotRequired primitives + JSON strings; no secrets/endpoints/PII | ✅ PASS |
| TC-02 | S-2 rejection is degraded (not ERROR) | injection / oversize → `execute()` returns **status=SUCCESS + error_code (INJECTION_REJECTED / INPUT_TOO_LONG)**; `_extra_security_gate_input` is a no-op that never raises; main / post_process (disclaimer / redaction / audit) still run | ✅ PASS |
| TC-03 | No JWT/Credential in `src/` | `gate-credential-scan`: 0 violations (redaction patterns are class-char-anchored) | ✅ PASS |
| TC-05 | S-4: no duplicate lifecycle events | only domain events emitted | ✅ PASS |
| TC-06 | S-2 `_security_gate_input()` not overridden | `@final`; only `_extra_*` extended | ✅ PASS |
| TC-07 | S-3 `_security_gate_output()` not overridden | `@final`; may raise via `_extra_*` | ✅ PASS |
| TC-08 | `required_trust_level` enforced | VERIFIED_EXTERNAL on all FunctionNode subclasses | ✅ PASS |
| TC-11 | S-4: ≥1 domain `emit_trace_event()` per `execute()` | emitted on every path | ✅ PASS |

## Proof-of-Boundary Tests (Mandatory)

| PB-ID | Boundary | Expected Result | Result |
|-------|----------|----------------|--------|
| PB-1 | `emit_trace_event()` fires from `shared.utils.audit_logger` | No silent failures | ✅ (real SDK on CI) |
| PB-2 | Post-invoke State is primitives only | No Pydantic/dataclass | ✅ PASS |
| PB-4 | Import isolation — no Level 0 imports | AST scan: 0 violations | ✅ PASS |
| PB-6 | Invoke order S-1 → S-4 → S-2 → execute → S-3 → S-4 | Order verified | ✅ (real SDK on CI; local-stub env-diff) |
| Composition | Cat 2 `GraphNode`-in-main wraps inner `BaseGraph` (cached) | gate-composition passes | ✅ (S-0 gate) |

## Business Logic Tests

| BL-ID | Test | Input | Expected Result | Result |
|-------|------|-------|----------------|--------|
| BL-01 | Prompt-version drift diagnosis | "system prompt が baseline と drift" | cited comparison/interpretation/disambiguation + checklist | ✅ PASS |
| BL-02 | Model-parameter drift diagnosis | "temperature が変わった" | model_parameter dimension diagnosed, cited | ✅ PASS |
| BL-03 | Multi-dimension classify | prompt + tool question | ≥2 dimensions classified + x-ref cause split included | ✅ PASS |
| BL-04 | Versioned citation completeness | any grounded diagnosis | every dimension cites source + kb_version | ✅ PASS |
| BL-05 | Out-of-scope | non-config question | `out_of_scope`, no citations, safe answer | ✅ PASS |
| BL-06 | Empty input | "   " | degraded SUCCESS, still audits | ✅ PASS |
| BL-07 | Endpoint/token/credential/PII redaction | baseline w/ URL + token + email | `[ENDPOINT/TOKEN/CREDENTIAL/PII-REDACTED]`, secret never persists | ✅ PASS |
| BL-08 | Mandatory advisory disclaimer | any output | S-3 gate blocks output missing it (advisory-only) | ✅ PASS |
| BL-09 | Grounded on caller inputs | baseline/observed provided | diagnosis `grounded_on` reflects supplied inputs (not a static lookup) | ✅ PASS |
| BL-10 | Injection / oversize reaches post via real `Graph().invoke()` | injection marker / >20k-char input | degraded SUCCESS + error_code; `PostProcessNode` runs (out-of-scope safe envelope + advisory disclaimer + S-4 audit); rejected body absent from output | ✅ PASS |

## Test Execution Summary
- Total: 30+ (unit nodes/services + graph wiring + integration + PB)
- Pass: all core unit/integration · Skip: server import (local stub env-diff) · env-diff: PB invoke-order (real SDK on CI)
- Coverage: **90%+** on the agent modules (nodes / graph / services / utils / schemas)
