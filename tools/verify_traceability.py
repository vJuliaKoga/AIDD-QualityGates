#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verify_traceability.py — AIDD Traceability Checker & Fixer

モード:
  check  指定ディレクトリ群の全YAMLを横断してトレーサビリティを検証する
  fix    derived_from が PENDING/空のフィールドを対話的に（または一括で）修正する

使い方:
  # 検証のみ
  python tools/verify_traceability.py check ^
      --dirs planning/yaml/planning_v2.2 requirements/yaml/requirements_v1 ^
      --report-out reports/traceability_report.json

  # 対話的修正（PLN系IDから選んで設定）
  python tools/verify_traceability.py fix ^
      --dirs planning/yaml/planning_v2.2 requirements/yaml/requirements_v1 ^
      --target requirements/yaml/requirements_v1

  # 非対話的一括修正（全PENDINGを同一IDに設定）
  python tools/verify_traceability.py fix ^
      --dirs planning/yaml/planning_v2.2 requirements/yaml/requirements_v1 ^
      --target requirements/yaml/requirements_v1 ^
      --set-derived-from PLN-PLN-CONCEPT-005

  # ドライラン（ファイルを書き換えずに確認のみ）
  python tools/verify_traceability.py fix ... --dry-run

Exit codes:
  0  TRACEABILITY: PASS（checkモード）/ 修正完了（fixモード）
  1  TRACEABILITY: FAIL（checkモード）/ 修正スキップ（fixモード）
  2  引数エラー / 実行エラー
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required.  pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# ============================================================
# 定数
# ============================================================

# AIDD ID 正規表現  PREFIX-PHASE-PURPOSE-NNN
ID_PATTERN = re.compile(r"^[A-Z]{2,5}-[A-Z]{2,5}-[A-Z0-9_]+-\d{3}$")

# 自身の ID を保持するフィールド名（小文字で比較）
OWN_ID_KEYS: Set[str] = {"id", "req_id", "doc_id", "artifact_id"}

# 参照（upstream 方向）を保持するフィールド名
DERIVED_FROM_KEYS: Set[str] = {"derived_from", "derivedfrom"}

# 参照（downstream 方向）を保持するフィールド名
TRACES_TO_KEYS: Set[str] = {"traces_to", "tracesto"}

# プロンプト参照フィールド
PROMPT_REF_KEYS: Set[str] = {"prompt_id"}

# 全参照フィールド（チェック対象）
ALL_REF_KEYS: Set[str] = DERIVED_FROM_KEYS | TRACES_TO_KEYS | PROMPT_REF_KEYS

# PENDING 判定パターン（大文字小文字不問）
PENDING_STRINGS: Set[str] = {"pending", ""}

# check モードで FAIL とするフィールド（traces_to の空は警告止まり）
FAIL_ON_EMPTY: Set[str] = DERIVED_FROM_KEYS


# ============================================================
# ユーティリティ
# ============================================================

def is_aidd_id(value: Any) -> bool:
    """文字列が AIDD ID フォーマットに一致するか"""
    return isinstance(value, str) and bool(ID_PATTERN.match(value.strip()))


def is_pending(value: Any) -> bool:
    """値が PENDING / 空 / None / 空リストかどうか"""
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0 or all(
            isinstance(v, str) and v.strip().upper() in {"PENDING", ""}
            for v in value
        )
    if isinstance(value, str):
        return value.strip().upper() in {"PENDING", ""}
    return False


def collect_yaml_files(dirs: List[Path]) -> List[Path]:
    """ディレクトリ（またはファイル）から YAML ファイルを再帰的に収集する"""
    files: List[Path] = []
    for d in dirs:
        if d.is_file() and d.suffix.lower() in (".yaml", ".yml"):
            files.append(d)
        elif d.is_dir():
            found = sorted(
                p for p in d.rglob("*")
                if p.is_file() and p.suffix.lower() in (".yaml", ".yml")
            )
            files.extend(found)
        else:
            print(f"[WARN] Not found: {d}", file=sys.stderr)
    # 重複排除しつつ順序を保持
    seen: Set[Path] = set()
    result: List[Path] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result


def load_yaml_safe(path: Path) -> Optional[Any]:
    """YAML を安全に読み込む。失敗時は None を返す"""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] Cannot parse {path}: {exc}", file=sys.stderr)
        return None


def rel(path: Path, base: Path) -> str:
    """base からの相対パス文字列を返す（スラッシュ区切り）"""
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


