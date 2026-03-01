# -*- coding: utf-8 -*-
"""
---
meta:
    artifact_id: TST-G1-AMB-001
    file: g1_ambiguity.py
    author: '@juria.koga'
    source_type: human
    source: manual
    timestamp: '2026-03-01T17:15:00+09:00'
    content_hash: ae10ecc96204e9b33a06cd626f7db31de069f167961bb795dd492845ec899500
---

G1: 曖昧語チェック（Ambiguity Gate） - 汎用（企画〜運用で使い回し）

方針:
- 曖昧語は全カテゴリで検出してレポート化する
- ただしCIを止めるのは「手順/要求（PROC_REQ）」カテゴリのみ
- 除外できるのも PROC_REQ のみ（ズルいPASS防止）

出力:
- output/target/<sanitized_target>/<mmdd_hhss>.json（上書き回避）
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


# ----------------------------
# ルート推定
# ----------------------------

def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur] + list(cur.parents):
        if (p / "packs").exists() and (p / "artifacts").exists():
            return p
    return Path.cwd().resolve()


ROOT = find_repo_root(Path(__file__))
DEFAULT_OUT_ROOT = ROOT / "output" / "G1"


# ----------------------------
# 出力（G3互換）
# ----------------------------

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


# ----------------------------
# 曖昧語定義
# ----------------------------

@dataclass
class AmbiguityRule:
    term: str
    severity: str  # HIGH/MED/LOW
    pattern: re.Pattern
    note: str = ""


def build_default_rules() -> List[AmbiguityRule]:
    defs = [
        ("適切に", "HIGH", r"適切に", "基準が不明。定義/条件/閾値を要求"),
        ("柔軟に", "HIGH", r"柔軟に", "例外条件や優先順位が不明になりやすい"),
        ("なるべく", "MED", r"なるべく", "上限/下限/努力義務の範囲が不明"),
        ("可能な限り", "MED", r"可能な限り", "達成条件の欠落"),
        ("基本的に", "MED", r"基本的に", "例外条件が未定義になりやすい"),
        ("適宜", "MED", r"適宜", "判断者・判断基準が曖昧"),
        ("十分(に)?", "LOW", r"十分(に)?", "“十分”の定義が必要"),
        ("できるだけ", "LOW", r"できるだけ", "同上"),
        ("必要に応じて", "LOW", r"必要に応じて", "条件の明記が必要"),
    ]
    rules: List[AmbiguityRule] = []
    for term, sev, pat, note in defs:
        rules.append(AmbiguityRule(term=term, severity=sev, pattern=re.compile(pat), note=note))
    return rules


# ----------------------------
# 入力収集
# ----------------------------

def collect_targets(p: Path) -> List[Path]:
    if p.is_file():
        return [p]
    if p.is_dir():
        files: List[Path] = []
        for ext in ("*.md", "*.yaml", "*.yml"):
            files.extend(sorted(p.rglob(ext)))
        return files
    raise SystemExit(f"target が存在しません: {p}")


def read_text_file(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def yaml_to_text(p: Path) -> str:
    obj = yaml.safe_load(read_text_file(p))
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False) if obj is not None else ""


def load_content(p: Path) -> str:
    if p.suffix.lower() in (".yaml", ".yml"):
        return yaml_to_text(p)
    return read_text_file(p)


# ----------------------------
# カテゴリ判定（ヒューリスティック）
# ----------------------------

PROC_PATTERNS = [
    re.compile(r"^\s*([-*]|\d+[.)])\s+"),  # 箇条書き/番号
    re.compile(r"(すること|しなければ|必須|禁止|前提|～を行う|～を実施|must|shall)", re.IGNORECASE),
]
QUOTE_PATTERNS = [
    re.compile(r"^\s*>\s+"),  # 引用
    re.compile(r"(例：|例えば|サンプル|引用)"),
]


def categorize_line(line: str, in_code_block: bool) -> str:
    if in_code_block:
        return "QUOTE"
    if any(p.search(line) for p in QUOTE_PATTERNS):
        return "QUOTE"
    if any(p.search(line) for p in PROC_PATTERNS):
        return "PROC_REQ"
    return "DESC"


def split_lines_with_code_state(text: str) -> List[Tuple[int, str, bool]]:
    """
    (lineno, line, in_code_block) を返す
    - Markdownの ``` をトグルしてコードブロック内判定
    """
    out: List[Tuple[int, str, bool]] = []
    in_code = False
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("```"):
            # fence行自体もQUOTE扱いだが、ここではトグルのみ
            out.append((i, line, True))
            in_code = not in_code
            continue
        out.append((i, line, in_code))
    return out


