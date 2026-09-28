"""CMN-C2-677 — deterministic domain services (no framework imports).

DriftGuidanceKB: a seeded, **versioned** knowledge base of AI-agent configuration-drift diagnostic
guidance across the five drift dimensions (prompt/version, tool-manifest, model-parameter, policy,
deployment-environment). Each entry carries a comparison method, an interpretation, a
config-drift-vs-other-cause disambiguation, verification steps, a source citation, and a KB version —
all sourced from public change-management / config-governance guidance (no secrets, endpoints or PII).

Dimension classification and retrieval are deterministic (keyword/tag scoring) and auditable; the
production LLM is reserved for phrasing the synthesised diagnosis map, never for the grounding itself.
"""

from __future__ import annotations

from typing import Any

# Canonical drift dimensions (job-to-be-done taxonomy).
DIMENSIONS = (
    "prompt_version",
    "tool_manifest",
    "model_parameter",
    "policy",
    "deployment_environment",
)

# Deterministic keyword → dimension map (lower-cased substring match).
_DIMENSION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "prompt_version": (
        "prompt",
        "system prompt",
        "template",
        "instruction",
        "few-shot",
        "プロンプト",
        "指示",
        "テンプレート",
    ),
    "tool_manifest": (
        "tool",
        "manifest",
        "function",
        "mcp",
        "tool schema",
        "capability",
        "ツール",
        "マニフェスト",
        "関数",
    ),
    "model_parameter": (
        "model",
        "temperature",
        "top_p",
        "top-p",
        "max_tokens",
        "parameter",
        "weights",
        "モデル",
        "温度",
        "パラメータ",
    ),
    "policy": (
        "policy",
        "guardrail",
        "trust level",
        "permission",
        "rbac",
        "rate limit",
        "ポリシー",
        "ガードレール",
        "権限",
        "レート",
    ),
    "deployment_environment": (
        "environment",
        "deployment",
        "region",
        "endpoint",
        "runtime",
        "container",
        "env var",
        "staging",
        "production",
        "環境",
        "デプロイ",
        "リージョン",
        "エンドポイント",
    ),
}

