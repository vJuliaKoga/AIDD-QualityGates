#!/usr/bin/env python3
"""
meta:
    artifact_id: TST-G4-EVAL-004
    file: g4_deepeval.py
    author: '@juria.koga'
    source_type: human
    source: manual
    timestamp: '2026-03-02T22:24:00+09:00'
    content_hash: 4b90c60c166df837cde6d0c84b4aede238070f68499a34f0bf0abbed83bde4a6
---
G4 DeepEval Gate — PLN Transform Quality Check
================================================
評価1 (Faithfulness): 構造化YAMLが参照ファイル（MD or YAML）に対して忠実か（ハルシネーション検出）
    - derived_from が今回の参照ファイルを含まない場合は、今回の精査スコープ外として Faithfulness を SKIP（自動PASS）
    - 品質保証補足事項ファイル（QA supplement）も自動PASS
    - FaithfulnessのReasonは非表示（タイムアウト回避）

評価2 (Checklist): 構造化YAMLがチェックリストのルールを満たすか（プログラムで検証）

出力: JSON + Allure互換結果ファイル

環境変数:
    AIDD_STAGE          : 対象工程 (例: PLN)
    AIDD_REF_MODE       : 参照モード (AUTO|MD|YAML)  ※AUTOは AIDD_FILE_PATH の拡張子で推定
    AIDD_FILE_PATH      : 参照ファイルパス（MDでもYAMLでも可）  ★推奨
    AIDD_MD_PATH        : 旧互換（AIDD_FILE_PATHが無い場合の参照MDパス）
    AIDD_YAML_DIR       : 評価対象YAMLディレクトリ
    AIDD_CHECKLISTS     : チェックリストYAMLパス
    AIDD_OUT_ROOT       : 出力ルートディレクトリ
    AIDD_EVAL_MODEL     : 使用モデル (例: gpt-5.2)
    AIDD_FAITHFULNESS_SKIP : Faithfulness評価から除外するファイル名（カンマ区切り）
                            "*" を指定すると全ファイルをスキップ（Checklist評価のみ実行）
                            例: "PLN-PLN-AIQUA-002.yaml" または "*"

補足:
- FaithfulnessのSKIP優先順位:
    1) AIDD_FAITHFULNESS_SKIP="*" → 全ファイル自動PASS
    2) AIDD_FAITHFULNESS_SKIP に明示指定 → そのファイル自動PASS
    3) derived_from が今回の参照ファイルを含まない → スコープ外として自動PASS
    4) QA補足事項（derived_from に今回参照以外の *.md/*.yaml が含まれる）→ 自動PASS
    5) それ以外 → FaithfulnessMetricで評価
"""

import os
import sys
import glob
import json
import uuid
import re
import time
import yaml
from pathlib import Path
from datetime import datetime

from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

# ─── Config ───────────────────────────────────────────────────────────────────

STAGE = os.environ.get("AIDD_STAGE", "PLN")

# 参照モード（AUTO|MD|YAML）
REF_MODE = os.environ.get("AIDD_REF_MODE", "AUTO").upper().strip()

# 参照ファイル（将来のMD→YAML切替に備えて統一）
# 互換: AIDD_FILE_PATH が無ければ AIDD_MD_PATH を使う
FILE_PATH = os.environ.get("AIDD_FILE_PATH", "").strip()
if not FILE_PATH:
    FILE_PATH = os.environ.get("AIDD_MD_PATH", "artifacts/planning/PLN-PLN-FLW-002.md").strip()

YAML_DIR = os.environ.get("AIDD_YAML_DIR", "artifacts/planning/yaml/v3")
CHECKLISTS = os.environ.get("AIDD_CHECKLISTS", "packs/checklists/CHK-PLN-CONSIST-001.yaml")
OUT_ROOT = os.environ.get("AIDD_OUT_ROOT", "output/G4/pln_transform")
EVAL_MODEL = os.environ.get("AIDD_EVAL_MODEL", "gpt-5.2")

# AIDD_FAITHFULNESS_SKIP: カンマ区切りのファイル名リスト、または "*"（全スキップ）
_skip_raw = os.environ.get("AIDD_FAITHFULNESS_SKIP", "")
FAITHFULNESS_SKIP_ALL = _skip_raw.strip() == "*"
FAITHFULNESS_SKIP_FILES = {s.strip() for s in _skip_raw.split(",") if s.strip() and s.strip() != "*"}

WARN_THRESHOLD = 0.70

