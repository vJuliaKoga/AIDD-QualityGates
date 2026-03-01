import argparse
import datetime as _dt
from pathlib import Path
import subprocess
import sys
import yaml


MD_FRONT_MATTER_DELIM = "---"


class _QuotedStr(str):
    pass


def _quoted_str_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="'")


yaml.SafeDumper.add_representer(_QuotedStr, _quoted_str_representer)


def now_local_iso() -> str:
    # e.g. 2026-03-01T03:46:00+09:00
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def run_sha256(script_path: Path, target_file: Path) -> str:
    res = subprocess.run(
        [sys.executable, str(script_path), str(target_file)],
        capture_output=True, text=True
    )
    if res.returncode != 0:
        raise SystemExit(
            "Hash script failed.\n"
            f"cmd: {sys.executable} {script_path} {target_file}\n"
            f"stdout:\n{res.stdout}\n"
            f"stderr:\n{res.stderr}\n"
        )
    out = (res.stdout or "").strip().splitlines()
    if not out:
        raise SystemExit("Hash script produced no output.")
    return out[-1].strip()


def rebuild_meta_ai(existing_meta: dict | None, *, artifact_id: str, file_name: str,
                    prompt_id: str, source: str, model: str) -> dict:
    """Rebuild meta so prompt_id is always traceable.

    Policy:
    - Keep ONLY meta.schema_version from the old meta (if present).
    - Everything else is re-stamped deterministically in a stable key order.
    """
    schema_version = None
    if isinstance(existing_meta, dict):
        schema_version = existing_meta.get("schema_version")

    meta: dict = {}
    if schema_version is not None:
        meta["schema_version"] = schema_version

    # Stable ordering (insertion order)
    meta["artifact_id"] = artifact_id
    meta["file"] = file_name
    meta["author"] = model
    meta["source_type"] = "ai"
    meta["source"] = source           # e.g. "codex" / "chatgpt" / "manual"
    meta["prompt_id"] = prompt_id     # <-- traceable prompt ID (explicit field)
    meta["timestamp"] = _QuotedStr(now_local_iso())
    meta["model"] = model
    meta["content_hash"] = "PENDING"
    return meta


def assert_meta_present(f: Path, expected_artifact_id: str, expected_prompt_id: str):
    data = yaml.safe_load(f.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("YAML root must be an object")

    meta = data.get("meta")
    if not isinstance(meta, dict):
        raise SystemExit("meta is missing after stamping.")

    required = ["artifact_id", "file", "author", "source_type", "source", "prompt_id",
                "timestamp", "model", "content_hash"]
    missing = [k for k in required if k not in meta]
    if missing:
        raise SystemExit(f"meta missing keys after stamping: {missing}")

    if meta["artifact_id"] != expected_artifact_id:
        raise SystemExit(f"meta.artifact_id mismatch: {meta['artifact_id']} != {expected_artifact_id}")
    if meta["prompt_id"] != expected_prompt_id:
        raise SystemExit(f"meta.prompt_id mismatch: {meta['prompt_id']} != {expected_prompt_id}")


def _dump_yaml(data: dict) -> str:
    return yaml.dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        Dumper=yaml.SafeDumper,
    )


def _move_meta_to_top(root: dict) -> dict:
    if not isinstance(root, dict):
        return root
    meta = root.get("meta")
    new_root = {}
    if meta is not None:
        new_root["meta"] = meta
    for k, v in root.items():
        if k == "meta":
            continue
        new_root[k] = v
    return new_root


def _split_md_front_matter(text: str) -> tuple[dict | None, str]:
    """Split markdown YAML front matter.

    Returns:
        (front_matter_dict_or_None, body_text)

    Front matter format:
        ---
        meta:
        ...
        ---
        <body>
    """
    lines = (text or "").splitlines(keepends=True)
    if not lines:
        return None, ""

    if lines[0].strip() != MD_FRONT_MATTER_DELIM:
        return None, text

    # find closing delimiter
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == MD_FRONT_MATTER_DELIM:
            end_idx = i
            break

    if end_idx is None:
        # malformed; treat as no front matter
        return None, text

    fm_text = "".join(lines[1:end_idx])
    body = "".join(lines[end_idx + 1 :])
    try:
        fm = yaml.safe_load(fm_text)
    except Exception:
        fm = None
    return fm if isinstance(fm, dict) else None, body