# ── seeded, versioned config-drift diagnostic guidance KB (public guidance) ────
# Each record: {dim_id, dimension, title, comparison_method, interpretation, disambiguation,
#               verification_steps[], tags[], source, kb_version}
KB: list[dict[str, Any]] = [
    {
        "dim_id": "DRIFT-PRM-001",
        "dimension": "prompt_version",
        "title": "System-prompt / instruction template drift",
        "comparison_method": "宣言 baseline の prompt/template hash・version tag と観測状態の実効 prompt を "
        "セクション単位で diff（system / few-shot / guardrail 節を分離して比較）。",
        "interpretation": "節単位の差分が挙動変化と時間的に相関する場合は prompt-version drift が濃厚。"
        "文言のみで出力分布が大きく動くなら prompt 起因、入力分布が変わっていれば data 起因。",
        "disambiguation": "config drift（prompt 版数の乖離）か: prompt hash/version が baseline と不一致 かつ "
        "model/parameter は不変 → prompt drift。model 版数も動いていれば model_parameter と併発を疑う。",
        "verification_steps": [
            "baseline prompt version tag と観測環境の実効 prompt version を突き合わせる",
            "system / few-shot / guardrail 節ごとに diff を取り、変更節を特定する",
            "変更節と挙動変化の発生時刻の相関を確認する",
        ],
        "tags": ["prompt", "template", "instruction", "few-shot", "system prompt", "プロンプト"],
        "source": "AI Agent Change-Management Guidance — Prompt Versioning (public)",
        "kb_version": "2026.06",
    },
    {
        "dim_id": "DRIFT-TOOL-002",
        "dimension": "tool_manifest",
        "title": "Tool / function manifest drift",
        "comparison_method": "宣言 baseline の tool manifest（tool 名・引数 schema・enable 状態・MCP endpoint 参照）と "
        "観測状態の有効ツール一覧を集合差分で比較。",
        "interpretation": "利用可能ツール集合や引数 schema の差分は tool-manifest drift。ツール呼び出し失敗の増加が "
        "manifest 差分と一致すれば config 起因、ツール実体側の障害なら operational 起因。",
        "disambiguation": "config drift（manifest 定義の乖離）か operational（ツール実体の障害）か: manifest は一致するが "
        "呼び出しが失敗 → operational。manifest 自体が baseline と不一致 → tool-manifest drift。",
        "verification_steps": [
            "baseline の有効ツール集合と観測環境の有効ツール集合を集合差分で比較する",
            "引数 schema（必須/型/enum）の差分を tool 単位で確認する",
            "ツール呼び出し失敗率の変化が manifest 差分と一致するか確認する",
        ],
        "tags": ["tool", "manifest", "function", "mcp", "capability", "schema", "ツール"],
        "source": "AI Agent Change-Management Guidance — Tool Manifest Governance (public)",
        "kb_version": "2026.06",
    },
    {
        "dim_id": "DRIFT-MODEL-003",
        "dimension": "model_parameter",
        "title": "Model / decoding-parameter drift",
        "comparison_method": "宣言 baseline の model id・version と decoding パラメータ（temperature / top_p / "
        "max_tokens 等）を観測状態と数値比較。",
        "interpretation": "temperature / top_p の乖離は出力の多様性・一貫性に直結。model version の乖離は "
        "能力そのものを変える。挙動変化がパラメータ差分と整合すれば model_parameter drift。",
        "disambiguation": "config drift（parameter/version 乖離）か model 本体の非決定性か: 同一入力・同一 seed で "
        "再現するなら parameter drift、seed 固定でも揺れるなら model 側非決定性（config drift ではない）。",
        "verification_steps": [
            "baseline と観測環境の model id / version を突き合わせる",
            "temperature / top_p / max_tokens 等の decoding パラメータを数値比較する",
            "同一入力・seed 固定で出力が再現するか（parameter 起因の切り分け）を確認する",
        ],
        "tags": ["model", "temperature", "top_p", "max_tokens", "parameter", "weights", "モデル"],
        "source": "AI Agent Change-Management Guidance — Model & Decoding Parameters (public)",
        "kb_version": "2026.06",
    },
    {
        "dim_id": "DRIFT-POL-004",
        "dimension": "policy",
        "title": "Policy / guardrail / trust-level drift",
        "comparison_method": "宣言 baseline の policy（trust level 要件・guardrail 設定・rate limit・権限スコープ）と "
        "観測状態の実効 policy を項目単位で比較。",
        "interpretation": "guardrail の緩和や trust level の低下は安全・拒否挙動を変える。拒否/許可の分布変化が "
        "policy 差分と一致すれば policy drift。",
        "disambiguation": "config drift（policy 設定の乖離）か入力分布変化か: policy 設定は一致するが拒否率が変化 → "
        "入力/データ起因。policy 設定自体が baseline と不一致 → policy drift。",
        "verification_steps": [
            "baseline の trust level 要件・guardrail・rate limit・権限スコープを観測値と比較する",
            "拒否/許可・エスカレーションの分布変化が policy 差分と相関するか確認する",
            "緩和方向（弱い trust level・広い権限）の drift を優先的にレビューする",
        ],
        "tags": ["policy", "guardrail", "trust level", "permission", "rbac", "rate limit", "ポリシー"],
        "source": "AI Agent Change-Management Guidance — Policy & Guardrail Governance (public)",
        "kb_version": "2026.06",
    },
    {
        "dim_id": "DRIFT-ENV-005",
        "dimension": "deployment_environment",
        "title": "Deployment-environment drift",
        "comparison_method": "宣言 baseline の deployment 記述（region・runtime/container version・env var・"
        "endpoint 参照の論理名）と観測環境を項目単位で比較（実値でなく差分の有無を確認）。",
        "interpretation": "runtime/依存 version や region の乖離は latency・可用性・数値再現性に影響。挙動変化が "
        "環境差分と一致すれば deployment-environment drift。",
        "disambiguation": "config drift（環境定義の乖離）か operational（一時的なインフラ障害）か: 環境定義は一致するが "
        "断続的に失敗 → operational。環境定義自体が baseline と不一致 → deployment-environment drift。",
        "verification_steps": [
            "baseline と観測環境の region・runtime/container version・依存 version を比較する",
            "env var / endpoint 参照の論理名の差分の有無を確認する（実 endpoint 値は扱わない）",
            "挙動変化が環境差分と一時的インフラ障害のどちらと相関するか確認する",
        ],
        "tags": ["environment", "deployment", "region", "endpoint", "runtime", "container", "env var", "環境"],
        "source": "AI Agent Change-Management Guidance — Deployment Environment Governance (public)",
        "kb_version": "2026.06",
    },
    {
        "dim_id": "DRIFT-XREF-006",
        "dimension": "cross_dimension",
        "title": "Config-drift vs model / data / operational cause disambiguation",
        "comparison_method": "各次元の baseline↔観測 差分マトリクスを作り、挙動変化イベントとの時間的相関で "
        "config drift か他要因かを切り分ける（複数次元の同時 drift を検出）。",
        "interpretation": "複数次元が同時に動いている場合は変更の重なりを疑う。どの次元差分も無いのに挙動が変化 → "
        "config drift ではなく model 非決定性 / data 分布変化 / operational 障害を優先調査。",
        "disambiguation": "config drift か否かの上位判定: 差分マトリクスに 1 つ以上の baseline 乖離があり挙動変化と "
        "相関 → config drift。乖離ゼロ → 非 config 要因（本テンプレのスコープ外、担当窓口へ）。",
        "verification_steps": [
            "5 次元それぞれの baseline↔観測 差分有無を一覧化する",
            "各差分と挙動変化イベントの時間的相関を確認する",
            "差分ゼロなら config drift 以外（model/data/operational）を切り分け先として明示する",
        ],
        "tags": ["drift", "cause", "config drift", "model", "data", "operational", "切り分け", "diagnosis"],
        "source": "AI Agent Change-Management Guidance — Drift Cause Disambiguation (public)",
        "kb_version": "2026.06",
    },
]