# ─── File Loading ─────────────────────────────────────────────────────────────


def load_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_yaml_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_yaml_dir(yaml_dir: str) -> dict:
    """YAMLディレクトリの全ファイルを読み込む。{path: {"content": str, "data": dict}}"""
    result = {}
    for fp in sorted(glob.glob(f"{yaml_dir}/*.yaml")):
        content = load_text(fp)
        data = yaml.safe_load(content) or {}
        result[fp] = {"content": content, "data": data}
    return result


def infer_ref_mode(file_path: str, ref_mode: str) -> str:
    """AUTOの場合は拡張子で推定。"""
    if ref_mode in ("MD", "YAML"):
        return ref_mode
    ext = Path(file_path).suffix.lower()
    if ext == ".md":
        return "MD"
    if ext in (".yaml", ".yml"):
        return "YAML"
    # 変な拡張子ならMD扱いに倒す（最小驚き）
    return "MD"


def build_reference_content(file_path: str, ref_mode: str) -> str:
    """
    Faithfulnessの retrieval_context に渡す参照内容を生成。
    - MD: そのまま全文
    - YAML: YAMLを読み込んでダンプ（順序保持/見やすさ優先）
    """
    mode = infer_ref_mode(file_path, ref_mode)
    if mode == "MD":
        return load_text(file_path)
    data = load_yaml_file(file_path)
    # 参照YAMLは「文字列コンテキスト化」する（大きすぎる場合は必要に応じて外で短縮）
    return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)

# ─── derived_from based scope control ─────────────────────────────────────────


def _normalize_name(p: str) -> str:
    """derived_from に入る文字列はパス/URL/相対混在しうるので、末尾ファイル名だけで比較する。"""
    try:
        return Path(str(p)).name
    except Exception:
        return str(p)


def derived_from_list(yaml_data: dict) -> list[str]:
    df = yaml_data.get("derived_from") or []
    if isinstance(df, str):
        return [df]
    if isinstance(df, list):
        return [str(x) for x in df if x is not None]
    return []


def should_skip_faithfulness_by_derived_from(yaml_data: dict, main_ref_path: str) -> tuple[bool, str]:
    """
    要望:
    - derived_from に登録されている参照が「今回の参照ファイル」と違うなら Faithfulnessをスキップしたい。
    実装:
    - derived_from が空/無い → 判定不能なのでスキップしない（通常評価）
    - derived_from があり、そこに main_ref_name が含まれない → スコープ外としてSKIP（自動PASS）
    """
    df = derived_from_list(yaml_data)
    if not df:
        return False, ""

    main_name = _normalize_name(main_ref_path)
    df_names = {_normalize_name(x) for x in df}

    if main_name not in df_names:
        return True, f"[SKIP] derived_from に今回参照({main_name})が無いためスコープ外（derived_from={sorted(df_names)})"
    return False, ""


def is_qa_supplement(yaml_data: dict, main_ref_path: str) -> bool:
    """
    QA補足事項ファイル判定（工程非依存・汎用ロジック）。

    判定基準:
    - derived_from に、今回の主参照（AIDD_FILE_PATH）の「ファイル名」以外の *.md/*.yaml が含まれる。
        → それは主参照以外の補足資料（QA/チェックリスト等）由来の可能性が高いので Faithfulness は自動PASS。
    """
    main_name = _normalize_name(main_ref_path)
    for ref in derived_from_list(yaml_data):
        ref_name = _normalize_name(ref)
        if ref_name == main_name:
            continue
        if ref_name.lower().endswith((".md", ".yaml", ".yml")):
            return True
    return False

# ─── Evaluation 1: Faithfulness ───────────────────────────────────────────────


def _auto_pass_result(fname: str, fp: str, reason: str) -> dict:
    return {
        "test_name": f"Faithfulness :: {fname}",
        "category": "faithfulness",
        "file": fp,
        "score": 1.0,
        "passed": True,
        "status": "pass",
        "reason": reason,
        "duration_ms": 0,
    }