# ----------------------------
# 除外リスト
# ----------------------------

def load_excludes(exclude_file: Optional[Path]) -> Dict[Tuple[str, int, str, str], Dict]:
    """
    excludeキー: (file, line, term, category)
    - category は PROC_REQ のみ許可
    """
    if exclude_file is None:
        return {}
    if not exclude_file.exists():
        raise SystemExit(f"exclude_file が見つかりません: {exclude_file}")

    obj = yaml.safe_load(exclude_file.read_text(encoding="utf-8")) or {}
    if obj.get("schema_version") != "g1_ambiguity_excludes_v1":
        raise SystemExit("exclude_file schema_version が不正です（g1_ambiguity_excludes_v1 が必要）")

    excludes = {}
    for e in (obj.get("excludes") or []):
        f = str(e.get("file", "")).strip()
        ln = int(e.get("line", 0))
        term = str(e.get("term", "")).strip()
        cat = str(e.get("category", "")).strip()
        if cat != "PROC_REQ":
            # “手順/要求だけ除外可”を強制
            raise SystemExit(f"exclude の category は PROC_REQ のみ許可です: {e}")
        if not f or ln <= 0 or not term:
            raise SystemExit(f"exclude の指定が不正です: {e}")
        excludes[(f, ln, term, cat)] = e
    return excludes


# ----------------------------
# 検出
# ----------------------------

def scan_text(
    file_path: Path,
    text: str,
    rules: List[AmbiguityRule],
    excludes: Dict[Tuple[str, int, str, str], Dict],
    context_window: int = 40,
) -> List[Dict]:
    findings: List[Dict] = []

    for lineno, line, in_code in split_lines_with_code_state(text):
        category = categorize_line(line, in_code_block=in_code)

        for r in rules:
            if r.pattern.search(line):
                ctx = line.strip()
                if len(ctx) > 2 * context_window:
                    ctx = ctx[:context_window] + " … " + ctx[-context_window:]

                key = (str(file_path), lineno, r.term, category)
                excluded = key in excludes

                findings.append({
                    "file": str(file_path),
                    "line": lineno,
                    "severity": r.severity,
                    "term": r.term,
                    "category": category,           # QUOTE / DESC / PROC_REQ
                    "excluded": bool(excluded),     # PROC_REQ のみ true になり得る
                    "context": ctx,
                    "note": r.note,
                    "exclude_reason": excludes.get(key, {}).get("reason") if excluded else None,
                    "approved_by": excludes.get(key, {}).get("approved_by") if excluded else None,
                    "approved_at": excludes.get(key, {}).get("approved_at") if excluded else None,
                })

    return findings


def summarize(findings: List[Dict], total_files: int) -> Dict:
    sev_count = {"HIGH": 0, "MED": 0, "LOW": 0}
    cat_count = {"QUOTE": 0, "DESC": 0, "PROC_REQ": 0}
    proc_req_fail = 0

    for f in findings:
        sev = f.get("severity", "LOW")
        cat = f.get("category", "DESC")

        if sev in sev_count:
            sev_count[sev] += 1
        if cat in cat_count:
            cat_count[cat] += 1

        if cat == "PROC_REQ" and not f.get("excluded", False):
            proc_req_fail += 1

    return {
        "files": total_files,
        "hits": len(findings),
        "high": sev_count["HIGH"],
        "med": sev_count["MED"],
        "low": sev_count["LOW"],
        "quote": cat_count["QUOTE"],
        "desc": cat_count["DESC"],
        "proc_req": cat_count["PROC_REQ"],
        "proc_req_fail": proc_req_fail,
    }


