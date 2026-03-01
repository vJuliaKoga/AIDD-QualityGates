# -*- coding: utf-8 -*-
"""
---
meta:
    artifact_id: RES-TST-EVAL-001
    file: evaluate_planning_md_vs_yaml_v1.py
    author: '@juria.koga'
    source_type: human
    source: manual
    timestamp: '2026-03-01T13:54:00+09:00'
    content_hash: 32ac2b57db54ec314fefe3afb0ea4db34a89392fd88472294d8b5c4dcf3b6837
---
企画書（MD）と分割YAML（planning/yaml）を DeepEval で突合し、
チェックリスト（CONSIST / AIDD）に照らして評価するスクリプト。

重要:
- 分割YAML前提：すべてのチェックリスト項目が必須ではない
    -> 対象YAMLに該当セクションが無い場合は SKIP（適用外）として扱い、合否や平均に含めない
- 並列実行しない（AsyncConfigでrun_async=False、max_concurrent=1）
- timeoutしにくいように、YAML1ファイル=1評価（項目まとめ）にする
- コンソール出力は「以前のスクリプト」同等の集計表示を出す

突合対象（既定）:
- 企画書MD：artifacts/planning/PLN-PLN-FLW-002.md
- 構造化企画YAML：artifacts/planning/yaml/*.yaml
- チェックリスト：
    ① packs/checklists/CHK-PLN-CONSIST-001.yaml
    ② packs/checklists/CHK-PLN-AIDD-001.yaml

DeepEval（v3.8.x）準拠:
- evaluate() には run_async 等を直接渡さず、
    async_config / display_config / error_config を渡す
    (DeepEval Docs: End-to-End Evals / Datasets の evaluate 説明を参照)
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# ---- DeepEval imports（v3.8.x想定） ----
try:
    from deepeval import evaluate
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    from deepeval.evaluate import AsyncConfig, DisplayConfig, ErrorConfig
    from deepeval.test_run.test_run import TestRunResultDisplay
    from deepeval.metrics import FaithfulnessMetric, GEval
except Exception as e:
    raise SystemExit(
        "DeepEval import failed. `pip install deepeval==3.8.4` 等を確認してください。\n"
        f"Error: {e}"
    )

# =============================================================================
# パス定義（repo直下で動く前提）
# =============================================================================

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MD = ROOT / "artifacts" / "planning" / "PLN-PLN-FLW-002.md"
DEFAULT_YAML_DIR = ROOT / "artifacts" / "planning" / "yaml"
DEFAULT_CHK_CONSIST = ROOT / "packs" / "checklists" / "CHK-PLN-CONSIST-001.yaml"
DEFAULT_CHK_AIDD = ROOT / "packs" / "checklists" / "CHK-PLN-AIDD-001.yaml"
DEFAULT_OUT = ROOT / "output" / "deepeval" / "planning" / "eval_md_vs_yaml_v1.json"

# =============================================================================
# 評価設定（並列禁止 + timeout対策）
# =============================================================================

# API負荷軽減（必要なら増やす）
SLEEP_BETWEEN_CASES = 0.8

# DeepEval / LLM側で落ちたときの簡易リトライ
MAX_RETRY_PER_CASE = 2
RETRY_BACKOFF_SEC = 6

FAITHFULNESS_THRESHOLD = 0.5
GEVAL_THRESHOLD = 0.6

# DeepEvalの非同期・表示・エラー設定（v3.8.x）
DEEPEVAL_ASYNC_CONFIG = AsyncConfig(
    run_async=False,      # 並列実行しない（逐次）
    throttle_value=1.0,   # 呼び出し間隔（秒）※レート制限/timeout気味なら 2.0 以上に
    max_concurrent=1      # 念のため1固定

)
DEEPEVAL_DISPLAY_CONFIG = DisplayConfig(
    show_indicator=True,                 # 進捗インジケータ
    print_results=False,                 # DeepEvalの逐次出力を抑止（自前の集計printを使う）
    verbose_mode=None,                   # Noneなら各metricのverbose_modeを尊重
    display_option=TestRunResultDisplay.ALL,  # ALL / FAILING / PASSING
    file_output_dir=None
)
DEEPEVAL_ERROR_CONFIG = ErrorConfig(
    # 1ケース落ちても全体を止めず、スクリプト側で集計する
    ignore_errors=True,
    skip_on_missing_params=False
)

# =============================================================================
# データ構造
# =============================================================================


@dataclass
class ChecklistItem:
    """AIDDチェックリスト1項目"""
    item_id: str
    title: str
    risk: str = "MED"  # HIGH/MED/LOW
    # stage_required: {PLN:true/false, ...} を想定。無ければ「PLNで評価対象」とする
    stage_required_pln: Optional[bool] = None
    # evidence_hint（YAML: scope...など）を使って対象セクション推定に利用
    evidence_hint: List[str] = None


@dataclass
class PlanningYamlDoc:
    """分割YAML（企画1ファイル）"""
    path: Path
    meta: Dict[str, Any]
    # テンプレ上のトップレベルセクション（goal/scope/...）のうち、non-nullなもの
    present_sections: List[str]
    raw: Dict[str, Any]

    def to_compact_text(self) -> str:
        """LLM入力用に、YAMLをコンパクトに文字列化（長文化しすぎない）"""
        obj: Dict[str, Any] = {"meta": self.meta}
        for sec in self.present_sections:
            obj[sec] = self.raw.get(sec)
        for k in ["config_artifacts", "traceability"]:
            if k in self.raw and self.raw.get(k) is not None:
                obj[k] = self.raw.get(k)
        return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False).strip()

# =============================================================================
# ユーティリティ
# =============================================================================


def load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def load_yaml_safe(p: Path) -> Dict[str, Any]:
    return yaml.safe_load(load_text(p)) or {}


def ensure_paths_exist(md_path: Path, yaml_dir: Path, chk1: Path) -> None:
    if not md_path.exists():
        raise SystemExit(f"企画MDが見つかりません: {md_path}")
    if not yaml_dir.exists():
        raise SystemExit(f"企画YAMLディレクトリが見つかりません: {yaml_dir}")
    if not chk1.exists():
        raise SystemExit(f"チェックリスト（CONSIST）が見つかりません: {chk1}")


def detect_present_sections(doc: Dict[str, Any]) -> List[str]:
    """
    テンプレのトップレベルセクション群から、non-nullのものを抽出。
    分割YAML前提：だいたい1〜2セクションだけ埋まっている想定。
    """
    sections = [
        "goal", "problem", "scope", "constraints", "architecture", "workflow",
        "score_policy", "ai_quality_requirements", "inspection_design",
        "id_issuer", "integration", "traceability",
    ]
    present = []
    for s in sections:
        if s in doc and doc.get(s) is not None:
            present.append(s)
    return present


def load_planning_yaml_docs(yaml_dir: Path) -> List[PlanningYamlDoc]:
    docs: List[PlanningYamlDoc] = []
    for p in sorted(yaml_dir.glob("*.yaml")):
        data = load_yaml_safe(p)
        meta = data.get("meta") or {}
        present = detect_present_sections(data)
        docs.append(PlanningYamlDoc(path=p, meta=meta, present_sections=present, raw=data))
    if not docs:
        raise SystemExit(f"企画YAMLが見つかりません: {yaml_dir}")
    return docs


def summarize_consist_checklist(chk: Dict[str, Any]) -> str:
    """
    CHK-PLN-CONSIST-001.yaml は rules 形式なので、
    LLMに渡す「観点の一覧テキスト」にする。
    """
    c = chk.get("checklist") or {}
    parts = []
    parts.append(f"=== {c.get('id', '(no id)')} : {c.get('name', '(no name)')} ===")
    parts.append("以下は機械検証（G3前後）で満たすべき整合性ルールです。")
    for r in (c.get("rules") or []):
        rid = r.get("rule_id", "")
        sev = r.get("severity", "")
        title = r.get("title", "")
        parts.append(f"- [{sev}] {rid}: {title}")
    return "\n".join(parts)


def parse_aidd_checklist_items(chk: Dict[str, Any]) -> Tuple[str, List[ChecklistItem]]:
    """
    CHK-PLN-AIDD-001.yaml を想定して items を抽出。
    ファイル構造が多少違っても落ちないように緩く読む。
    """
    c = chk.get("checklist") or chk
    title = c.get("name") or c.get("title") or "AIDDチェックリスト"
    items_raw = (c.get("items") or [])
    items: List[ChecklistItem] = []

    for it in items_raw:
        if not isinstance(it, dict):
            continue
        item_id = it.get("item_id") or it.get("id") or ""
        t = it.get("title") or it.get("question") or ""
        risk = it.get("risk") or "MED"

        stage_required = it.get("stage_required") or {}
        stage_required_pln = None
        if isinstance(stage_required, dict) and "PLN" in stage_required:
            stage_required_pln = bool(stage_required.get("PLN"))

        evidence_hint = it.get("evidence_hint") or []
        if evidence_hint is None:
            evidence_hint = []

        items.append(
            ChecklistItem(
                item_id=str(item_id),
                title=str(t),
                risk=str(risk),
                stage_required_pln=stage_required_pln,
                evidence_hint=[str(x) for x in evidence_hint] if isinstance(evidence_hint, list) else [str(evidence_hint)],
            )
        )

    summary = f"=== AIDDチェックリスト（要約）: {title} / items={len(items)} ==="
    return summary, items


def is_item_applicable_to_doc(item: ChecklistItem, doc: PlanningYamlDoc) -> bool:
    """
    分割YAML前提の「適用可否」判定。
    - stage_required_pln が False なら企画段階ではSKIP
    - evidence_hint に 'YAML: scope' 等があれば、doc.present_sections と突合
      （ヒントが無い場合は「一般項目」として適用）
    """
    if item.stage_required_pln is False:
        return False

    hinted_sections = []
    for h in (item.evidence_hint or []):
        m = re.search(r"YAML:\s*([a-zA-Z0-9_.]+)", h)
        if m:
            root = m.group(1).split(".", 1)[0]
            hinted_sections.append(root)

    if hinted_sections:
        return any(sec in doc.present_sections for sec in hinted_sections)

    # ヒントが無い場合は広く適用（ただし doc が空なら意味ないのでSKIP）
    return len(doc.present_sections) > 0


def format_applicable_items_for_prompt(items: List[ChecklistItem], doc: PlanningYamlDoc) -> str:
    """LLMに渡す「このYAMLで評価するべきチェック項目」一覧テキスト。"""
    parts = []
    parts.append("=== 適用チェック項目（このYAMLで評価対象） ===")
    for it in items:
        parts.append(f"- {it.item_id} [{it.risk}] {it.title}")
    if not items:
        parts.append("(このYAMLに適用できる項目がありません。SKIP扱いにしてください。)")
    parts.append("")
    parts.append(f"※このYAMLで存在するセクション: {', '.join(doc.present_sections) if doc.present_sections else '(なし)'}")
    return "\n".join(parts)

# =============================================================================
# DeepEval メトリクス
# =============================================================================


def build_metrics() -> List[Any]:
    """
    1テストケース（=1 YAML）に適用するメトリクス。
    - Faithfulness: MDを根拠にできているか（幻覚/捏造検出）
    - GEval: チェックリスト観点での適合度（SKIP考慮の指示はcriteria内で行う）
    """
    metrics: List[Any] = []

    metrics.append(FaithfulnessMetric(threshold=FAITHFULNESS_THRESHOLD, include_reason=True))

    metrics.append(
        GEval(
            name="企画MD↔YAML突合（チェックリスト準拠）",
            criteria=(
                "あなたは上流工程QAのレビュアです。\n"
                "INPUTには「企画MD全文（もしくは抜粋）」「整合性ルール（CONSIST）」「適用チェック項目一覧」が含まれます。\n"
                "ACTUAL_OUTPUTには「評価対象の分割YAML（meta + 存在セクションのみ）」が含まれます。\n\n"
                "あなたの仕事:\n"
                "1) このYAMLが企画MDと矛盾していないか（根拠があるか）を確認\n"
                "2) 適用チェック項目（一覧）について、各項目ごとに YES/NO/HOLD を判定\n"
                "   - 分割YAMLのため『このYAMLに含まれないセクション』の項目は SKIP（適用外）\n"
                "   - SKIPは減点しない\n"
                "3) 最終的に0.0〜1.0で総合スコアを付ける（NOが多いほど低い）\n\n"
                "出力ルール:\n"
                "- 日本語で、次のJSONだけを出してください（余計な文章は出さない）\n"
                "{\n"
                '  "artifact_file": "...",\n'
                '  "applicable_section": ["scope", ...],\n'
                '  "results": [\n'
                '    {"item_id":"...", "judgement":"YES|NO|HOLD|SKIP", "reason":"...", "md_evidence":"(MD引用/要約)"}\n'
                "  ],\n"
                '  "overall_score": 0.0,\n'
                '  "notes": "改善点があれば簡潔に"\n'
                "}\n\n"
                "注意:\n"
                "- md_evidence は短い引用/要約で良い\n"
                "- 矛盾や捏造があれば NO として具体に指摘\n"
            ),
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.RETRIEVAL_CONTEXT,
            ],
            threshold=GEVAL_THRESHOLD,
        )
    )

    return metrics

# =============================================================================
# テストケース構築
# =============================================================================


def build_test_case(
    planning_md_text: str,
    consist_rules_text: str,
    aidd_summary: str,
    doc: PlanningYamlDoc,
    applicable_items: List[ChecklistItem],
) -> LLMTestCase:
    """
    1 YAML = 1 test case
    - INPUT: 企画MD（長すぎるとtimeoutの原因なので、必要なら短縮）
    - ACTUAL_OUTPUT: 対象YAML（存在セクションのみコンパクト化）
    """
    md_for_input = planning_md_text
    if len(md_for_input) > 12000:
        md_for_input = md_for_input[:12000] + "\n...(省略)"

    items_text = format_applicable_items_for_prompt(applicable_items, doc)

    input_text = (
        "=== 企画書（MD） ===\n"
        f"{md_for_input}\n\n"
        f"{consist_rules_text}\n\n"
        f"{aidd_summary}\n\n"
        f"{items_text}\n"
    )

    actual = (
        f"=== 対象YAML: {doc.path.name} ===\n"
        f"{doc.to_compact_text()}"
    )

    return LLMTestCase(
        input=input_text,
        actual_output=actual,
        retrieval_context=[md_for_input],
        additional_metadata={
            "yaml_file": doc.path.name,
            "artifact_id": str((doc.meta or {}).get("artifact_id", "")),
            "present_sections": doc.present_sections,
        },
    )

# =============================================================================
# 結果パース / 保存
# =============================================================================


def safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """GEvalのreasonがJSON想定だが崩れることがあるので緩く拾う。"""
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def serialize_metric(md: Any) -> Dict[str, Any]:
    return {
        "name": getattr(md, "name", None),
        "score": getattr(md, "score", None),
        "threshold": getattr(md, "threshold", None),
        "success": getattr(md, "success", None),
        "reason": getattr(md, "reason", None),
        "evaluation_model": getattr(md, "evaluation_model", None),
        "evaluation_cost": getattr(md, "evaluation_cost", None),
        "error": getattr(md, "error", None),
    }


def evaluate_one_case(tc: LLMTestCase, metrics: List[Any]) -> Any:
    """
    逐次実行 + 簡易リトライ（timeout/一時エラー対策）
    DeepEval v3.8.x: async_config / display_config / error_config を evaluate() に渡す
    """
    last_err = None
    for attempt in range(MAX_RETRY_PER_CASE + 1):
        try:
            res = evaluate(
                test_cases=[tc],
                metrics=metrics,
                identifier=f"planning_md_vs_yaml::{tc.additional_metadata.get('yaml_file', 'unknown')}",
                async_config=DEEPEVAL_ASYNC_CONFIG,
                display_config=DEEPEVAL_DISPLAY_CONFIG,
                error_config=DEEPEVAL_ERROR_CONFIG,
            )
            return res
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRY_PER_CASE:
                time.sleep(RETRY_BACKOFF_SEC * (attempt + 1))
                continue
            raise e
    raise last_err  # noqa


def build_console_summary(structured: Dict[str, Any], out_path: Path) -> None:
    """
    以前のスクリプトと同じ見た目のコンソール出力を行う
    """
    print()
    print("=== 評価完了 ===")
    print(f"テストケース数 : {structured['summary']['total_test_cases']}")
    print(f"合格 / 不合格  : {structured['summary']['passed']} / {structured['summary']['failed']}")
    print(f"合格率         : {structured['summary']['pass_rate'] * 100:.1f}%")
    print()
    print("メトリクス平均スコア:")
    for name, avg in structured["summary"]["metric_averages"].items():
        verdict = "OK" if avg >= GEVAL_THRESHOLD else "NG"
        print(f"  [{verdict}] {name}: {avg:.3f}")
    print()
    print(f"結果ファイル: {out_path}")


def main(
    md_path: Path = DEFAULT_MD,
    yaml_dir: Path = DEFAULT_YAML_DIR,
    chk_consist_path: Path = DEFAULT_CHK_CONSIST,
    chk_aidd_path: Path = DEFAULT_CHK_AIDD,
    out_path: Path = DEFAULT_OUT,
) -> None:
    ensure_paths_exist(md_path, yaml_dir, chk_consist_path)

    planning_md = load_text(md_path)

    chk_consist = load_yaml_safe(chk_consist_path)
    consist_rules_text = summarize_consist_checklist(chk_consist)

    aidd_summary = "=== AIDDチェックリスト（要約）: (not found) ==="
    aidd_items: List[ChecklistItem] = []
    if chk_aidd_path.exists():
        chk_aidd = load_yaml_safe(chk_aidd_path)
        aidd_summary, aidd_items = parse_aidd_checklist_items(chk_aidd)

    docs = load_planning_yaml_docs(yaml_dir)
    metrics = build_metrics()

    structured: Dict[str, Any] = {
        "meta": {
            "md_path": str(md_path),
            "yaml_dir": str(yaml_dir),
            "checklists": {
                "consist": str(chk_consist_path),
                "aidd": str(chk_aidd_path) if chk_aidd_path.exists() else None,
            },
            "timestamp": datetime.now().isoformat(),
        },
        "summary": {
            "yaml_files": len(docs),
            "evaluated": 0,
            "skipped": 0,
            # ここから下は最後に埋める（コンソール集計用）
            "total_test_cases": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "metric_averages": {},
        },
        "details": [],
    }

    # メトリクス平均算出用
    metric_scores: Dict[str, List[float]] = {}

    for doc in docs:
        # 分割YAMLなので「そのYAMLに適用できる項目だけ」評価する
        applicable = [it for it in aidd_items if is_item_applicable_to_doc(it, doc)]

        # 企画段階で適用項目がゼロ & present_sectionsもゼロならSKIP扱い
        if not doc.present_sections and not applicable:
            structured["summary"]["skipped"] += 1
            structured["details"].append({
                "yaml_file": doc.path.name,
                "artifact_id": (doc.meta or {}).get("artifact_id"),
                "present_sections": doc.present_sections,
                "status": "SKIP",
                "reason": "YAMLに評価対象セクションが存在しないため",
            })
            continue

        tc = build_test_case(
            planning_md_text=planning_md,
            consist_rules_text=consist_rules_text,
            aidd_summary=aidd_summary,
            doc=doc,
            applicable_items=applicable,
        )

        # 逐次評価（1件ずつ）
        res = evaluate_one_case(tc, metrics)

        # DeepEvalの返り値から test_result を取り出す
        test_results = getattr(res, "test_results", None)
        if test_results is None:
            # バージョン/環境差で返り値がlistのことがある
            test_results = res if isinstance(res, list) else []
        tr = test_results[0] if test_results else None

        tr_success = getattr(tr, "success", None) if tr else None
        metrics_data = getattr(tr, "metrics_data", []) if tr else []

        serialized_metrics = [serialize_metric(m) for m in (metrics_data or [])]

        # metric average 用に収集
        for m in (metrics_data or []):
            name = getattr(m, "name", None)
            sc = getattr(m, "score", None)
            if name and sc is not None:
                metric_scores.setdefault(str(name), []).append(float(sc))

        # GEvalのreason（JSON）を可能なら抽出
        ge_reason = None
        for m in (metrics_data or []):
            if getattr(m, "name", "") == "企画MD↔YAML突合（チェックリスト準拠）":
                ge_reason = getattr(m, "reason", None)
                break
        parsed = safe_parse_json(ge_reason) if isinstance(ge_reason, str) else None

        # overall_score は GEval JSONの overall_score を優先、無ければ metric.score
        overall_score = None
        if isinstance(parsed, dict) and "overall_score" in parsed:
            try:
                overall_score = float(parsed["overall_score"])
            except Exception:
                overall_score = None
        if overall_score is None:
            for m in (metrics_data or []):
                if getattr(m, "name", "") == "企画MD↔YAML突合（チェックリスト準拠）":
                    sc = getattr(m, "score", None)
                    if sc is not None:
                        overall_score = float(sc)
                    break

        structured["summary"]["evaluated"] += 1
        structured["details"].append({
            "yaml_file": doc.path.name,
            "artifact_id": (doc.meta or {}).get("artifact_id"),
            "present_sections": doc.present_sections,
            "status": "DONE",
            "tr_success": tr_success,
            "overall_score": overall_score,
            "metrics": serialized_metrics,
            "geval_json": parsed,
        })

        # 連続叩きを避ける（API負荷軽減）
        time.sleep(SLEEP_BETWEEN_CASES)

    # ---- コンソール集計（以前のスクリプト形式） ----
    done = [d for d in structured["details"] if d.get("status") == "DONE"]
    total_test_cases = len(done)

    passed = 0
    failed = 0
    for d in done:
        if d.get("tr_success") is True:
            passed += 1
        elif d.get("tr_success") is False:
            failed += 1
        else:
            # successが取れない場合は、GEvalのscoreで代替（最低限の判定）
            sc = d.get("overall_score")
            if isinstance(sc, (int, float)) and float(sc) >= GEVAL_THRESHOLD:
                passed += 1
            else:
                failed += 1

    metric_averages = {
        name: (sum(vals) / len(vals))
        for name, vals in metric_scores.items()
        if vals
    }

    structured["summary"].update({
        "total_test_cases": total_test_cases,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total_test_cases) if total_test_cases else 0.0,
        "metric_averages": {k: round(v, 3) for k, v in metric_averages.items()},
    })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")

    build_console_summary(structured, out_path)


if __name__ == "__main__":
    # 環境変数で差し替えできるように（必要なら）
    md = Path(os.getenv("PLN_MD_PATH", str(DEFAULT_MD)))
    yd = Path(os.getenv("PLN_YAML_DIR", str(DEFAULT_YAML_DIR)))
    c1 = Path(os.getenv("PLN_CHK_CONSIST", str(DEFAULT_CHK_CONSIST)))
    c2 = Path(os.getenv("PLN_CHK_AIDD", str(DEFAULT_CHK_AIDD)))
    out = Path(os.getenv("PLN_DEEPEVAL_OUT", str(DEFAULT_OUT)))
    main(md, yd, c1, c2, out)