def eval_faithfulness(ref_content: str, yaml_files: dict, main_ref_path: str) -> list:
    """
    各YAMLについてFaithfulnessMetricで参照ファイル（MD/YAML）との整合性を評価する。

    SKIP優先順位:
        1. AIDD_FAITHFULNESS_SKIP="*"  → 全ファイル自動PASS（ref_contentは不要）
        2. AIDD_FAITHFULNESS_SKIP にファイル名が含まれる → そのファイルを自動PASS
        3. derived_from が今回参照を含まない → スコープ外として自動PASS
        4. QA補足事項ヒューリスティック → 自動PASS
        5. それ以外 → FaithfulnessMetric で評価

    include_reason=False でタイムアウトを回避。
    """
    results = []
    main_ref_name = Path(main_ref_path).name

    for fp, info in yaml_files.items():
        fname = Path(fp).name
        yaml_data = info["data"]
        yaml_content = info["content"]
        start = time.time()

        # 1. 全スキップ指定
        if FAITHFULNESS_SKIP_ALL:
            print(f"  [SKIP] {fname}  ← AIDD_FAITHFULNESS_SKIP=* により全スキップ")
            r = _auto_pass_result(fname, fp, "[SKIP] AIDD_FAITHFULNESS_SKIP=* により全スキップ（Checklist評価のみ）")
            r["duration_ms"] = int((time.time() - start) * 1000)
            results.append(r)
            continue

        # 2. 明示的除外ファイル
        if fname in FAITHFULNESS_SKIP_FILES:
            print(f"  [SKIP] {fname}  ← AIDD_FAITHFULNESS_SKIP に明示指定")
            r = _auto_pass_result(fname, fp, f"[SKIP] AIDD_FAITHFULNESS_SKIP に明示指定（{fname}）")
            r["duration_ms"] = int((time.time() - start) * 1000)
            results.append(r)
            continue

        # 3. derived_from スコープ外判定
        skip_df, msg_df = should_skip_faithfulness_by_derived_from(yaml_data, main_ref_path)
        if skip_df:
            print(f"  [SKIP] {fname}  ← derived_from に主参照({main_ref_name})が無い")
            r = _auto_pass_result(fname, fp, msg_df)
            r["duration_ms"] = int((time.time() - start) * 1000)
            results.append(r)
            continue

        # 4. QA補足事項ヒューリスティック
        if is_qa_supplement(yaml_data, main_ref_path):
            print(f"  [AUTO-PASS] {fname}  ← QA補足事項ファイル（ポリシーによりFaithfulness自動PASS）")
            r = _auto_pass_result(fname, fp, "[AUTO-PASS] 品質保証補足事項ファイルのためFaithfulness自動PASS（ポリシー準拠）")
            r["duration_ms"] = int((time.time() - start) * 1000)
            results.append(r)
            continue

        print(f"  [EVAL] Faithfulness: {fname} ...", end=" ", flush=True)
        try:
            metric = FaithfulnessMetric(
                threshold=WARN_THRESHOLD,
                model=EVAL_MODEL,
                include_reason=False,
                async_mode=False,
            )
            test_case = LLMTestCase(
                input=(
                    f"この構造化YAMLファイル（{fname}）は、参照ファイル（{main_ref_name}）の内容を"
                    "忠実に構造化したものですか？"
                    "参照に存在しない内容の創作（ハルシネーション）がないか、"
                    "また意味的妥当性があるかを評価してください。"
                ),
                actual_output=yaml_content,
                retrieval_context=[ref_content],
            )
            metric.measure(test_case)

            score = float(metric.score)
            passed = metric.is_successful()
            status = "pass" if passed else ("warn" if score >= 0.5 else "fail")

            print(f"score={score:.3f} → {status.upper()}")
            results.append({
                "test_name": f"Faithfulness :: {fname}",
                "category": "faithfulness",
                "file": fp,
                "score": round(score, 4),
                "passed": bool(passed),
                "status": status,
                "reason": "",  # Reason非表示（タイムアウト回避）
                "duration_ms": int((time.time() - start) * 1000),
            })

        except Exception as exc:
            print(f"ERROR: {exc}")
            results.append({
                "test_name": f"Faithfulness :: {fname}",
                "category": "faithfulness",
                "file": fp,
                "score": 0.0,
                "passed": False,
                "status": "error",
                "reason": str(exc),
                "duration_ms": int((time.time() - start) * 1000),
            })

    return results

# ─── Evaluation 2: Checklist (programmatic) ───────────────────────────────────


_META_REQUIRED_KEYS = {"artifact_id", "file", "author", "source_type", "timestamp", "content_hash"}
_TODO_PATTERN = re.compile(r"\b(TODO|TBD|PENDING)\b", re.IGNORECASE)


