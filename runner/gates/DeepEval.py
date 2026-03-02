# -*- coding: utf-8 -*-
"""
---
meta:
    artifact_id: TST-G4-EVAL-002
    file: g4_deepeval.py
    author: '@juria.koga'
    source_type: human
    source: manual
    timestamp: '2026-03-01T23:55:00+09:00'
    content_hash:41f3545ddbdff6149cef06938b27e2f47798a9e9e65ccd71c5e5bc7004fbd78d

---

G4 DeepEval Gate (NO Confident AI, NO warnings)

✅ 目的
- Confident AI を一切使わない（リンク表示・"No prompts logged" 警告を根絶）
- Faithfulness を「コア判定（スコア）」として使う（忠実性/ハルシネーション検知）
- Faithfulness NG/ERROR のケースだけ、短い explanation JSON を追加生成
- GEval は「参照整合 + CONSISTルール +（任意でAIDD項目）」で採点する
  ※AIDD項目が0件でも成立する設計（CONSIST-onlyで全落ちしない）
- judge モデルは AIDD_EVAL_MODEL（既定 gpt-5.2）に固定

✅ Confident AI 完全遮断（既定）
- DEEPEVAL_DISABLE_DOTENV=1 を deepeval import 前に立てて .env.local を読ませない
- DEEPEVAL_DISABLE_CONFIDENT=1 を立てる
- CONFIDENT_* をプロセス環境から削除（あっても使わない）

ENV（主なもの）
- AIDD_STAGE: PLN/REQ/...（既定 PLN）
- AIDD_REF_MODE: AUTO|MD|YAML（既定 AUTO）
- AIDD_MD_PATH: 参照MD
- AIDD_REF_YAML_DIR: 参照YAML dir（YAMLモード）
- AIDD_YAML_DIR: 評価対象YAML dir
- AIDD_CHECKLISTS: セミコロン区切り（CONSIST/AIDD混在OK）
- AIDD_OUT_ROOT: 出力ルート（既定 output/target）

- AIDD_EVAL_MODEL: judgeモデル名（既定 gpt-5.2）
- AIDD_ENABLE_CONFIDENT: 1 にすると Confident を有効化（既定 0 = 無効）

Faithfulness安定化
- AIDD_FAITHFULNESS_INCLUDE_REASON: 1 で reason 生成（既定 0）
- AIDD_FAITHFULNESS_TRUTHS_LIMIT: truths 抽出上限（既定 20）
- AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS: retrieval_context 文字上限（既定 4500）
- AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS: Faithfulness用 actual_output 文字上限（既定 3500）

Explanation（NG時のみ）
- AIDD_FAITHFULNESS_EXPLAIN_ON_FAIL: 1 でNG時 explanation 作成（既定 1）
- AIDD_FAITHFULNESS_EXPLAIN_MAX_FINDINGS: 最大指摘件数（既定 3）
- AIDD_FAITHFULNESS_EXPLAIN_MAX_WORDS: 全体語数上限（既定 280）

DeepEval
- DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE: 例 "900"（任意）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# =============================================================================
# Confident AI を "完全に" 使わない（既定）
# ※ deepeval import より前に設定する必要がある
# =============================================================================

AIDD_ENABLE_CONFIDENT = os.getenv("AIDD_ENABLE_CONFIDENT", "0").lower() in ("1", "true", "yes")

if not AIDD_ENABLE_CONFIDENT:
    os.environ.setdefault("DEEPEVAL_DISABLE_DOTENV", "1")
    os.environ.setdefault("DEEPEVAL_DISABLE_CONFIDENT", "1")
    for k in list(os.environ.keys()):
        if k.startswith("CONFIDENT_"):
            os.environ.pop(k, None)

# =============================================================================
# DeepEval import（env設定後に行うため noqa）
# =============================================================================

try:
    from deepeval import evaluate  # noqa: E402
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams  # noqa: E402
    from deepeval.evaluate import AsyncConfig, DisplayConfig, ErrorConfig  # noqa: E402
    from deepeval.test_run.test_run import TestRunResultDisplay  # noqa: E402
    from deepeval.metrics import FaithfulnessMetric, GEval  # noqa: E402
except Exception as e:
    raise SystemExit(
        "DeepEval import failed. `pip install deepeval==3.8.4` 等を確認してください。\n"
        f"Error: {e}"
    )

# =============================================================================
# Repo root
# =============================================================================


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur] + list(cur.parents):
        if (p / "packs").exists() and (p / "artifacts").exists():
            return p
    return Path.cwd().resolve()


ROOT = find_repo_root(Path(__file__))

# =============================================================================
# Defaults
# =============================================================================

DEFAULT_STAGE = "PLN"
DEFAULT_REF_MODE = "AUTO"  # AUTO|MD|YAML

DEFAULT_MD = ROOT / "artifacts" / "planning" / "PLN-PLN-FLW-002.md"
DEFAULT_REF_YAML_DIR = ROOT / "artifacts" / "planning" / "yaml"
DEFAULT_TARGET_YAML_DIR = ROOT / "artifacts" / "planning" / "yaml"

DEFAULT_OUT_ROOT = ROOT / "output" / "target"

DEFAULT_CHECKLISTS = [
    ROOT / "packs" / "checklists" / "CHK-PLN-CONSIST-001.yaml",
    ROOT / "packs" / "checklists" / "CHK-PLN-AIDD-001.yaml",
]

# =============================================================================
# Eval configs
# =============================================================================

SLEEP_BETWEEN_CASES = 2.0
MAX_RETRY_PER_CASE = 2
RETRY_BACKOFF_SEC = 6

FAITHFULNESS_THRESHOLD = 0.5
GEVAL_THRESHOLD = 0.6

EVAL_MODEL = os.getenv("AIDD_EVAL_MODEL", "gpt-5.2")

FAITHFULNESS_INCLUDE_REASON = os.getenv("AIDD_FAITHFULNESS_INCLUDE_REASON", "0").lower() in ("1", "true", "yes")
FAITHFULNESS_TRUTHS_LIMIT = int(os.getenv("AIDD_FAITHFULNESS_TRUTHS_LIMIT", "20"))
FAITHFULNESS_CONTEXT_MAX_CHARS = int(os.getenv("AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS", "4500"))
FAITHFULNESS_ACTUAL_MAX_CHARS = int(os.getenv("AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS", "3500"))

FAITHFULNESS_EXPLAIN_ON_FAIL = os.getenv("AIDD_FAITHFULNESS_EXPLAIN_ON_FAIL", "1").lower() in ("1", "true", "yes")
FAITHFULNESS_EXPLAIN_MAX_FINDINGS = int(os.getenv("AIDD_FAITHFULNESS_EXPLAIN_MAX_FINDINGS", "3"))
FAITHFULNESS_EXPLAIN_MAX_WORDS = int(os.getenv("AIDD_FAITHFULNESS_EXPLAIN_MAX_WORDS", "280"))

DEEPEVAL_ASYNC_CONFIG = AsyncConfig(run_async=False, throttle_value=2.0, max_concurrent=1)

DEEPEVAL_DISPLAY_CONFIG = DisplayConfig(
    show_indicator=True,
    print_results=False,
    verbose_mode=None,
    display_option=TestRunResultDisplay.ALL,
    file_output_dir=None,
)

DEEPEVAL_ERROR_CONFIG = ErrorConfig(ignore_errors=True, skip_on_missing_params=False)

# =============================================================================
# Data structures
# =============================================================================


@dataclass
class ChecklistItem:
    item_id: str
    title: str
    risk: str = "MED"
    stage_required: Optional[Dict[str, bool]] = None
    evidence_hint: List[str] = None


@dataclass
class ArtifactDoc:
    path: Path
    meta: Dict[str, Any]
    present_sections: List[str]
    raw: Dict[str, Any]

    def to_compact_text(self, include_sections: Optional[List[str]] = None) -> str:
        obj: Dict[str, Any] = {"meta": self.meta}
        secs = include_sections if include_sections is not None else self.present_sections
        for sec in secs:
            if sec in self.raw and self.raw.get(sec) is not None:
                obj[sec] = self.raw.get(sec)
        for k in ["config_artifacts", "traceability"]:
            if k in self.raw and self.raw.get(k) is not None:
                obj[k] = self.raw.get(k)
        return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False).strip()


# =============================================================================
# Output helpers (G3 style)
# =============================================================================


def sanitize_path_as_dirname(root: Path, p: Path) -> str:
    try:
        rel = p.resolve().relative_to(root.resolve())
        parts = list(rel.parts)
    except Exception:
        parts = list(p.parts)

    parts = [x for x in parts if x and not re.match(r"^[A-Za-z]:\\?$", x)]
    name = "_".join(parts)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "unknown_target"


def unique_output_path(out_dir: Path, base_name: str, ext: str = ".json") -> Path:
    p = out_dir / f"{base_name}{ext}"
    if not p.exists():
        return p
    i = 1
    while True:
        cand = out_dir / f"{base_name}_{i:02d}{ext}"
        if not cand.exists():
            return cand
        i += 1


def build_g3_style_output_path(repo_root: Path, output_root: Path, target_path: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    tgt = sanitize_path_as_dirname(repo_root, target_path)
    out_dir = output_root / tgt
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%m%d_%H%S")
    return unique_output_path(out_dir, ts, ".json")


# =============================================================================
# Utils
# =============================================================================


def load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def load_yaml_safe(p: Path) -> Dict[str, Any]:
    return yaml.safe_load(load_text(p)) or {}


def detect_present_sections(doc: Dict[str, Any]) -> List[str]:
    sections = [
        "goal", "problem", "scope", "constraints", "architecture", "workflow",
        "score_policy", "ai_quality_requirements", "inspection_design",
        "id_issuer", "integration", "traceability",
    ]
    return [s for s in sections if s in doc and doc.get(s) is not None]


def load_yaml_dir(yaml_dir: Path) -> List[ArtifactDoc]:
    docs: List[ArtifactDoc] = []
    for p in sorted(yaml_dir.glob("*.yaml")):
        data = load_yaml_safe(p)
        meta = data.get("meta") or {}
        present = detect_present_sections(data)
        docs.append(ArtifactDoc(path=p, meta=meta, present_sections=present, raw=data))
    if not docs:
        raise SystemExit(f"YAMLが見つかりません: {yaml_dir}")
    return docs


def ensure_paths_exist(ref_mode: str, md_path: Path, ref_yaml_dir: Path, target_yaml_dir: Path, checklists: List[Path]) -> None:
    for c in checklists:
        if not c.exists():
            raise SystemExit(f"チェックリストが見つかりません: {c}")

    if not target_yaml_dir.exists():
        raise SystemExit(f"評価対象YAMLディレクトリが見つかりません: {target_yaml_dir}")

    if ref_mode == "MD":
        if not md_path.exists():
            raise SystemExit(f"参照MDが見つかりません: {md_path}")
    elif ref_mode == "YAML":
        if not ref_yaml_dir.exists():
            raise SystemExit(f"参照YAMLディレクトリが見つかりません: {ref_yaml_dir}")
    else:
        raise SystemExit(f"ref_modeが不正です: {ref_mode}")


# =============================================================================
# Checklist loading
# =============================================================================


def summarize_consist_checklist(chk: Dict[str, Any]) -> str:
    c = chk.get("checklist") or {}
    if not c.get("rules"):
        return ""
    parts = []
    parts.append(f"=== {c.get('id', '(no id)')} : {c.get('name', '(no name)')} ===")
    parts.append("以下は整合性（CONSIST）ルールです。")
    for r in (c.get("rules") or []):
        rid = r.get("rule_id", "")
        sev = r.get("severity", "")
        title = r.get("title", "")
        parts.append(f"- [{sev}] {rid}: {title}")
    return "\n".join(parts)


def parse_aidd_checklist_items(chk: Dict[str, Any]) -> Tuple[str, List[ChecklistItem]]:
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
        stage_required = it.get("stage_required") or None
        evidence_hint = it.get("evidence_hint") or []
        if evidence_hint is None:
            evidence_hint = []
        items.append(ChecklistItem(
            item_id=str(item_id),
            title=str(t),
            risk=str(risk),
            stage_required=stage_required if isinstance(stage_required, dict) else None,
            evidence_hint=[str(x) for x in evidence_hint] if isinstance(evidence_hint, list) else [str(evidence_hint)],
        ))

    summary = f"=== AIDDチェックリスト（要約）: {title} / items={len(items)} ==="
    return summary, items


def load_checklists(paths: List[Path]) -> Tuple[str, str, List[ChecklistItem]]:
    consist_texts: List[str] = []
    aidd_items: List[ChecklistItem] = []
    aidd_titles: List[str] = []

    for p in paths:
        chk = load_yaml_safe(p)
        ctext = summarize_consist_checklist(chk)
        if ctext:
            consist_texts.append(ctext)

        summary, items = parse_aidd_checklist_items(chk)
        if items:
            aidd_titles.append(summary)
            aidd_items.extend(items)

    consist_rules_text = "\n\n".join([t for t in consist_texts if t.strip()]) or "(CONSISTルールなし)"
    aidd_summary = "\n".join(aidd_titles) if aidd_titles else "=== AIDDチェックリスト（要約）: (itemsなし) ==="
    return consist_rules_text, aidd_summary, aidd_items


# =============================================================================
# Applicability logic
# =============================================================================


def stage_required_for_item(item: ChecklistItem, stage: str) -> Optional[bool]:
    if not item.stage_required:
        return None
    if stage in item.stage_required:
        return bool(item.stage_required.get(stage))
    return None


def is_item_applicable_to_doc(item: ChecklistItem, doc: ArtifactDoc, stage: str) -> bool:
    sr = stage_required_for_item(item, stage)
    if sr is False:
        return False

    hinted_sections: List[str] = []
    for h in (item.evidence_hint or []):
        m = re.search(r"YAML:\s*([a-zA-Z0-9_.]+)", h)
        if m:
            root = m.group(1).split(".", 1)[0]
            hinted_sections.append(root)

    if hinted_sections:
        return any(sec in doc.present_sections for sec in hinted_sections)

    return len(doc.present_sections) > 0


def format_applicable_items_for_prompt(items: List[ChecklistItem], doc: ArtifactDoc, stage: str) -> str:
    parts: List[str] = []
    parts.append(f"=== 任意: AIDD適用チェック項目（{stage} / このYAMLで該当する場合のみ） ===")
    if items:
        for it in items:
            parts.append(f"- {it.item_id} [{it.risk}] {it.title}")
    else:
        parts.append("(該当するAIDD項目はありません。items判定は省略し、CONSIST/参照整合のみで評価してください。)")
    parts.append("")
    parts.append(f"※このYAMLで存在するセクション: {', '.join(doc.present_sections) if doc.present_sections else '(なし)'}")
    return "\n".join(parts)


# =============================================================================
# Reference context
# =============================================================================


def build_reference_context_md(stage: str, md_path: Path) -> str:
    return f"=== 参照MD（{stage}）: {md_path.name} ===\n{load_text(md_path)}"


def build_reference_context_yaml_for_doc(stage: str, ref_docs: List[ArtifactDoc], target_doc: ArtifactDoc) -> str:
    wanted = target_doc.present_sections[:]
    if not wanted:
        return f"=== 参照YAML（{stage}） ===\n(対象YAMLにセクションが無いため参照抽出なし)"

    chunks: List[str] = []
    chunks.append(f"=== 参照YAML（{stage}）: sections={', '.join(wanted)} ===")

    for sec in wanted:
        matched = [d for d in ref_docs if sec in d.present_sections][:3]
        if not matched:
            chunks.append(f"- (参照側に {sec} セクションがありません)")
            continue
        for d in matched:
            chunks.append(f"\n--- ref_file: {d.path.name} / section: {sec} ---")
            chunks.append(d.to_compact_text(include_sections=[sec]))

    return "\n".join(chunks)


def extract_reference_for_sections(reference_text: str, present_sections: List[str], max_chars: int) -> str:
    if not reference_text or max_chars <= 0:
        return ""
    if not present_sections:
        return reference_text[:max_chars]

    picks: List[str] = []
    text = reference_text

    for sec in present_sections:
        sec = (sec or "").strip()
        if not sec:
            continue
        m = re.search(rf"(?im)^(#+\s*.*{re.escape(sec)}.*)$", text)
        if m:
            start = max(0, m.start() - 200)
            end = min(len(text), m.start() + 1800)
            picks.append(text[start:end])

    if not picks:
        for sec in present_sections:
            sec = (sec or "").strip()
            if not sec:
                continue
            m = re.search(rf"(?im)^({re.escape(sec)}\s*:)\s*", text)
            if m:
                start = max(0, m.start() - 100)
                end = min(len(text), m.start() + 1800)
                picks.append(text[start:end])

    if not picks:
        return text[:max_chars]

    return "\n\n---\n\n".join(picks)[:max_chars]


# =============================================================================
# Metrics
# =============================================================================


def build_faithfulness_metric() -> Any:
    return FaithfulnessMetric(
        threshold=FAITHFULNESS_THRESHOLD,
        model=EVAL_MODEL,
        include_reason=FAITHFULNESS_INCLUDE_REASON,
        truths_extraction_limit=FAITHFULNESS_TRUTHS_LIMIT,
        penalize_ambiguous_claims=True,
    )


def build_geval_metric() -> Any:
    """
    重要: ここを「結果JSON生成」ではなく「整合性を採点」する設計に変更。
    items が無くても成立し、CONSIST-only で全落ちしない。
    """
    return GEval(
        name="参照/CONSIST整合スコア（GEval）",
        model=EVAL_MODEL,
        criteria=(
            "あなたは上流工程QAのレビュアです。\n"
            "INPUTには『参照（MDまたは参照YAML）』『CONSIST整合ルール』『任意: AIDD適用項目一覧』が含まれます。\n"
            "ACTUAL_OUTPUTは評価対象の分割YAML（meta + 存在セクションのみ）です。\n\n"
            "あなたの仕事:\n"
            "A) 参照とACTUAL_OUTPUTが矛盾していないか（根拠があるか）\n"
            "B) CONSISTルールに反していないか\n"
            "C) もし AIDD適用項目が提示されている場合は、その観点も軽く確認（無ければ省略でOK）\n\n"
            "採点:\n"
            "- 0.0〜1.0で overall_score を決める（重大な矛盾/ルール違反が多いほど低い）\n\n"
            "出力:\n"
            "- 次のJSONだけを出す（短く）。item_results は任意（無くてOK）。\n"
            "{\n"
            '  "overall_score": 0.0,\n'
            '  "top_issues": [\n'
            '     {"type":"REF|CONSIST|AIDD", "issue":"短文", "evidence":"短い根拠"}\n'
            "  ],\n"
            '  "notes": "改善点があれば一言"\n'
            "}\n"
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
        threshold=GEVAL_THRESHOLD,
    )


def build_faithfulness_explain_metric() -> Any:
    max_findings = max(1, FAITHFULNESS_EXPLAIN_MAX_FINDINGS)
    max_words = max(120, FAITHFULNESS_EXPLAIN_MAX_WORDS)
    return GEval(
        name="Faithfulness NG explanation",
        model=EVAL_MODEL,
        criteria=(
            "あなたはRAG忠実性の監査官です。\n"
            "RETRIEVAL_CONTEXTは短い参照です。\n"
            "ACTUAL_OUTPUTは生成結果（YAML）です。\n\n"
            "目的:\n"
            "- ACTUAL_OUTPUT内の『参照と矛盾/根拠不明』な記述を抽出し、短い理由と根拠を示す。\n\n"
            "出力は次のJSONのみ（日本語）。制約:\n"
            f"- findingsは最大{max_findings}件\n"
            "- claimは短く（1文）\n"
            "- reasonは各60文字以内\n"
            "- evidenceは参照からの短い抜粋 or 要約（各80文字以内）\n"
            f"- 全体で{max_words}語以内\n"
            "{\n"
            '  "summary":"一言で",\n'
            '  "findings":[\n'
            '     {"claim":"問題の記述(短く)", "reason":"なぜNGか", "evidence":"参照側の根拠"}\n'
            "  ]\n"
            "}\n"
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
        threshold=0.0,
    )


# =============================================================================
# Test case builder
# =============================================================================


def build_test_case(
    stage: str,
    reference_text: str,
    consist_rules_text: str,
    aidd_summary: str,
    target_doc: ArtifactDoc,
    applicable_items: List[ChecklistItem],
    *,
    actual_max_chars: Optional[int] = None,
) -> LLMTestCase:
    ref_for_geval = reference_text
    if len(ref_for_geval) > 12000:
        ref_for_geval = ref_for_geval[:12000] + "\n...(省略)"

    ref_for_faith = extract_reference_for_sections(reference_text, target_doc.present_sections, FAITHFULNESS_CONTEXT_MAX_CHARS)

    items_text = format_applicable_items_for_prompt(applicable_items, target_doc, stage)
    input_text = f"{ref_for_geval}\n\n{consist_rules_text}\n\n{aidd_summary}\n\n{items_text}\n"

    actual = f"=== 対象YAML: {target_doc.path.name} ===\n{target_doc.to_compact_text()}"
    if actual_max_chars is not None and actual_max_chars > 0 and len(actual) > actual_max_chars:
        actual = actual[:actual_max_chars] + "\n...(truncated for faithfulness)"

    return LLMTestCase(
        input=input_text,
        actual_output=actual,
        retrieval_context=[ref_for_faith],
        additional_metadata={
            "yaml_file": target_doc.path.name,
            "artifact_id": str((target_doc.meta or {}).get("artifact_id", "")),
            "present_sections": target_doc.present_sections,
            "stage": stage,
        },
    )


# =============================================================================
# JSON helpers
# =============================================================================


def safe_parse_json(text: Optional[str]) -> Optional[Dict[str, Any]]:
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


def _extract_first_metric_result(res: Any) -> Optional[Any]:
    tr_list = getattr(res, "test_results", None)
    if isinstance(tr_list, list) and tr_list:
        tr = tr_list[0]
        md_list = getattr(tr, "metrics_data", None)
        if isinstance(md_list, list) and md_list:
            return md_list[0]
    return None


# =============================================================================
# Evaluate wrapper
# =============================================================================


def evaluate_one_case(tc: LLMTestCase, metrics: List[Any]) -> Any:
    last_err = None
    for attempt in range(MAX_RETRY_PER_CASE + 1):
        try:
            return evaluate(
                test_cases=[tc],
                metrics=metrics,
                identifier=f"g4_deepeval::{tc.additional_metadata.get('yaml_file', 'unknown')}",
                async_config=DEEPEVAL_ASYNC_CONFIG,
                display_config=DEEPEVAL_DISPLAY_CONFIG,
                error_config=DEEPEVAL_ERROR_CONFIG,
                hyperparameters={
                    "Stage": tc.additional_metadata.get("stage"),
                    "Ref Mode": os.getenv("AIDD_REF_MODE", "AUTO"),
                    "Model": EVAL_MODEL,
                    "Faithfulness Threshold": FAITHFULNESS_THRESHOLD,
                    "Faithfulness Include Reason": FAITHFULNESS_INCLUDE_REASON,
                    "Faithfulness Truths Limit": FAITHFULNESS_TRUTHS_LIMIT,
                    "Faithfulness Ctx Max Chars": FAITHFULNESS_CONTEXT_MAX_CHARS,
                    "Faithfulness Actual Max Chars": FAITHFULNESS_ACTUAL_MAX_CHARS,
                    "Faith Explain On Fail": FAITHFULNESS_EXPLAIN_ON_FAIL,
                    "GEval Threshold": GEVAL_THRESHOLD,
                    "Per-task timeout(sec)": os.getenv("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE"),
                    "Script": "runner/gates/g4_deepeval.py",
                    "Confident Enabled": AIDD_ENABLE_CONFIDENT,
                },
            )
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRY_PER_CASE:
                time.sleep(RETRY_BACKOFF_SEC * (attempt + 1))
                continue
            raise e
    raise last_err  # noqa


def print_console_summary(structured: Dict[str, Any], out_path: Path) -> None:
    print()
    print("=== 評価完了 ===")
    print(f"テストケース数 : {structured['summary']['total_test_cases']}")
    print(f"合格 / 不合格  : {structured['summary']['passed']} / {structured['summary']['failed']}")
    print(f"合格率         : {structured['summary']['pass_rate'] * 100:.1f}%")
    print()
    print("メトリクス平均スコア:")
    for name, avg in structured["summary"]["metric_averages"].items():
        print(f"  {name}: {avg:.3f}")
    print()
    print(f"結果ファイル: {out_path}")


# =============================================================================
# CLI
# =============================================================================


def parse_checklists_arg(s: str) -> List[Path]:
    parts = [x.strip() for x in re.split(r"[;,\n]", s) if x.strip()]
    return [Path(x) for x in parts]


def resolve_paths(
    stage: str,
    ref_mode: str,
    md_path: Path,
    ref_yaml_dir: Path,
    target_yaml_dir: Path,
    checklists: List[Path],
    out_root: Path,
) -> Tuple[str, str, Path, Path, Path, List[Path], Path]:
    def rp(p: Path) -> Path:
        return (ROOT / p).resolve() if not p.is_absolute() else p.resolve()

    stage = stage.upper().strip()
    ref_mode = ref_mode.upper().strip()

    md_path = rp(md_path)
    ref_yaml_dir = rp(ref_yaml_dir)
    target_yaml_dir = rp(target_yaml_dir)
    out_root = rp(out_root)
    checklists = [rp(c) for c in checklists]

    if ref_mode == "AUTO":
        ref_mode = "MD" if md_path.exists() else "YAML"
    if ref_mode not in ("MD", "YAML"):
        raise SystemExit(f"AIDD_REF_MODE が不正です: {ref_mode} (AUTO|MD|YAML)")

    return stage, ref_mode, md_path, ref_yaml_dir, target_yaml_dir, checklists, out_root


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="G4 DeepEval Gate (NO Confident AI)")
    ap.add_argument("--stage", default=os.getenv("AIDD_STAGE", DEFAULT_STAGE))
    ap.add_argument("--ref_mode", default=os.getenv("AIDD_REF_MODE", DEFAULT_REF_MODE))
    ap.add_argument("--md", default=os.getenv("AIDD_MD_PATH", str(DEFAULT_MD)))
    ap.add_argument("--ref_yaml_dir", default=os.getenv("AIDD_REF_YAML_DIR", str(DEFAULT_REF_YAML_DIR)))
    ap.add_argument("--yaml_dir", default=os.getenv("AIDD_YAML_DIR", str(DEFAULT_TARGET_YAML_DIR)))
    ap.add_argument("--checklists", default=os.getenv("AIDD_CHECKLISTS", ";".join(str(p) for p in DEFAULT_CHECKLISTS)))
    ap.add_argument("--out_root", default=os.getenv("AIDD_OUT_ROOT", str(DEFAULT_OUT_ROOT)))
    return ap


# =============================================================================
# main
# =============================================================================


def main(
    stage: str,
    ref_mode: str,
    md_path: Path,
    ref_yaml_dir: Path,
    target_yaml_dir: Path,
    checklist_paths: List[Path],
    out_root: Path,
) -> int:
    ensure_paths_exist(ref_mode, md_path, ref_yaml_dir, target_yaml_dir, checklist_paths)

    consist_rules_text, aidd_summary, aidd_items = load_checklists(checklist_paths)
    target_docs = load_yaml_dir(target_yaml_dir)

    ref_docs: List[ArtifactDoc] = []
    ref_text_global: Optional[str] = None
    if ref_mode == "MD":
        ref_text_global = build_reference_context_md(stage, md_path)
    else:
        ref_docs = load_yaml_dir(ref_yaml_dir)

    faithfulness_metric = build_faithfulness_metric()
    geval_metric = build_geval_metric()
    explain_metric = build_faithfulness_explain_metric()

    out_path = build_g3_style_output_path(ROOT, out_root, target_yaml_dir)

    structured: Dict[str, Any] = {
        "gate": "G4_DEEPEVAL",
        "meta": {
            "artifact_id": "RES-TST-G4EVAL-001",
            "stage": stage,
            "ref_mode": ref_mode,
            "md_path": str(md_path) if ref_mode == "MD" else None,
            "ref_yaml_dir": str(ref_yaml_dir) if ref_mode == "YAML" else None,
            "yaml_dir": str(target_yaml_dir),
            "checklists": [str(p) for p in checklist_paths],
            "timestamp": datetime.now().isoformat(),
            "output_style": "g3_compatible",
            "output_root": str(out_root),
            "output_file": str(out_path),
            "eval_model": EVAL_MODEL,
            "confident_enabled": AIDD_ENABLE_CONFIDENT,
        },
        "summary": {
            "yaml_files": len(target_docs),
            "evaluated": 0,
            "skipped": 0,
            "total_test_cases": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "metric_averages": {},
        },
        "details": [],
    }

    metric_scores: Dict[str, List[float]] = {}

    for doc in target_docs:
        applicable = [it for it in aidd_items if is_item_applicable_to_doc(it, doc, stage)]

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

        reference_text = (ref_text_global or "") if ref_mode == "MD" else build_reference_context_yaml_for_doc(stage, ref_docs, doc)

        tc_geval = build_test_case(
            stage=stage,
            reference_text=reference_text,
            consist_rules_text=consist_rules_text,
            aidd_summary=aidd_summary,
            target_doc=doc,
            applicable_items=applicable,
            actual_max_chars=None,
        )
        tc_faith = build_test_case(
            stage=stage,
            reference_text=reference_text,
            consist_rules_text=consist_rules_text,
            aidd_summary=aidd_summary,
            target_doc=doc,
            applicable_items=applicable,
            actual_max_chars=FAITHFULNESS_ACTUAL_MAX_CHARS,
        )

        # Faithfulness (core)
        res_faith = evaluate_one_case(tc_faith, [faithfulness_metric])
        md_faith = _extract_first_metric_result(res_faith)
        faith_ser = serialize_metric(md_faith) if md_faith else {
            "name": "Faithfulness", "score": None, "threshold": FAITHFULNESS_THRESHOLD,
            "success": None, "reason": None, "evaluation_model": None, "evaluation_cost": None,
            "error": "No metrics_data returned",
        }
        faith_score = faith_ser.get("score")
        faith_error = faith_ser.get("error")
        faith_ok = (faith_error is None) and isinstance(faith_score, (int, float)) and float(faith_score) >= FAITHFULNESS_THRESHOLD

        # GEval (consistency score)
        res_geval = evaluate_one_case(tc_geval, [geval_metric])
        md_geval = _extract_first_metric_result(res_geval)
        geval_ser = serialize_metric(md_geval) if md_geval else {
            "name": "参照/CONSIST整合スコア（GEval）", "score": None, "threshold": GEVAL_THRESHOLD,
            "success": None, "reason": None, "evaluation_model": None, "evaluation_cost": None,
            "error": "No metrics_data returned",
        }

        parsed = safe_parse_json(geval_ser.get("reason") if isinstance(geval_ser.get("reason"), str) else None)

        # overall_score を優先して採用（無ければ metric.score）
        overall_score = None
        if isinstance(parsed, dict) and "overall_score" in parsed:
            try:
                overall_score = float(parsed["overall_score"])
            except Exception:
                overall_score = None
        if overall_score is None and isinstance(geval_ser.get("score"), (int, float)):
            overall_score = float(geval_ser["score"])

        geval_ok = isinstance(overall_score, (int, float)) and float(overall_score) >= GEVAL_THRESHOLD

        # Explanation only when Faithfulness NG/ERROR
        faith_explain_json = None
        if FAITHFULNESS_EXPLAIN_ON_FAIL and (not faith_ok):
            res_exp = evaluate_one_case(tc_faith, [explain_metric])
            md_exp = _extract_first_metric_result(res_exp)
            exp_reason = getattr(md_exp, "reason", None) if md_exp else None
            faith_explain_json = safe_parse_json(exp_reason if isinstance(exp_reason, str) else None)

        tr_success = bool(faith_ok and geval_ok)

        for ser in (faith_ser, geval_ser):
            name = ser.get("name")
            sc = ser.get("score")
            if name and isinstance(sc, (int, float)):
                metric_scores.setdefault(str(name), []).append(float(sc))

        structured["summary"]["evaluated"] += 1
        structured["details"].append({
            "yaml_file": doc.path.name,
            "artifact_id": (doc.meta or {}).get("artifact_id"),
            "present_sections": doc.present_sections,
            "status": "DONE",
            "tr_success": tr_success,
            "overall_score": overall_score,
            "faithfulness": {
                "score": faith_score,
                "threshold": FAITHFULNESS_THRESHOLD,
                "ok": faith_ok,
                "error": faith_error,
            },
            "metrics": [faith_ser, geval_ser],
            "geval_json": parsed,
            "faithfulness_explain": faith_explain_json,
        })

        time.sleep(SLEEP_BETWEEN_CASES)

    done = [d for d in structured["details"] if d.get("status") == "DONE"]
    total_test_cases = len(done)
    passed = sum(1 for d in done if d.get("tr_success") is True)
    failed = total_test_cases - passed

    metric_averages = {k: (sum(v) / len(v)) for k, v in metric_scores.items() if v}

    structured["summary"].update({
        "total_test_cases": total_test_cases,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total_test_cases) if total_test_cases else 0.0,
        "metric_averages": {k: round(v, 3) for k, v in metric_averages.items()},
    })

    out_path.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
    print_console_summary(structured, out_path)
    return 0


if __name__ == "__main__":
    ap = build_argparser()
    args = ap.parse_args()

    stage, ref_mode, md_path, ref_yaml_dir, target_yaml_dir, chk_paths, out_root = resolve_paths(
        stage=str(args.stage),
        ref_mode=str(args.ref_mode),
        md_path=Path(str(args.md)),
        ref_yaml_dir=Path(str(args.ref_yaml_dir)),
        target_yaml_dir=Path(str(args.yaml_dir)),
        checklists=parse_checklists_arg(str(args.checklists)),
        out_root=Path(str(args.out_root)),
    )

    raise SystemExit(main(stage, ref_mode, md_path, ref_yaml_dir, target_yaml_dir, chk_paths, out_root))