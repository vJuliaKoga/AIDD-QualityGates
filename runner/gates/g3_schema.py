"""
meta:
    artifact_id: RES-TST-G3SCHEMA-001
    file: g3_schema.py
    author: '@juria.koga'
    source_type: human
    source: manual
    timestamp: '2026-03-01T13:01:00+09:00'
    content_hash: b65132f5d6b98b8272d8ac29ebb3ba35f2f6d1157c2528b4943c87284bae01e7

"""
import json
import sys
from pathlib import Path
from datetime import datetime
import re

import yaml
from jsonschema import Draft202012Validator


def find_repo_root(start: Path) -> Path:
    """
    runner/gates/ 配下でも packs/pln_pack/ 配下でも動くように、
    上に登りながら repo root を推定する。
    """
    cur = start.resolve()
    for p in [cur] + list(cur.parents):
        if (p / "packs").exists() and (p / "artifacts").exists():
            return p
    # 最後の手段：実行位置
    return Path.cwd().resolve()


ROOT = find_repo_root(Path(__file__))

DEFAULT_SCHEMA = ROOT / "packs" / "pln_pack" / "schemas" / "pln_canonical_v1.schema.json"
DEFAULT_INPUT_PATH = ROOT / "artifacts" / "planning" / "yaml"  # dir or file
DEFAULT_OUTPUT_DIR = ROOT / "output" / "G3"


def load_yaml(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_path_as_dirname(p: Path) -> str:
    """
    例:
        artifacts/planning/yaml        -> artifacts_planning_yaml
        artifacts/planning/yaml/A.yaml -> artifacts_planning_yaml_A_yaml
    - Windowsでも安全なディレクトリ名にするため、英数と _ - . 以外は _ に潰す
    - 区切りはパス区切りを '_' に変換
    """
    # 可能なら repo root からの相対にする（長すぎ対策＆分かりやすさ）
    try:
        rel = p.resolve().relative_to(ROOT.resolve())
        parts = list(rel.parts)
    except Exception:
        parts = list(p.parts)

    # パスのドライブ名みたいな変なのを除外（例: 'C:\\'）
    parts = [x for x in parts if x and not re.match(r"^[A-Za-z]:\\?$", x)]

    name = "_".join(parts)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "unknown_target"


def validate_one(schema, doc, doc_path: Path):
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))
    return [
        {
            "path": str(doc_path),
            "json_path": "/" + "/".join(map(str, e.absolute_path)),
            "message": e.message,
        }
        for e in errors
    ]


def target_dir_name(input_path: Path) -> str:
    """
    ディレクトリ名は「テスト対象フォルダ or ファイル名」。
    - dir: そのまま name
    - file: stem（拡張子なし）
    """
    if input_path.is_file():
        return input_path.stem
    return input_path.name


def unique_output_path(out_dir: Path, base_name: str, ext: str = ".json") -> Path:
    """
    同じ秒で連続実行しても上書きしないよう、存在したら _01,_02… を付ける。
    """
    p = out_dir / f"{base_name}{ext}"
    if not p.exists():
        return p
    i = 1
    while True:
        cand = out_dir / f"{base_name}_{i:02d}{ext}"
        if not cand.exists():
            return cand
        i += 1


def main():
    schema_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SCHEMA
    input_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_INPUT_PATH
    output_root = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OUTPUT_DIR

    schema = load_json(schema_path)

    # output_root が無ければ作る
    output_root.mkdir(parents=True, exist_ok=True)

    # 対象名サブディレクトリ（無ければ作る）
    tgt_name = sanitize_path_as_dirname(input_path)
    out_dir = output_root / tgt_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # 成果物ファイル名：mmdd_hhss（要件どおり）
    ts = datetime.now().strftime("%m%d_%H%S")
    out_file = unique_output_path(out_dir, ts, ".json")

    # 入力が dir なら *.yaml、file ならその1枚
    if input_path.is_dir():
        yaml_files = sorted(input_path.glob("*.yaml"))
    else:
        yaml_files = [input_path] if input_path.exists() else []

    if not yaml_files:
        result = {
            "gate": "G3_SCHEMA",
            "status": "FAIL",
            "reason": f"No YAML files found in {input_path}",
            "schema": str(schema_path),
            "target": str(input_path),
            "output_dir": str(out_dir),
            "files": [],
            "errors": [],
        }
        out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(1)

    all_errors = []
    validated = []
    for yp in yaml_files:
        doc = load_yaml(yp)
        errs = validate_one(schema, doc, yp)
        validated.append(str(yp))
        all_errors.extend(errs)

    status = "PASS" if not all_errors else "FAIL"
    result = {
        "gate": "G3_SCHEMA",
        "status": status,
        "schema": str(schema_path),
        "target": str(input_path),
        "output_dir": str(out_dir),
        "files": validated,
        "error_count": len(all_errors),
        "errors": all_errors[:200],
    }
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()