def _non_meta_yaml_str(yaml_data: dict) -> str:
    without_meta = {k: v for k, v in yaml_data.items() if k != "meta"}
    try:
        return yaml.dump(without_meta, allow_unicode=True, default_flow_style=False)
    except Exception:
        return ""


def _find_yaml_by_purpose(yaml_files: dict, purpose: str) -> dict:
    return {fp: info for fp, info in yaml_files.items() if purpose in Path(fp).name.upper()}


def check_rule(rule_id: str, yaml_files: dict, md_glob_pattern: str) -> dict:
    try:
        if rule_id == "PLN-CONS-001":
            md_files = glob.glob(md_glob_pattern)
            if md_files:
                names = [Path(f).name for f in md_files]
                return {"passed": True, "detail": f"{len(md_files)}件存在: {names}"}
            return {"passed": False, "detail": "PLN-PLN-*.md が見つかりません"}

        if rule_id == "PLN-CONS-002":
            if yaml_files:
                return {"passed": True, "detail": f"{len(yaml_files)}件のYAMLが存在します"}
            return {"passed": False, "detail": "PLN-PLN-*.yaml が見つかりません"}

        if rule_id == "PLN-CONS-010":
            return {"passed": True, "detail": "企画書本文MDはプレーンMarkdown形式（YAML frontmatterなし）のためスキップ"}

        if rule_id == "PLN-CONS-011":
            failures = []
            for fp, info in yaml_files.items():
                meta = info["data"].get("meta") or {}
                if not meta:
                    failures.append(f"{Path(fp).name}: metaセクションなし")
                    continue
                missing = _META_REQUIRED_KEYS - set(meta.keys())
                if missing:
                    failures.append(f"{Path(fp).name}: 欠如キー={sorted(missing)}")
            if failures:
                return {"passed": False, "detail": " / ".join(failures)}
            return {"passed": True, "detail": f"全{len(yaml_files)}件でmeta必須キー確認済み"}

        if rule_id == "PLN-CONS-020":
            failures = []
            for fp, info in yaml_files.items():
                actual = Path(fp).name
                declared = info["data"].get("meta", {}).get("file", "")
                if declared != actual:
                    failures.append(f"{actual}: meta.file='{declared}'")
            if failures:
                return {"passed": False, "detail": "不一致: " + " / ".join(failures)}
            return {"passed": True, "detail": "全YAMLでmeta.fileと実ファイル名が一致"}

        if rule_id == "PLN-CONS-030":
            bad = []
            for fp, info in yaml_files.items():
                h = str(info["data"].get("meta", {}).get("content_hash", "") or "")
                if h.upper() in ("PENDING", "TODO", ""):
                    bad.append(f"{Path(fp).name}: content_hash='{h}'")
            if bad:
                return {"passed": False, "detail": "未設定: " + " / ".join(bad)}
            return {"passed": True, "detail": "全YAMLのcontent_hashが設定済み"}

        if rule_id == "PLN-CONS-040":
            failures = []
            for fp, info in yaml_files.items():
                stem = Path(fp).stem
                artifact_id = info["data"].get("meta", {}).get("artifact_id", "") or ""
                if artifact_id and artifact_id not in stem:
                    failures.append(f"{Path(fp).name}: artifact_id='{artifact_id}'がステムに含まれない")
            if failures:
                return {"passed": False, "detail": "不一致: " + " / ".join(failures)}
            return {"passed": True, "detail": "全YAMLのファイル名にartifact_idが含まれる"}

        if rule_id == "PLN-CONS-060":
            violations = []
            for fp, info in yaml_files.items():
                non_meta = _non_meta_yaml_str(info["data"])
                found = set(_TODO_PATTERN.findall(non_meta))
                if found:
                    violations.append(f"{Path(fp).name}: {found}")
            if violations:
                return {"passed": False, "detail": "TODO/TBD/PENDING残存: " + " / ".join(violations)}
            return {"passed": True, "detail": "meta以外にTODO/TBD/PENDINGなし"}

        if rule_id == "PLN-CONS-100":
            required = ["primary_goal", "success_criteria", "scope_in", "scope_out", "abort_conditions"]
            goal_files = _find_yaml_by_purpose(yaml_files, "GOAL")
            if not goal_files:
                return {"passed": False, "detail": "PLN-PLN-GOAL-*.yaml が見つかりません"}
            failures = []
            for fp, info in goal_files.items():
                goal = info["data"].get("goal") or {}
                missing = [k for k in required if not goal.get(k)]
                if missing:
                    failures.append(f"{Path(fp).name}: goal.{missing}が欠如または空")
            if failures:
                return {"passed": False, "detail": " / ".join(failures)}
            return {"passed": True, "detail": f"GOAL YAML必須キー確認済み: {[Path(fp).name for fp in goal_files]}"}

        if rule_id == "PLN-CONS-110":
            scope_files = _find_yaml_by_purpose(yaml_files, "SCOPE")
            if not scope_files:
                return {"passed": False, "detail": "PLN-PLN-SCOPE-*.yaml が見つかりません"}
            failures = []
            for fp, info in scope_files.items():
                scope = info["data"].get("scope") or {}
                if not scope.get("scope_in"):
                    failures.append(f"{Path(fp).name}: scope.scope_in が欠如")
                if not scope.get("scope_out"):
                    failures.append(f"{Path(fp).name}: scope.scope_out が欠如")
                terminology = scope.get("terminology") or {}
                glossary = terminology.get("glossary") or []
                if not glossary:
                    failures.append(f"{Path(fp).name}: scope.terminology.glossary が空または欠如")
            if failures:
                return {"passed": False, "detail": " / ".join(failures)}
            return {"passed": True, "detail": f"SCOPE YAML必須キー確認済み: {[Path(fp).name for fp in scope_files]}"}

        return {"passed": True, "detail": f"ルール {rule_id} は自動チェック対象外（スキップ）"}

    except Exception as exc:
        return {"passed": False, "detail": f"チェック実行エラー: {exc}"}