def _build_md_with_front_matter(front_matter: dict, body: str) -> str:
    fm_yaml = _dump_yaml(front_matter).rstrip() + "\n"
    body = body or ""
    # Ensure body starts after a newline (cosmetic)
    if body and not body.startswith("\n"):
        # but avoid adding extra blank line if body already starts with header
        pass
    return f"{MD_FRONT_MATTER_DELIM}\n{fm_yaml}{MD_FRONT_MATTER_DELIM}\n\n{body.lstrip()}"


def assert_meta_present_md(f: Path, expected_artifact_id: str, expected_prompt_id: str):
    fm, _body = _split_md_front_matter(f.read_text(encoding="utf-8"))
    if not isinstance(fm, dict):
        raise SystemExit("front matter is missing after stamping.")
    meta = fm.get("meta")
    if not isinstance(meta, dict):
        raise SystemExit("meta is missing after stamping.")

    required = [
        "artifact_id",
        "file",
        "author",
        "source_type",
        "source",
        "prompt_id",
        "timestamp",
        "model",
        "content_hash",
    ]
    missing = [k for k in required if k not in meta]
    if missing:
        raise SystemExit(f"meta missing keys after stamping: {missing}")
    if meta["artifact_id"] != expected_artifact_id:
        raise SystemExit(f"meta.artifact_id mismatch: {meta['artifact_id']} != {expected_artifact_id}")
    if meta["prompt_id"] != expected_prompt_id:
        raise SystemExit(f"meta.prompt_id mismatch: {meta['prompt_id']} != {expected_prompt_id}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="artifacts/planning/PLN-PLN-GOAL-001.yaml etc.")
    ap.add_argument("--prompt-id", required=True, help="PRM-PLN-YAML-001 etc. (stored in meta.prompt_id)")
    ap.add_argument("--source", default="codex", help="Where the content came from (default: codex)")
    ap.add_argument("--hash-script", default="hashtag/hashtag_generator.py")
    ap.add_argument("--model", default="gpt-5.2", help="Model label stored in meta.author/meta.model")
    args = ap.parse_args()

    f = Path(args.file).resolve()
    if not f.exists():
        raise SystemExit(f"--file not found: {f}")

    prompt_id = args.prompt_id.strip()
    source = args.source.strip() or "codex"
    model = args.model.strip() or "gpt-5.2"

    hash_script = Path(args.hash_script).resolve()
    if not hash_script.exists():
        raise SystemExit(f"--hash-script not found: {hash_script}")

    artifact_id = f.stem  # ファイルのベース名（拡張子なし）== artifact_id

    # --- YAML (.yaml/.yml) ---
    if f.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise SystemExit("YAML root must be a mapping/object")

        existing_meta = data.get("meta")

        # meta を作り直す（schema_version があればそれだけ残す）
        data["meta"] = rebuild_meta_ai(
            existing_meta,
            artifact_id=artifact_id,
            file_name=f.name,
            prompt_id=prompt_id,
            source=source,
            model=model,
        )

        data = _move_meta_to_top(data)

        # まずは PENDING のまま一度保存（ハッシュが最終構造を反映するように）
        f.write_text(_dump_yaml(data), encoding="utf-8")

        # ハッシュを計算して確定させる
        h = run_sha256(hash_script, f)
        data["meta"]["content_hash"] = h
        data = _move_meta_to_top(data)
        f.write_text(_dump_yaml(data), encoding="utf-8")

        # Verify
        assert_meta_present(f, expected_artifact_id=artifact_id, expected_prompt_id=prompt_id)
        print(f"Stamped AI meta into: {f}")
        return

    # --- Markdown (.md) ---
    if f.suffix.lower() == ".md":
        existing_fm, body = _split_md_front_matter(f.read_text(encoding="utf-8"))
        existing_meta = existing_fm.get("meta") if isinstance(existing_fm, dict) else None

        meta = rebuild_meta_ai(
            existing_meta,
            artifact_id=artifact_id,
            file_name=f.name,
            prompt_id=prompt_id,
            source=source,
            model=model,
        )

        fm = {"meta": meta}

        # まずは PENDING のまま一度保存（ハッシュが最終構造を反映するように）
        f.write_text(_build_md_with_front_matter(fm, body), encoding="utf-8")

        # ハッシュを計算して確定させる
        h = run_sha256(hash_script, f)
        fm["meta"]["content_hash"] = h
        f.write_text(_build_md_with_front_matter(fm, body), encoding="utf-8")

        # Verify
        assert_meta_present_md(f, expected_artifact_id=artifact_id, expected_prompt_id=prompt_id)
        print(f"Stamped AI meta into: {f}")
        return

    raise SystemExit(f"Unsupported file extension for stampingMeta: {f.suffix}")


if __name__ == "__main__":
    main()
