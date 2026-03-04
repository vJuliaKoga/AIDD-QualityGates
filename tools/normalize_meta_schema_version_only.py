"""Normalize meta to only keep meta.schema_version (if present).

Rules:
- If a YAML/MD file has no meta, do nothing.
- If meta exists and meta.schema_version exists, keep ONLY schema_version.
- Otherwise (meta exists but no schema_version), remove meta entirely.

This is intended as a pre-step before tools/stampingMeta/stampingMeta.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


MD_DELIM = "---"


def _dump_yaml(data: dict) -> str:
    return yaml.dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        Dumper=yaml.SafeDumper,
    )


def _split_md_front_matter(text: str) -> tuple[dict | None, str]:
    lines = (text or "").splitlines(keepends=True)
    if not lines:
        return None, ""
    if lines[0].strip() != MD_DELIM:
        return None, text
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == MD_DELIM:
            end_idx = i
            break
    if end_idx is None:
        return None, text
    fm_text = "".join(lines[1:end_idx])
    body = "".join(lines[end_idx + 1:])
    try:
        fm = yaml.safe_load(fm_text)
    except Exception:
        fm = None
    return fm if isinstance(fm, dict) else None, body


def _build_md(front_matter: dict, body: str) -> str:
    fm_yaml = _dump_yaml(front_matter).rstrip() + "\n"
    return f"{MD_DELIM}\n{fm_yaml}{MD_DELIM}\n\n{body or ''}"


def normalize_mapping(root: dict) -> tuple[dict, bool]:
    """Returns (new_root, changed)."""
    if not isinstance(root, dict):
        return root, False
    if "meta" not in root:
        return root, False
    meta = root.get("meta")
    if not isinstance(meta, dict):
        # Remove non-dict meta
        new_root = dict(root)
        new_root.pop("meta", None)
        return new_root, True
    if "schema_version" in meta:
        new_meta = {"schema_version": meta.get("schema_version")}
        if meta == new_meta:
            return root, False
        new_root = dict(root)
        new_root["meta"] = new_meta
        return new_root, True
    # meta exists but schema_version missing => remove meta
    new_root = dict(root)
    new_root.pop("meta", None)
    return new_root, True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pattern", default="*", help="Glob inside dir, default: *")
    args = ap.parse_args()

    d = Path(args.dir)
    if not d.exists():
        raise SystemExit(f"Directory not found: {d}")

    changed = 0
    scanned = 0

    for p in sorted(d.glob(args.pattern)):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf not in (".yaml", ".yml", ".md"):
            continue
        scanned += 1

        if suf in (".yaml", ".yml"):
            root = yaml.safe_load(p.read_text(encoding="utf-8"))
            root = root or {}
            if not isinstance(root, dict):
                continue
            new_root, did = normalize_mapping(root)
            if did:
                p.write_text(_dump_yaml(new_root), encoding="utf-8")
                changed += 1
            continue

        # .md
        text = p.read_text(encoding="utf-8")
        fm, body = _split_md_front_matter(text)
        if not isinstance(fm, dict) or "meta" not in fm:
            continue
        new_fm, did = normalize_mapping(fm)
        if did:
            p.write_text(_build_md(new_fm, body), encoding="utf-8")
            changed += 1

    print(f"Scanned: {scanned}")
    print(f"Changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