def eval_checklist(yaml_files: dict, checklist_data: dict) -> list:
    checklist = checklist_data.get("checklist", {})
    rules = checklist.get("rules", [])
    scope = checklist.get("scope", {})
    md_glob_base = scope.get("planning_md_glob", "artifacts/planning/PLN-PLN-*.md")

    results = []
    for rule in rules:
        rule_id = rule["rule_id"]
        rule_title = rule["title"]
        severity = rule.get("severity", "warn")

        label = rule_title[:55] + ("..." if len(rule_title) > 55 else "")
        print(f"  [CHECK] {rule_id}: {label}", end=" ", flush=True)
        start = time.time()

        chk = check_rule(rule_id, yaml_files, md_glob_base)
        passed = chk["passed"]
        detail = chk["detail"]
        score = 1.0 if passed else 0.0
        status = "pass" if passed else ("fail" if severity == "fail" else "warn")

        print(f"→ {'PASS' if passed else 'FAIL'}")
        results.append({
            "test_name": f"Checklist :: {rule_id}",
            "category": "checklist",
            "rule_id": rule_id,
            "rule_title": rule_title,
            "severity": severity,
            "score": score,
            "passed": passed,
            "status": status,
            "reason": detail,
            "duration_ms": int((time.time() - start) * 1000),
        })

    return results

# ─── Output ───────────────────────────────────────────────────────────────────


def _summary(results: list) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    scores = [r["score"] for r in results]
    avg = sum(scores) / len(scores) if scores else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "avg_score": round(avg, 4),
        "warning": avg < WARN_THRESHOLD,
    }


def _make_out_paths(out_root: str) -> tuple[Path, Path]:
    yaml_subdir = YAML_DIR.replace("\\", "_").replace("/", "_").strip("_")
    ts_fname = datetime.now().strftime("%m%d_%H%M") + ".json"
    base_dir = Path(out_root) / yaml_subdir
    return base_dir / ts_fname, base_dir / "allure-results"


