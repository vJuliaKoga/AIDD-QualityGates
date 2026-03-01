# -*- coding: utf-8 -*-
"""
---
meta:
    artifact_id: TST-G4-EVAL-001
    file: g4_deepeval.py
    author: '@juria.koga'
    source_type: human
    source: manual
    timestamp: '2026-03-01T14:23:00+09:00'
    content_hash: 0018c77888b7a9d70fbb56f1da536543aa102784d131ee4ef6db7c50ceefca5f
---

工程非依存 G4 DeepEval ゲート（参照: MD または YAML）

要件:
- 参照を MD / YAML で切替できる（PLNはMDでもOK、REQ以降はYAML参照でOK）
- 分割YAML前提：すべてのチェックリスト項目が必須ではない
    -> 適用可能項目だけを評価対象にし、不要観点で減点されない
    -> セクションが無い/適用項目が無い場合は SKIP（減点しない）
- 並列実行しない（AsyncConfig: run_async=False, max_concurrent=1）
- timeout回避：YAML 1ファイル = 1 test case（まとめ評価）＋ throttle/休止/リトライ
- 出力はG3互換：
    output/target/<sanitized_target>/<mmdd_hhss>.json
    ※無ければmkdir、同秒衝突は _01,_02…

ENV / 引数:
- AIDD_STAGE : PLN/REQ/BAS/DET...（既定 PLN）
- AIDD_REF_MODE : AUTO / MD / YAML（既定 AUTO）
- AIDD_MD_PATH : 参照MDパス（既定 artifacts/planning/PLN-PLN-FLW-002.md）
- AIDD_REF_YAML_DIR : 参照YAMLディレクトリ（既定 artifacts/planning/yaml）
- AIDD_YAML_DIR : 評価対象YAMLディレクトリ（既定 artifacts/planning/yaml）
- AIDD_CHECKLISTS : セミコロン区切りで複数指定
    例: packs/checklists/CHK-PLN-CONSIST-001.yaml;packs/checklists/CHK-PLN-AIDD-001.yaml
- AIDD_OUT_ROOT : 出力ルート（既定 output/target）

追加（judgeモデル固定）:
- AIDD_EVAL_MODEL : LLM-as-a-judge に使うモデル名（既定 gpt-5.2）
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

# ---- DeepEval imports（あなたの環境：deepeval 3.8.4前提） ----
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
# リポジトリルート推定（runner/gates 配下想定）
# =============================================================================

def find_repo_root(start: Path) -> Path:
    """
    runner/gates/ 配下でも packs/* 配下でも動くように、
    上に登りながら repo root を推定する。
    """
    cur = start.resolve()
    for p in [cur] + list(cur.parents):
        if (p / "packs").exists() and (p / "artifacts").exists():
            return p
    return Path.cwd().resolve()


ROOT = find_repo_root(Path(__file__))

# =============================================================================
# デフォルト（PLNを既定にしつつ、ENV/引数で差し替え可能）
# =============================================================================

DEFAULT_STAGE = "PLN"
DEFAULT_REF_MODE = "AUTO"  # AUTO|MD|YAML

DEFAULT_MD = ROOT / "artifacts" / "planning" / "PLN-PLN-FLW-002.md"
DEFAULT_REF_YAML_DIR = ROOT / "artifacts" / "planning" / "yaml"     # 参照側（企画）
DEFAULT_TARGET_YAML_DIR = ROOT / "artifacts" / "planning" / "yaml"  # 評価対象（既定は企画）

DEFAULT_OUT_ROOT = ROOT / "output" / "target"

DEFAULT_CHECKLISTS = [
    ROOT / "packs" / "checklists" / "CHK-PLN-CONSIST-001.yaml",
    ROOT / "packs" / "checklists" / "CHK-PLN-AIDD-001.yaml",
]

# =============================================================================
# 評価設定（並列禁止 + timeout対策）
# =============================================================================

SLEEP_BETWEEN_CASES = 2.0
MAX_RETRY_PER_CASE = 2
RETRY_BACKOFF_SEC = 6

FAITHFULNESS_THRESHOLD = 0.5
GEVAL_THRESHOLD = 0.6

# 評価に使うLLM（LLM-as-a-judge）
EVAL_MODEL = os.getenv("AIDD_EVAL_MODEL", "gpt-5.2")

# Faithfulnessの暴走（長文出力/多数truth抽出）対策
# - include_reason: Trueだと理由生成の追加呼び出しが走り、長文化で落ちやすいので既定はOFF
# - truths_extraction_limit: retrieval_contextが長いと truth/claim が爆発するので制限
# - retrieval_context自体も短縮（build_test_case内で section 近傍だけ抜粋）
FAITHFULNESS_INCLUDE_REASON = os.getenv("AIDD_FAITHFULNESS_INCLUDE_REASON", "0").lower() in ("1", "true", "yes")
FAITHFULNESS_TRUTHS_LIMIT = int(os.getenv("AIDD_FAITHFULNESS_TRUTHS_LIMIT", "20"))
FAITHFULNESS_CONTEXT_MAX_CHARS = int(os.getenv("AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS", "4500"))

DEEPEVAL_ASYNC_CONFIG = AsyncConfig(
    run_async=False,
    throttle_value=2.0,   # レート/timeoutが少なければ 1.0〜
    max_concurrent=1,
)

DEEPEVAL_DISPLAY_CONFIG = DisplayConfig(
    show_indicator=True,                      # 多いのが嫌なら False
    print_results=False,                      # 止まるようならDebugの為Trueにする
    verbose_mode=None,
    display_option=TestRunResultDisplay.ALL,
    file_output_dir=None,
)

DEEPEVAL_ERROR_CONFIG = ErrorConfig(
    ignore_errors=True,
    skip_on_missing_params=False,
)

# =============================================================================
# データ構造
# =============================================================================


@dataclass
class ChecklistItem:
    item_id: str
    title: str
    risk: str = "MED"  # HIGH/MED/LOW
    stage_required: Optional[Dict[str, bool]] = None  # {PLN:true, REQ:false...} 等
    evidence_hint: List[str] = None


@dataclass
class ArtifactDoc:
    """分割YAML（企画/要件/設計など）1ファイル"""
    path: Path
    meta: Dict[str, Any]
    present_sections: List[str]
    raw: Dict[str, Any]

    def to_compact_text(self, include_sections: Optional[List[str]] = None) -> str:
        """
        LLM入力用にコンパクトに文字列化
        - include_sections を指定したら、そのセクションだけ出す（timeout回避）
        """
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
# G3互換の出力ルール（output/target/<sanitized>/<mmdd_hhss>.json）
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
# 共通ユーティリティ
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


def ensure_paths_exist(
    ref_mode: str,
    md_path: Path,
    ref_yaml_dir: Path,
    target_yaml_dir: Path,
    checklists: List[Path],
) -> None:
    # チェックリストは常に必須
    for c in checklists:
        if not c.exists():
            raise SystemExit(f"チェックリストが見つかりません: {c}")

    if not target_yaml_dir.exists():
        raise SystemExit(f"評価対象YAMLディレクトリが見つかりません: {target_yaml_dir}")

    # 参照モード別に参照の存在確認
    if ref_mode == "MD":
        if not md_path.exists():
            raise SystemExit(f"参照MDが見つかりません: {md_path}")
    elif ref_mode == "YAML":
        if not ref_yaml_dir.exists():
            raise SystemExit(f"参照YAMLディレクトリが見つかりません: {ref_yaml_dir}")
    else:
        raise SystemExit(f"ref_modeが不正です: {ref_mode}")


# =============================================================================
# チェックリスト読み込み（複数対応）
# =============================================================================

def summarize_consist_checklist(chk: Dict[str, Any]) -> str:
    """
    rules 形式なら CONSIST としてテキスト化してLLMに渡す。
    """
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
    """
    items形式（AIDD）を抽出
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
    """
    複数チェックリストを読み込む。
    - CONSIST（rules）はまとめてテキスト化
    - AIDD（items）はまとめて配列化
    """
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
    aidd_summary = "\n".join(aidd_titles) if aidd_titles else "=== AIDDチェックリスト（要約）: (not found) ==="
    return consist_rules_text, aidd_summary, aidd_items


# =============================================================================
# 「不要観点で減点しない」ための適用判定
# =============================================================================

def stage_required_for_item(item: ChecklistItem, stage: str) -> Optional[bool]:
    """
    stage_required が無いなら「この工程で評価対象（True扱い）」にする。
    stage_required があれば、そのstageのboolを参照。
    """
    if not item.stage_required:
        return None
    if stage in item.stage_required:
        return bool(item.stage_required.get(stage))
    return None


def is_item_applicable_to_doc(item: ChecklistItem, doc: ArtifactDoc, stage: str) -> bool:
    """
    - stage_required[stage] が False → その工程では評価しない（SKIP）
    - evidence_hint に YAML: scope.xxx があれば、該当セクションが存在するYAMLだけ評価
    - ヒント無しは一般項目扱いだが、docが空ならSKIP
    """
    sr = stage_required_for_item(item, stage)
    if sr is False:
        return False

    hinted_sections = []
    for h in (item.evidence_hint or []):
        m = re.search(r"YAML:\s*([a-zA-Z0-9_.]+)", h)
        if m:
            root = m.group(1).split(".", 1)[0]
            hinted_sections.append(root)

    if hinted_sections:
        return any(sec in doc.present_sections for sec in hinted_sections)

    return len(doc.present_sections) > 0


def format_applicable_items_for_prompt(items: List[ChecklistItem], doc: ArtifactDoc, stage: str) -> str:
    parts = []
    parts.append(f"=== 適用チェック項目（{stage} / このYAMLで評価対象） ===")
    for it in items:
        parts.append(f"- {it.item_id} [{it.risk}] {it.title}")
    if not items:
        parts.append("(このYAMLに適用できる項目がありません。SKIP扱いにしてください。)")
    parts.append("")
    parts.append(f"※このYAMLで存在するセクション: {', '.join(doc.present_sections) if doc.present_sections else '(なし)'}")
    return "\n".join(parts)


# =============================================================================
# 参照コンテキストの組み立て（MD or YAML）
# =============================================================================

def build_reference_context_md(stage: str, md_path: Path) -> str:
    """
    参照がMDの場合：全文（長すぎる場合は後段で短縮）
    """
    return f"=== 参照MD（{stage}）: {md_path.name} ===\n{load_text(md_path)}"


def build_reference_context_yaml_for_doc(
    stage: str,
    ref_docs: List[ArtifactDoc],
    target_doc: ArtifactDoc,
) -> str:
    """
    参照がYAMLの場合：
    - target_doc の present_sections と一致するセクションを ref_docs から抽出して短くする
    - 参照側に該当セクションが複数あっても、全部詰めすぎないように先頭数件だけ
    """
    wanted = target_doc.present_sections[:]
    if not wanted:
        return f"=== 参照YAML（{stage}） ===\n(対象YAMLにセクションが無いため参照抽出なし)"

    chunks: List[str] = []
    chunks.append(f"=== 参照YAML（{stage}）: sections={', '.join(wanted)} ===")

    # セクションごとに一致する参照YAMLを集める
    for sec in wanted:
        matched = [d for d in ref_docs if sec in d.present_sections]
        # 多すぎ防止：最大3件まで（必要なら調整）
        matched = matched[:3]
        if not matched:
            chunks.append(f"- (参照側に {sec} セクションがありません)")
            continue
        for d in matched:
            chunks.append(f"\n--- ref_file: {d.path.name} / section: {sec} ---")
            chunks.append(d.to_compact_text(include_sections=[sec]))

    return "\n".join(chunks)


def extract_reference_for_sections(reference_text: str, present_sections: List[str], max_chars: int) -> str:
    """Faithfulness用に、参照テキストから『関係しそうな部分』だけを短く抜粋する。

    - MD参照: 見出し（# / ## / ###）に present_sections の語が含まれる箇所を優先
    - YAML参照（build_reference_context_yaml_for_docの出力など）: key行（goal: 等）周辺を優先
    - ヒットしない場合は先頭から max_chars
    """
    if not reference_text:
        return ""
    if max_chars <= 0:
        return ""
    if not present_sections:
        return reference_text[:max_chars]

    picks: List[str] = []
    text = reference_text

    # まずはMarkdown見出し（例: "## goal"）を狙う
    for sec in present_sections:
        sec = (sec or "").strip()
        if not sec:
            continue
        # 見出し行にsecが含まれる
        m = re.search(rf"(?im)^(#+\s*.*{re.escape(sec)}.*)$", text)
        if m:
            start = max(0, m.start() - 200)
            end = min(len(text), m.start() + 1800)
            picks.append(text[start:end])

    # Markdown見出しで拾えない場合、YAML key行（例: "goal:"）を狙う
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

    out = "\n\n---\n\n".join(picks)
    return out[:max_chars]


# =============================================================================
# DeepEval メトリクス
# =============================================================================

def build_explain_metric() -> Any:
    """
    FaithfulnessがNG/エラーのケースだけ、短文で原因を説明させるためのメトリクス。
    - core判定とは切り離し、reason生成の長文化でゲートが壊れないようにする
    - retrieval_context は build_test_case で短縮済みのものを使う
    """
    max_findings = max(1, int(os.getenv("AIDD_FAITHFULNESS_EXPLAIN_MAX_FINDINGS", "3")))
    max_words = max(120, int(os.getenv("AIDD_FAITHFULNESS_EXPLAIN_MAX_WORDS", "280")))

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
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        threshold=0.0,  # ゲートには使わない
    )


def build_metrics(enable_faithfulness: bool) -> List[Any]:
    """
    - Faithfulness は参照コンテキストがある場合に有効（MDでもYAML参照でも使える）
    - GEval は常に実行（チェックリスト判定＆SKIP非減点）
    """
    metrics: List[Any] = []

    if enable_faithfulness:
        # LengthFinishReasonError を避けて「まず完走」を優先
        # - include_reason=False: judgeの出力長を抑える
        # - truths_extraction_limit: retrieval_contextが長いと truth/claim が爆発するので制限
        metrics.append(
            FaithfulnessMetric(
                threshold=FAITHFULNESS_THRESHOLD,
                model=EVAL_MODEL,
                include_reason=FAITHFULNESS_INCLUDE_REASON,
                truths_extraction_limit=FAITHFULNESS_TRUTHS_LIMIT,
                penalize_ambiguous_claims=True,
            )
        )

    metrics.append(GEval(
        name="参照↔YAML突合（チェックリスト準拠）",
        model=EVAL_MODEL,
        criteria=(
            "あなたは上流工程QAのレビュアです。\n"
            "INPUTには「参照（MDまたは参照YAML）」「整合性ルール（CONSIST）」「適用チェック項目一覧」が含まれます。\n"
            "ACTUAL_OUTPUTには「評価対象の分割YAML（meta + 存在セクションのみ）」が含まれます。\n\n"
            "あなたの仕事:\n"
            "1) このYAMLが参照内容と矛盾していないか（根拠があるか）を確認\n"
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
            '    {"item_id":"...", "judgement":"YES|NO|HOLD|SKIP", "reason":"...", "evidence":"(参照の引用/要約)"}\n'
            "  ],\n"
            '  "overall_score": 0.0,\n'
            '  "notes": "改善点があれば簡潔に"\n'
            "}\n"
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        threshold=GEVAL_THRESHOLD,
    ))
    return metrics


# =============================================================================
# test case
# =============================================================================

def build_test_case(
    stage: str,
    reference_text: str,
    consist_rules_text: str,
    aidd_summary: str,
    target_doc: ArtifactDoc,
    applicable_items: List[ChecklistItem],
    *,
    faithfulness_actual_max_chars: Optional[int] = None,
) -> Tuple[LLMTestCase, LLMTestCase]:
    """
    1 YAML = 1 test case
    - INPUT: 参照 + CONSIST + AIDD要約 + 適用項目
    - ACTUAL_OUTPUT: 対象YAML（存在セクションのみ）
    - Faithfulness用だけ actual_output を短縮して claims 抽出の暴走を抑える
    """
    # GEval用（INPUT）は従来通り：多少長くても良い
    ref_for_geval = reference_text
    if len(ref_for_geval) > 12000:
        ref_for_geval = ref_for_geval[:12000] + "\n...(省略)"

    # Faithfulness用（retrieval_context）は短く・関係章だけに絞る
    ref_for_faith = extract_reference_for_sections(
        reference_text=reference_text,
        present_sections=target_doc.present_sections,
        max_chars=FAITHFULNESS_CONTEXT_MAX_CHARS,
    )

    items_text = format_applicable_items_for_prompt(applicable_items, target_doc, stage)

    input_text = (
        f"{ref_for_geval}\n\n"
        f"{consist_rules_text}\n\n"
        f"{aidd_summary}\n\n"
        f"{items_text}\n"
    )

    actual_full = f"=== 対象YAML: {target_doc.path.name} ===\n{target_doc.to_compact_text()}"
    actual_short = actual_full
    if faithfulness_actual_max_chars is not None and faithfulness_actual_max_chars > 0 and len(actual_short) > faithfulness_actual_max_chars:
        actual_short = actual_short[:faithfulness_actual_max_chars] + "\n...(truncated for faithfulness)"

    # GEval用（フル）
    tc_geval = LLMTestCase(
        input=input_text,
        actual_output=actual_full,
        retrieval_context=[ref_for_faith],
        additional_metadata={
            "yaml_file": target_doc.path.name,
            "artifact_id": str((target_doc.meta or {}).get("artifact_id", "")),
            "present_sections": target_doc.present_sections,
            "stage": stage,
        },
    )

    # Faithfulness用（短縮actual）
    tc_faith = LLMTestCase(
        input=input_text,
        actual_output=actual_short,
        retrieval_context=[ref_for_faith],
        additional_metadata={
            "yaml_file": target_doc.path.name,
            "artifact_id": str((target_doc.meta or {}).get("artifact_id", "")),
            "present_sections": target_doc.present_sections,
            "stage": stage,
        },
    )

    return tc_geval, tc_faith


# =============================================================================
# 実行/結果
# =============================================================================

def safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
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
                    "GEval Threshold": GEVAL_THRESHOLD,
                    "Per-task timeout(sec)": os.getenv("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE"),
                    "Script": "runner/gates/g4_deepeval.py",
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
        verdict = "OK" if avg >= GEVAL_THRESHOLD else "NG"
        print(f"  [{verdict}] {name}: {avg:.3f}")
    print()
    print(f"結果ファイル: {out_path}")


# =============================================================================
# CLI / ENV
# =============================================================================

def parse_checklists_arg(s: str) -> List[Path]:
    parts = [x.strip() for x in re.split(r"[;,\n]", s) if x.strip()]
    return [Path(x) for x in parts]


def resolve_paths(stage: str, ref_mode: str, md_path: Path, ref_yaml_dir: Path, target_yaml_dir: Path,
                  checklists: List[Path], out_root: Path) -> Tuple[str, str, Path, Path, Path, List[Path], Path]:
    def rp(p: Path) -> Path:
        return (ROOT / p).resolve() if not p.is_absolute() else p.resolve()

    stage = stage.upper().strip()
    ref_mode = ref_mode.upper().strip()

    md_path = rp(md_path)
    ref_yaml_dir = rp(ref_yaml_dir)
    target_yaml_dir = rp(target_yaml_dir)
    out_root = rp(out_root)
    checklists = [rp(c) for c in checklists]

    # AUTO：MDが存在するならMD参照、無ければYAML参照
    if ref_mode == "AUTO":
        ref_mode = "MD" if md_path.exists() else "YAML"
    if ref_mode not in ("MD", "YAML"):
        raise SystemExit(f"AIDD_REF_MODE が不正です: {ref_mode} (AUTO|MD|YAML)")

    return stage, ref_mode, md_path, ref_yaml_dir, target_yaml_dir, checklists, out_root


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="G4 DeepEval Gate (MD/YAML reference)")
    ap.add_argument("--stage", default=os.getenv("AIDD_STAGE", DEFAULT_STAGE), help="工程 (PLN/REQ/BAS/DET...)")
    ap.add_argument("--ref_mode", default=os.getenv("AIDD_REF_MODE", DEFAULT_REF_MODE), help="AUTO|MD|YAML")
    ap.add_argument("--md", default=os.getenv("AIDD_MD_PATH", str(DEFAULT_MD)), help="参照MDパス（MDモードで使用）")
    ap.add_argument("--ref_yaml_dir", default=os.getenv("AIDD_REF_YAML_DIR", str(DEFAULT_REF_YAML_DIR)),
                    help="参照YAMLディレクトリ（YAMLモードで使用）")
    ap.add_argument("--yaml_dir", default=os.getenv("AIDD_YAML_DIR", str(DEFAULT_TARGET_YAML_DIR)),
                    help="評価対象YAMLディレクトリ")
    ap.add_argument(
        "--checklists",
        default=os.getenv("AIDD_CHECKLISTS", ";".join(str(p) for p in DEFAULT_CHECKLISTS)),
        help="チェックリスト（セミコロン区切りで複数指定）",
    )
    ap.add_argument("--out_root", default=os.getenv("AIDD_OUT_ROOT", str(DEFAULT_OUT_ROOT)), help="出力ルート（G3互換）")
    return ap


# =============================================================================
# main
# =============================================================================

def main(stage: str, ref_mode: str, md_path: Path, ref_yaml_dir: Path, target_yaml_dir: Path,
         checklist_paths: List[Path], out_root: Path) -> int:
    ensure_paths_exist(ref_mode, md_path, ref_yaml_dir, target_yaml_dir, checklist_paths)

    # チェックリスト読み込み
    consist_rules_text, aidd_summary, aidd_items = load_checklists(checklist_paths)

    # 評価対象YAML読み込み
    target_docs = load_yaml_dir(target_yaml_dir)

    # 参照準備
    ref_docs: List[ArtifactDoc] = []
    ref_text_global: Optional[str] = None
    if ref_mode == "MD":
        ref_text_global = build_reference_context_md(stage, md_path)
    else:
        # YAML参照の場合は参照ディレクトリを読み込む（docごとに必要セクションだけ抽出して使う）
        ref_docs = load_yaml_dir(ref_yaml_dir)

    # メトリクス
    core_metrics = build_metrics(enable_faithfulness=True)
    explain_metric = build_explain_metric()

    # G3互換の出力先（ターゲットは評価対象ディレクトリ）
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
        # このYAMLに「適用できる項目だけ」評価する（不要観点で減点しない）
        applicable = [it for it in aidd_items if is_item_applicable_to_doc(it, doc, stage)]

        # セクションも適用項目も無ければSKIP（減点しない）
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

        # 参照コンテキスト（MDは共通、YAMLはdocごとに必要セクションだけ抽出）
        if ref_mode == "MD":
            reference_text = ref_text_global or ""
        else:
            reference_text = build_reference_context_yaml_for_doc(stage, ref_docs, doc)

        # test case（GEval用フル、Faithfulness用短縮actual）
        tc_geval, tc_faith = build_test_case(
            stage=stage,
            reference_text=reference_text,
            consist_rules_text=consist_rules_text,
            aidd_summary=aidd_summary,
            target_doc=doc,
            applicable_items=applicable,
            faithfulness_actual_max_chars=int(os.getenv("AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS", "3500")),
        )

        # core（Faithfulness+GEval）を評価（ここは tc_geval で回すが Faithfulness は tc_faith の方が安定）
        # まず Faithfulness（core）
        res_faith = evaluate_one_case(tc_faith, [m for m in core_metrics if getattr(m, "name", "") == "Faithfulness" or m.__class__.__name__ == "FaithfulnessMetric"])
        tr_faith = (getattr(res_faith, "test_results", None) or [None])[0]
        md_faith = (getattr(tr_faith, "metrics_data", None) or [None])[0]
        faith_ser = serialize_metric(md_faith) if md_faith else {
            "name": "Faithfulness", "score": None, "threshold": FAITHFULNESS_THRESHOLD,
            "success": None, "reason": None, "evaluation_model": None, "evaluation_cost": None,
            "error": "No metrics_data returned",
        }
        faith_score = faith_ser.get("score")
        faith_error = faith_ser.get("error")
        faith_ok = (faith_error is None) and isinstance(faith_score, (int, float)) and float(faith_score) >= FAITHFULNESS_THRESHOLD

        # 次に GEval（チェックリスト）
        res_geval = evaluate_one_case(tc_geval, [m for m in core_metrics if getattr(m, "name", "") == "参照↔YAML突合（チェックリスト準拠）"])
        tr_geval = (getattr(res_geval, "test_results", None) or [None])[0]
        md_geval = (getattr(tr_geval, "metrics_data", None) or [None])[0]
        geval_ser = serialize_metric(md_geval) if md_geval else {
            "name": "参照↔YAML突合（チェックリスト準拠）", "score": None, "threshold": GEVAL_THRESHOLD,
            "success": None, "reason": None, "evaluation_model": None, "evaluation_cost": None,
            "error": "No metrics_data returned",
        }

        ge_reason = geval_ser.get("reason")
        parsed = safe_parse_json(ge_reason) if isinstance(ge_reason, str) else None

        overall_score = None
        if isinstance(parsed, dict) and "overall_score" in parsed:
            try:
                overall_score = float(parsed["overall_score"])
            except Exception:
                overall_score = None
        if overall_score is None:
            sc = geval_ser.get("score")
            if isinstance(sc, (int, float)):
                overall_score = float(sc)

        # NG時だけ explanation を追加生成
        explain_json = None
        if (not faith_ok):
            res_exp = evaluate_one_case(tc_faith, [explain_metric])
            tr_exp = (getattr(res_exp, "test_results", None) or [None])[0]
            md_exp = (getattr(tr_exp, "metrics_data", None) or [None])[0]
            exp_reason = getattr(md_exp, "reason", None) if md_exp else None
            explain_json = safe_parse_json(exp_reason) if isinstance(exp_reason, str) else None

        # ここではゲートを「Faithfulness & GEval の両方」合格でPASSにしている（必要なら片方だけに変更可）
        tr_success = bool(faith_ok and isinstance(overall_score, (int, float)) and float(overall_score) >= GEVAL_THRESHOLD)

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
            "metrics": [faith_ser, geval_ser],
            "geval_json": parsed,
            "faithfulness_ok": faith_ok,
            "faithfulness_explain": explain_json,
        })

        time.sleep(SLEEP_BETWEEN_CASES)

    # コンソール用集計
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