def exit_code_from_summary(summary: Dict) -> int:
    # FAIL対象は PROC_REQ の未除外のみ
    return 1 if summary["proc_req_fail"] > 0 else 0


# ----------------------------
# CLI
# ----------------------------

def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="G1 Ambiguity Gate (reusable)")
    ap.add_argument("--target", required=True, help="対象ファイル or ディレクトリ")
    ap.add_argument("--out_root", default=str(DEFAULT_OUT_ROOT), help="出力ルート（G3互換）")
    ap.add_argument("--exclude_file", default=None, help="除外リスト YAML（PROC_REQのみ許可）")
    ap.add_argument("--max_findings", type=int, default=300, help="出力に載せる最大件数（多すぎ防止）")
    return ap


def main() -> int:
    ap = build_argparser()
    args = ap.parse_args()

    target = Path(args.target)
    out_root = Path(args.out_root)
    exclude_file = Path(args.exclude_file) if args.exclude_file else None

    rules = build_default_rules()
    excludes = load_excludes(exclude_file)

    files = collect_targets(target)
    all_findings: List[Dict] = []

    for f in files:
        try:
            text = load_content(f)
        except Exception as e:
            # 読めないのは手順以前に問題なのでPROC_REQ扱いでFailに寄せる（除外不可）
            all_findings.append({
                "file": str(f),
                "line": None,
                "severity": "HIGH",
                "term": "READ_ERROR",
                "category": "PROC_REQ",
                "excluded": False,
                "context": "",
                "note": f"読み込み失敗: {type(e).__name__}: {e}",
                "exclude_reason": None,
                "approved_by": None,
                "approved_at": None,
            })
            continue

        all_findings.extend(scan_text(f, text, rules, excludes))

    if len(all_findings) > args.max_findings:
        all_findings = all_findings[:args.max_findings] + [{
            "file": None,
            "line": None,
            "severity": "LOW",
            "term": "TRUNCATED",
            "category": "DESC",
            "excluded": False,
            "context": "",
            "note": f"findings が多すぎるため {args.max_findings} 件で打ち切り",
            "exclude_reason": None,
            "approved_by": None,
            "approved_at": None,
        }]

    summary = summarize(all_findings, total_files=len(files))
    code = exit_code_from_summary(summary)

    out_path = build_g3_style_output_path(ROOT, out_root, target)

    report = {
        "gate": "G1_AMBIGUITY",
        "target": str(target),
        "timestamp": datetime.now().isoformat(),
        "config": {
            "exclude_file": str(exclude_file) if exclude_file else None,
            "max_findings": args.max_findings,
            "rules_count": len(rules),
            "fail_policy": "FAIL if any PROC_REQ not excluded",
        },
        "summary": summary,
        "findings": all_findings,
        "exit_code": code,
        "output_file": str(out_path),
    }

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # コンソール（CIログ用）
    print("=== G1 Ambiguity Gate ===")
    print(f"target         : {target}")
    print(f"files          : {summary['files']}")
    print(f"hits           : {summary['hits']} (HIGH={summary['high']}, MED={summary['med']}, LOW={summary['low']})")
    print(f"categories     : PROC_REQ={summary['proc_req']} (FAIL={summary['proc_req_fail']}), DESC={summary['desc']}, QUOTE={summary['quote']}")
    print(f"exclude_file   : {exclude_file if exclude_file else '(none)'}")
    print(f"exit_code      : {code}")
    print(f"report_file    : {out_path}")

    return code


if __name__ == "__main__":
    raise SystemExit(main())