def write_results(all_results: list, out_root: str) -> dict:
    json_path, allure_dir = _make_out_paths(out_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    faith_results = [r for r in all_results if r["category"] == "faithfulness"]
    check_results = [r for r in all_results if r["category"] == "checklist"]
    overall_pass = all(r["passed"] for r in all_results)

    output = {
        "gate_id": "G4",
        "stage": STAGE,
        "model": EVAL_MODEL,
        "timestamp": datetime.now().isoformat(),
        "inputs": {
            "file_path": FILE_PATH,
            "ref_mode": infer_ref_mode(FILE_PATH, REF_MODE),
            "yaml_dir": YAML_DIR,
            "checklist": CHECKLISTS,
        },
        "summary": {
            "total": len(all_results),
            "passed": sum(1 for r in all_results if r["passed"]),
            "failed": sum(1 for r in all_results if not r["passed"]),
            "overall_status": "pass" if overall_pass else "fail",
            "faithfulness": _summary(faith_results),
            "checklist": _summary(check_results),
        },
        "results": all_results,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    allure_dir.mkdir(parents=True, exist_ok=True)

    ts_ms = int(time.time() * 1000)
    for r in all_results:
        allure_status = "passed" if r["passed"] else ("broken" if r["status"] == "error" else "failed")
        ar = {
            "uuid": str(uuid.uuid4()),
            "name": r["test_name"],
            "status": allure_status,
            "stage": "finished",
            "start": ts_ms,
            "stop": ts_ms + r.get("duration_ms", 0),
            "labels": [
                {"name": "suite", "value": f"G4 {STAGE} Transform"},
                {"name": "feature", "value": r["category"].capitalize()},
                {"name": "severity", "value": r.get("severity", "normal")},
                {"name": "tag", "value": "G4"},
            ],
            "parameters": [
                {"name": "score", "value": str(r["score"])},
                {"name": "model", "value": EVAL_MODEL},
                {"name": "status", "value": r["status"]},
            ],
            "description": r.get("reason", ""),
            "steps": [],
        }
        allure_path = allure_dir / f"{ar['uuid']}-result.json"
        with open(allure_path, "w", encoding="utf-8") as f:
            json.dump(ar, f, ensure_ascii=False, indent=2)

    output["_meta"] = {"json_path": str(json_path), "allure_dir": str(allure_dir)}
    return output

# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    resolved_mode = infer_ref_mode(FILE_PATH, REF_MODE)
    skip_label = ("全スキップ(*)" if FAITHFULNESS_SKIP_ALL else (f"除外={FAITHFULNESS_SKIP_FILES}" if FAITHFULNESS_SKIP_FILES else "なし"))

    print(f"\n{'=' * 64}")
    print(f"[G4] DeepEval Gate — {STAGE} Transform Quality Check")
    print(f"[G4] Model : {EVAL_MODEL}")
    print(f"[G4] REF   : {FILE_PATH} (mode={resolved_mode})")
    print(f"[G4] YAMLs : {YAML_DIR}")
    print(f"[G4] CL    : {CHECKLISTS}")
    print(f"[G4] Skip  : {skip_label}")
    print(f"{'=' * 64}\n")

    # Faithfulness全スキップ時は参照ロード不要
    if FAITHFULNESS_SKIP_ALL:
        ref_content = ""
        print("[G4] Faithfulness全スキップ: 参照ロードをスキップ\n")
    else:
        ref_content = build_reference_content(FILE_PATH, REF_MODE)

    yaml_files = load_yaml_dir(YAML_DIR)
    checklist_data = load_yaml_file(CHECKLISTS)

    n_rules = len(checklist_data.get("checklist", {}).get("rules", []))
    print(f"[G4] {len(yaml_files)} YAMLファイル / {n_rules} チェックリストルール\n")

    print("[G4] ── 評価1: Faithfulness（YAML ↔ 参照 忠実性・ハルシネーション検出）──")
    faith_results = eval_faithfulness(ref_content, yaml_files, FILE_PATH)

    print(f"\n[G4] ── 評価2: Checklist（{Path(CHECKLISTS).name}）──")
    check_results = eval_checklist(yaml_files, checklist_data)

    all_results = faith_results + check_results
    output = write_results(all_results, OUT_ROOT)

    s = output["summary"]
    print(f"\n{'=' * 64}")
    print("[G4] SUMMARY")
    print(f"     Overall : {s['overall_status'].upper()}  (total={s['total']}, passed={s['passed']}, failed={s['failed']})")
    fs = s["faithfulness"]
    print(f"     Faithfulness : avg={fs['avg_score']:.3f}  passed={fs['passed']}/{fs['total']}{' ⚠ WARNING' if fs['warning'] else ''}")
    cs = s["checklist"]
    print(f"     Checklist    : avg={cs['avg_score']:.3f}  passed={cs['passed']}/{cs['total']}{' ⚠ WARNING' if cs['warning'] else ''}")
    print(f"\n[G4] Output  : {output['_meta']['json_path']}")
    print(f"[G4] Allure  : {output['_meta']['allure_dir']}")
    print(f"{'=' * 64}\n")

    if fs["warning"]:
        print(f"[G4] ⚠ WARNING: Faithfulness avg score < {WARN_THRESHOLD:.2f}")
    if cs["warning"]:
        print(f"[G4] ⚠ WARNING: Checklist avg score < {WARN_THRESHOLD:.2f}")

    sys.exit(0 if s["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