# ============================================================
# ID レジストリ構築
# ============================================================

def _collect_own_ids(obj: Any, filepath: str, registry: Dict[str, str]) -> None:
    """再帰的に OWN_ID_KEYS のフィールド値（AIDD ID のみ）を収集する"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in OWN_ID_KEYS and is_aidd_id(v):
                # 先着優先（同一 ID が複数ファイルにある場合は最初のもの）
                if v not in registry:
                    registry[v] = filepath
            else:
                _collect_own_ids(v, filepath, registry)
    elif isinstance(obj, list):
        for item in obj:
            _collect_own_ids(item, filepath, registry)


def build_id_registry(files: List[Path], base: Path) -> Dict[str, str]:
    """全ファイルから {AIDD_ID: 相対ファイルパス} のレジストリを構築する"""
    registry: Dict[str, str] = {}
    for f in files:
        doc = load_yaml_safe(f)
        if doc is None:
            continue
        _collect_own_ids(doc, rel(f, base), registry)
    return registry


# ============================================================
# 参照（Reference）抽出
# ============================================================

class Reference:
    """トレーサビリティ参照を表すデータクラス"""
    __slots__ = ("source_file", "source_id", "field", "ref_id", "direction")

    def __init__(
        self,
        source_file: str,
        source_id: str,
        field: str,
        ref_id: str,
        direction: str,  # "upstream" | "downstream" | "prompt"
    ) -> None:
        self.source_file = source_file
        self.source_id = source_id
        self.field = field
        self.ref_id = ref_id
        self.direction = direction

    def to_dict(self) -> Dict[str, str]:
        return {
            "source_file": self.source_file,
            "source_id": self.source_id,
            "field": self.field,
            "ref_id": self.ref_id,
            "direction": self.direction,
        }


def _field_direction(field_key: str) -> str:
    kl = field_key.lower()
    if kl in DERIVED_FROM_KEYS:
        return "upstream"
    if kl in TRACES_TO_KEYS:
        return "downstream"
    return "prompt"


def _collect_refs(
    obj: Any,
    filepath: str,
    context_id: str,
    refs: List[Reference],
) -> None:
    """再帰的に参照フィールドを収集する"""
    if isinstance(obj, dict):
        # このノードの自 ID を取得（参照元として使う）
        node_id = context_id
        for k in OWN_ID_KEYS:
            if is_aidd_id(obj.get(k, "")):
                node_id = obj[k]
                break

        for k, v in obj.items():
            kl = k.lower()
            if kl in ALL_REF_KEYS:
                direction = _field_direction(k)
                if isinstance(v, str) and is_aidd_id(v):
                    refs.append(Reference(filepath, node_id, k, v, direction))
                elif isinstance(v, list):
                    for item in v:
                        if is_aidd_id(item):
                            refs.append(Reference(filepath, node_id, k, item, direction))
            else:
                _collect_refs(v, filepath, node_id, refs)

    elif isinstance(obj, list):
        for item in obj:
            _collect_refs(item, filepath, context_id, refs)


def extract_references(files: List[Path], base: Path) -> List[Reference]:
    """全ファイルからトレーサビリティ参照を抽出する"""
    all_refs: List[Reference] = []
    for f in files:
        doc = load_yaml_safe(f)
        if doc is None:
            continue
        _collect_refs(doc, rel(f, base), "", all_refs)
    return all_refs


# ============================================================
# PENDING フィールドの検出
# ============================================================

class PendingEntry:
    """derived_from が PENDING / 空である箇所"""
    __slots__ = ("filepath", "context_id", "field", "current_value")

    def __init__(
        self,
        filepath: Path,
        context_id: str,
        field: str,
        current_value: Any,
    ) -> None:
        self.filepath = filepath
        self.context_id = context_id
        self.field = field
        self.current_value = current_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": str(self.filepath),
            "context_id": self.context_id,
            "field": self.field,
            "current_value": self.current_value,
        }


def _find_pending(
    obj: Any,
    filepath: Path,
    context_id: str,
    results: List[PendingEntry],
) -> None:
    """再帰的に PENDING な derived_from フィールドを検出する"""
    if isinstance(obj, dict):
        node_id = context_id
        for k in OWN_ID_KEYS:
            if is_aidd_id(obj.get(k, "")):
                node_id = obj[k]
                break

        for k, v in obj.items():
            kl = k.lower()
            if kl in DERIVED_FROM_KEYS and is_pending(v):
                results.append(PendingEntry(filepath, node_id, k, v))
            else:
                _find_pending(v, filepath, node_id, results)

    elif isinstance(obj, list):
        for item in obj:
            _find_pending(item, filepath, context_id, results)


def find_all_pending(files: List[Path]) -> List[PendingEntry]:
    """ファイル群から PENDING な derived_from を全て検出する"""
    results: List[PendingEntry] = []
    for f in files:
        doc = load_yaml_safe(f)
        if doc is None:
            continue
        _find_pending(doc, f, "", results)
    return results


# ============================================================
# check モード
# ============================================================

def cmd_check(
    dirs: List[Path],
    base: Path,
    report_out: Optional[Path],
    warn_orphan: bool,
) -> int:
    """トレーサビリティを検証する。PASS なら 0、FAIL なら 1 を返す"""
    files = collect_yaml_files(dirs)
    if not files:
        print("TRACEABILITY: FAIL — No YAML files found", file=sys.stderr)
        return 2

    print(f"Scanning {len(files)} YAML files ...")
    id_registry = build_id_registry(files, base)
    references = extract_references(files, base)
    pending = find_all_pending(files)

    # ---- 壊れたリンク（参照先が存在しない）
    broken: List[Dict[str, str]] = []
    for ref in references:
        if ref.ref_id not in id_registry:
            broken.append(ref.to_dict() | {"note": f"'{ref.ref_id}' は既知のIDに存在しません"})

    # ---- 孤立 ID（何にも参照されていない）
    referenced_ids: Set[str] = {r.ref_id for r in references}
    orphan_ids = sorted(set(id_registry.keys()) - referenced_ids)

    # ---- PENDING derived_from（FAILにする）
    pending_items = [p.to_dict() for p in pending]

    # ---- 判定
    has_broken = len(broken) > 0
    has_pending = len(pending) > 0
    overall_pass = not has_broken and not has_pending

    # ---- コンソール出力
    print()
    print(f"TRACEABILITY: {'PASS' if overall_pass else 'FAIL'}")
    print(f"  IDs found        : {len(id_registry)}")
    print(f"  References found : {len(references)}")
    print(f"  Broken links     : {len(broken)}   {'[FAIL]' if has_broken else '[OK]'}")
    print(f"  Pending derived  : {len(pending)}   {'[FAIL]' if has_pending else '[OK]'}")
    print(f"  Orphan IDs       : {len(orphan_ids)}  {'[WARN]' if orphan_ids else '[OK]'} (informational)")

    if broken:
        print()
        print("  [BROKEN LINKS]")
        for b in broken:
            print(f"    {b['source_file']}  ({b['source_id']})  {b['field']} → {b['ref_id']}")

    if pending:
        print()
        print("  [PENDING derived_from]  — 'fix' モードで修正できます")
        for p in pending_items:
            print(f"    {p['file']}  ({p['context_id']})  {p['field']} = {p['current_value']!r}")

    if warn_orphan and orphan_ids:
        print()
        print("  [ORPHAN IDs] — 何にも参照されていないID（参考情報）")
        for oid in orphan_ids[:30]:
            src = id_registry[oid]
            print(f"    {oid}  ({src})")
        if len(orphan_ids) > 30:
            print(f"    ... 他 {len(orphan_ids) - 30} 件")

    # ---- レポート出力
    report = {
        "generated_at": _now_iso(),
        "overall_pass": overall_pass,
        "summary": {
            "files_scanned": len(files),
            "ids_found": len(id_registry),
            "references_found": len(references),
            "broken_links": len(broken),
            "pending_derived_from": len(pending),
            "orphan_ids": len(orphan_ids),
        },
        "broken_links": broken,
        "pending_derived_from": pending_items,
        "orphan_ids": orphan_ids,
        "id_registry": id_registry,
        "references": [r.to_dict() for r in references],
    }

    if report_out:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print()
        print(f"  Report: {report_out}")

    return 0 if overall_pass else 1


# ============================================================
# fix モード — YAML パッチ適用
# ============================================================

def _patch_node(obj: Any, context_id: str, field: str, new_value: str) -> bool:
    """YAML オブジェクト内の対象フィールドを書き換える。成功したら True を返す"""
    if isinstance(obj, dict):
        # このノードが対象かどうか確認
        node_matches = False
        if context_id:
            for k in OWN_ID_KEYS:
                if obj.get(k) == context_id:
                    node_matches = True
                    break
        else:
            # context_id が空 = ドキュメントルートレベルのフィールドを直接書き換え
            node_matches = True

        if node_matches and field in obj:
            obj[field] = new_value
            return True

        # related サブキー内にある場合（例: related.derivedfrom）
        if node_matches and "related" in obj and isinstance(obj["related"], dict):
            rel_obj = obj["related"]
            if field in rel_obj:
                rel_obj[field] = new_value
                return True

        # 子ノードを再帰探索
        for v in obj.values():
            if isinstance(v, (dict, list)):
                if _patch_node(v, context_id, field, new_value):
                    return True

    elif isinstance(obj, list):
        for item in obj:
            if _patch_node(item, context_id, field, new_value):
                return True

    return False


def apply_patch(entry: PendingEntry, new_value: str) -> bool:
    """ファイルを読み込み、対象フィールドを修正して書き戻す"""
    doc = load_yaml_safe(entry.filepath)
    if doc is None:
        return False

    patched = _patch_node(doc, entry.context_id, entry.field, new_value)
    if not patched:
        # context_id なしで再試行（フラットな構造の場合）
        patched = _patch_node(doc, "", entry.field, new_value)

    if not patched:
        print(
            f"  [ERROR] フィールドが見つかりませんでした: "
            f"file={entry.filepath}  context_id={entry.context_id}  field={entry.field}",
            file=sys.stderr,
        )
        return False

    # yaml.dump で書き戻す（コメントは失われるが構造は保持）
    new_text = yaml.dump(doc, allow_unicode=True, sort_keys=False, default_flow_style=False)
    entry.filepath.write_text(new_text, encoding="utf-8")
    return True


# ============================================================
# fix モード — 対話UI
# ============================================================

def _print_id_menu(upstream_ids: List[str], id_registry: Dict[str, str]) -> None:
    """選択可能な upstream ID の一覧を表示する"""
    print("  利用可能な upstream IDs:")
    for i, uid in enumerate(upstream_ids, 1):
        src = Path(id_registry.get(uid, "")).name
        print(f"    {i:3d}. {uid}  ({src})")
    if not upstream_ids:
        print("    (なし)")


def cmd_fix(
    dirs: List[Path],
    target_dirs: List[Path],
    base: Path,
    set_value: Optional[str],
    dry_run: bool,
    show_all_ids: bool,
) -> int:
    """PENDING な derived_from を修正する。終了コードを返す"""
    # 全ファイルから ID レジストリを構築（選択肢として使う）
    all_files = collect_yaml_files(dirs)
    id_registry = build_id_registry(all_files, base)

    # 修正対象ファイルを特定
    target_files = collect_yaml_files(target_dirs)
    if not target_files:
        print("WARN: No YAML files found in --target directories.", file=sys.stderr)
        return 2

    pendings = find_all_pending(target_files)
    if not pendings:
        print("TRACEABILITY FIX: Nothing to fix — no PENDING derived_from found.")
        return 0

    print(f"PENDING derived_from が {len(pendings)} 件見つかりました。")
    if dry_run:
        print("  [DRY-RUN mode — ファイルは変更されません]")
    print()

    # upstream IDs の一覧（PLN プレフィックスを優先表示）
    pln_ids = sorted(uid for uid in id_registry if uid.startswith("PLN-"))
    other_ids = sorted(uid for uid in id_registry if not uid.startswith("PLN-"))
    upstream_ids = pln_ids + (other_ids if show_all_ids else [])

    fixed_count = 0
    skipped_count = 0

    for idx, entry in enumerate(pendings, 1):
        print(f"─── [{idx}/{len(pendings)}] PENDING derived_from ───────────────────────")
        print(f"  ファイル   : {entry.filepath}")
        print(f"  アイテムID : {entry.context_id or '(ドキュメントルート)'}")
        print(f"  フィールド : {entry.field}")
        print(f"  現在値     : {entry.current_value!r}")
        print()

        if set_value is not None:
            # 非対話モード: 引数で指定された値を使う
            if not is_aidd_id(set_value):
                print(f"  [ERROR] --set-derived-from の値が AIDD ID 形式ではありません: {set_value}", file=sys.stderr)
                return 2
            chosen = set_value
            print(f"  → --set-derived-from で設定: {chosen}")
        else:
            # 対話モード
            _print_id_menu(upstream_ids, id_registry)
            print()
            prompt = (
                "  選択してください "
                "[番号 / AIDD-ID 直接入力 / Enter でスキップ / q で終了]: "
            )
            try:
                answer = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\n中断しました。")
                break

            if answer.lower() == "q":
                print("終了します。")
                break
            if not answer:
                print("  → スキップ")
                skipped_count += 1
                continue
            if answer.isdigit():
                num = int(answer) - 1
                if 0 <= num < len(upstream_ids):
                    chosen = upstream_ids[num]
                else:
                    print(f"  [WARN] 番号が範囲外です: {answer}  スキップします。")
                    skipped_count += 1
                    continue
            elif is_aidd_id(answer):
                chosen = answer
            else:
                print(f"  [WARN] 有効な AIDD ID ではありません: {answer}  スキップします。")
                skipped_count += 1
                continue

        # パッチ適用
        if dry_run:
            print(f"  [DRY-RUN] {entry.field} を {chosen!r} に設定します")
            fixed_count += 1
        else:
            ok = apply_patch(entry, chosen)
            if ok:
                print(f"  [FIXED] {entry.field} = {chosen}")
                fixed_count += 1
            else:
                print(f"  [ERROR] パッチ適用に失敗しました")
                skipped_count += 1
        print()

    # サマリー
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if dry_run:
        print(f"DRY-RUN 完了: {fixed_count} 件を修正予定 / {skipped_count} 件スキップ")
    else:
        print(f"FIX 完了: {fixed_count} 件修正 / {skipped_count} 件スキップ")
        if fixed_count > 0:
            print("  修正後に 'check' モードで再検証することを推奨します。")

    return 0 if fixed_count > 0 or len(pendings) == 0 else 1


# ============================================================
# メイン
# ============================================================

def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


def _resolve_dirs(raw: List[str], base: Path) -> List[Path]:
    """文字列リストをパスに変換する（相対パスはリポジトリルートから解決）"""
    result: List[Path] = []
    for s in raw:
        p = Path(s)
        if not p.is_absolute():
            p = base / p
        result.append(p.resolve())
    return result


def main() -> None:
    ap = argparse.ArgumentParser(
        description="AIDD Traceability Checker & Fixer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--repo-root", default=".",
        help="リポジトリルート（デフォルト: カレントディレクトリ）",
    )

    sub = ap.add_subparsers(dest="command", required=True)

    # ---- check サブコマンド ----
    p_check = sub.add_parser("check", help="トレーサビリティを検証する")
    p_check.add_argument(
        "--dirs", nargs="+", required=True,
        help="スキャン対象のディレクトリ（複数指定可）",
    )
    p_check.add_argument(
        "--report-out", default="",
        help="レポート JSON の出力先（省略時は出力しない）",
    )
    p_check.add_argument(
        "--warn-orphan", action="store_true",
        help="孤立 ID の一覧を表示する（FAIL にはしない）",
    )

    # ---- fix サブコマンド ----
    p_fix = sub.add_parser(
        "fix",
        help="PENDING な derived_from を修正する",
    )
    p_fix.add_argument(
        "--dirs", nargs="+", required=True,
        help="ID レジストリ構築のスキャン対象（全フェーズを含めること）",
    )
    p_fix.add_argument(
        "--target", nargs="+", required=True,
        help="修正対象のディレクトリ（--dirs の部分集合）",
    )
    p_fix.add_argument(
        "--set-derived-from", default=None,
        help="全 PENDING を指定した ID で一括設定する（非対話モード）",
    )
    p_fix.add_argument(
        "--dry-run", action="store_true",
        help="ファイルを変更せずに確認のみ行う",
    )
    p_fix.add_argument(
        "--show-all-ids", action="store_true",
        help="PLN 系以外の ID も選択肢に含める",
    )

    args = ap.parse_args()
    base = Path(args.repo_root).resolve()

    if args.command == "check":
        dirs = _resolve_dirs(args.dirs, base)
        report_out = Path(args.report_out).resolve() if args.report_out else None
        code = cmd_check(dirs, base, report_out, args.warn_orphan)
        sys.exit(code)

    elif args.command == "fix":
        dirs = _resolve_dirs(args.dirs, base)
        target_dirs = _resolve_dirs(args.target, base)
        code = cmd_fix(
            dirs=dirs,
            target_dirs=target_dirs,
            base=base,
            set_value=args.set_derived_from,
            dry_run=args.dry_run,
            show_all_ids=args.show_all_ids,
        )
        sys.exit(code)


if __name__ == "__main__":
    main()
