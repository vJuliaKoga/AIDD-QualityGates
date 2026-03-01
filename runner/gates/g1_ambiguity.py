# -*- coding: utf-8 -*-
"""
G1: 曖昧語チェック（Ambiguity Gate）

企画書の定義（G1: 曖昧語チェック / 入力 .yaml/.md / 出力 ambiguityreport.json）に対応。
- 入力: ファイル or ディレクトリ（.md .yaml .yml）
- 出力: JSON（G3互換の出力スタイルで上書き回避）
    output/target/<sanitized_target>/<mmdd_hhss>.json

設計意図:
- “適切に/柔軟に/なるべく”のような曖昧語は、上流工程での誤解釈・乖離の温床になるため早期に検出する。
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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

DEFAULT_OUT_ROOT = ROOT / "output" / "target"


# ----------------------------
# 出力（G3互換）
# ----------------------------

def sanitize_path_as_dirname(root: Path, p: Path) -> str:
    """
    例:
        artifacts/planning/yaml        -> artifacts_planning_yaml
        artifacts/planning/yaml/A.yaml -> artifacts_planning_yaml_A_yaml
    """
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
    """
    まずは“上流で事故りやすい”定番のみ（増やすのは後でOK）。
    企画書で例示されている「適切に」「柔軟に」も含める。
    """
    defs = [
        ("適切に", "HIGH", r"適切に", "基準が不明。定義/条件/閾値を要求"),
        ("柔軟に", "HIGH", r"柔軟に", "例外条件や優先順位が不明になりやすい"),
        ("なるべく", "MED", r"なるべく", "上限/下限/努力義務の範囲が不明"),
        ("可能な限り", "MED", r"可能な限り", "達成条件の欠落"),
        ("基本的に", "MED", r"基本的に", "例外条件が未定義になりやすい"),
        ("適宜", "MED", r"適宜", "判断者・判断基準が曖昧"),
        ("適当(に)?", "MED", r"適当(に)?", "口語で混入しやすい"),
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
    """
    YAMLは “曖昧語検出” なので、構造を壊さず文字列化して検索すれば十分。
    """
    obj = yaml.safe_load(read_text_file(p))
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False) if obj is not None else ""


def load_content(p: Path) -> str:
    if p.suffix.lower() in (".yaml", ".yml"):
        return yaml_to_text(p)
    return read_text_file(p)


# ----------------------------
# 検出
# ----------------------------

def build_line_index(text: str) -> List[str]:
    return text.splitlines()


def scan_text(
    file_path: Path,
    text: str,
    rules: List[AmbiguityRule],
    context_window: int = 40,
) -> List[Dict]:
    lines = build_line_index(text)
    findings: List[Dict] = []
    for i, line in enumerate(lines, start=1):
        for r in rules:
            if r.pattern.search(line):
                # 前後コンテキスト（同一行だけでもよいが、短く補助）
                ctx = line.strip()
                if len(ctx) > 2 * context_window:
                    ctx = ctx[:context_window] + " … " + ctx[-context_window:]
                findings.append({
                    "file": str(file_path),
                    "line": i,
                    "severity": r.severity,
                    "term": r.term,
                    "context": ctx,
                    "note": r.note,
                })
    return findings


def summarize(findings: List[Dict], total_files: int) -> Dict:
    sev_count = {"HIGH": 0, "MED": 0, "LOW": 0}
    for f in findings:
        sev = f.get("severity", "LOW")
        if sev in sev_count:
            sev_count[sev] += 1
    return {
        "files": total_files,
        "hits": len(findings),
        "high": sev_count["HIGH"],
        "med": sev_count["MED"],
        "low": sev_count["LOW"],
    }


def decide_exit_code(summary: Dict, fail_on: str) -> int:
    """
    fail_on:
        - high: HIGHが1件でもあれば 1
        - med : HIGH or MEDが1件でもあれば 1
        - any : 1件でもあれば 1
        - none: 常に0
    """
    if fail_on == "none":
        return 0
    if fail_on == "high":
        return 1 if summary["high"] > 0 else 0
    if fail_on == "med":
        return 1 if (summary["high"] + summary["med"]) > 0 else 0
    if fail_on == "any":
        return 1 if summary["hits"] > 0 else 0
    raise SystemExit(f"fail_on が不正です: {fail_on}")


# ----------------------------
# CLI
# ----------------------------

def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="G1 Ambiguity Gate")
    ap.add_argument("--target", required=True, help="対象ファイル or ディレクトリ")
    ap.add_argument("--out_root", default=str(DEFAULT_OUT_ROOT), help="出力ルート（G3互換）")
    ap.add_argument("--fail_on", default="high", choices=["high", "med", "any", "none"],
                    help="Fail条件")
    ap.add_argument("--max_findings", type=int, default=200, help="出力に載せる最大件数（多すぎ防止）")
    return ap


def main() -> int:
    ap = build_argparser()
    args = ap.parse_args()

    target = Path(args.target)
    out_root = Path(args.out_root)

    rules = build_default_rules()

    files = collect_targets(target)
    all_findings: List[Dict] = []

    for f in files:
        try:
            text = load_content(f)
        except Exception as e:
            all_findings.append({
                "file": str(f),
                "line": None,
                "severity": "HIGH",
                "term": "READ_ERROR",
                "context": "",
                "note": f"読み込み失敗: {type(e).__name__}: {e}",
            })
            continue

        all_findings.extend(scan_text(f, text, rules))

    # 多すぎる場合は先頭のみ（Allure/集約が重くなるのを防ぐ）
    if len(all_findings) > args.max_findings:
        all_findings = all_findings[:args.max_findings] + [{
            "file": None,
            "line": None,
            "severity": "LOW",
            "term": "TRUNCATED",
            "context": "",
            "note": f"findings が多すぎるため {args.max_findings} 件で打ち切り",
        }]

    summary = summarize(all_findings, total_files=len(files))
    exit_code = decide_exit_code(summary, fail_on=args.fail_on)

    out_path = build_g3_style_output_path(ROOT, out_root, target)

    report = {
        "gate": "G1_AMBIGUITY",
        "target": str(target),
        "timestamp": datetime.now().isoformat(),
        "config": {
            "fail_on": args.fail_on,
            "max_findings": args.max_findings,
        },
        "summary": summary,
        "findings": all_findings,
        "exit_code": exit_code,
        "output_file": str(out_path),
    }

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # コンソール要約（CIログに出力）
    print("=== G1 Ambiguity Gate ===")
    print(f"target      : {target}")
    print(f"files       : {summary['files']}")
    print(f"hits        : {summary['hits']} (HIGH={summary['high']}, MED={summary['med']}, LOW={summary['low']})")
    print(f"fail_on     : {args.fail_on}")
    print(f"exit_code   : {exit_code}")
    print(f"report_file : {out_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