class DriftGuidanceKB:
    """Deterministic dimension classification + versioned-guidance retrieval over the seeded KB."""

    @staticmethod
    def classify_dimensions(query: str) -> list[dict[str, str]]:
        """Deterministic drift-dimension classification. Returns [] when nothing matches."""
        low = (query or "").lower()
        out: list[dict[str, str]] = []
        for dim in DIMENSIONS:
            for kw in _DIMENSION_KEYWORDS[dim]:
                if kw.lower() in low:
                    out.append({"dimension": dim, "evidence": kw})
                    break
        return out

    @staticmethod
    def retrieve(query: str, dimensions: list[str] | None, top_k: int = 4) -> list[dict[str, Any]]:
        """Keyword/tag- and dimension-scored retrieval over the versioned KB.

        [] when nothing matches (out-of-scope). The cross-dimension disambiguation entry is
        included whenever at least one concrete dimension matches (it grounds the cause split).
        """
        q = (query or "").lower()
        dim_set = set(dimensions or [])
        scored: list[tuple[int, dict[str, Any]]] = []
        for rec in KB:
            score = sum(2 for t in rec["tags"] if t.lower() in q)
            if rec["dimension"] in dim_set:
                score += 5
            if score:
                scored.append((score, rec))
        # If any concrete dimension matched, always ground the cause split with the x-ref entry.
        if scored and not any(s[1]["dim_id"] == "DRIFT-XREF-006" for s in scored):
            xref = next(r for r in KB if r["dim_id"] == "DRIFT-XREF-006")
            scored.append((1, xref))
        scored.sort(key=lambda x: (-x[0], x[1]["dim_id"]))
        out: list[dict[str, Any]] = []
        for score, rec in scored[:top_k]:
            out.append(
                {
                    "dim_id": rec["dim_id"],
                    "dimension": rec["dimension"],
                    "title": rec["title"],
                    "comparison_method": rec["comparison_method"],
                    "interpretation": rec["interpretation"],
                    "disambiguation": rec["disambiguation"],
                    "verification_steps": rec["verification_steps"],
                    "source": rec["source"],
                    "kb_version": rec["kb_version"],
                    "score": score,
                }
            )
        return out
