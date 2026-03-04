"""Batch-normalize meta and re-stamp meta for all .md/.yaml files in a directory.

Workflow per file:
1) Normalize existing meta so ONLY meta.schema_version remains (if present)
2) Run tools/stampingMeta/stampingMeta.py to rebuild meta and set content_hash
3) Verify meta.content_hash is a sha256 hex string (not PENDING)

Prints a summary only (no file contents).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MD_DELIM = "---"


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


def read_content_hash(path: Path) -> str | None:
    suf = path.suffix.lower()
    if suf in (".yaml", ".yml"):
        root = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(root, dict):
            meta = root.get("meta")
            if isinstance(meta, dict):
                h = meta.get("content_hash")
                return str(h) if h is not None else None
        return None

    if suf == ".md":
        fm, _body = _split_md_front_matter(path.read_text(encoding="utf-8"))
        if isinstance(fm, dict):
            meta = fm.get("meta")
            if isinstance(meta, dict):
                h = meta.get("content_hash")
                return str(h) if h is not None else None
        return None

    return None


def file_stats(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    return (len(data.splitlines()), len(data))


def run(cmd: list[str]) -> None:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + "cmd: "
            + " ".join(cmd)
            + "\nstdout:\n"
            + (res.stdout or "")
            + "\nstderr:\n"
            + (res.stderr or "")
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--prompt-id", required=True)
    ap.add_argument("--hash-script", default="tools/hashtag/hashtag_generator.py")
    ap.add_argument("--source", default="codex")
    ap.add_argument("--model", default="gpt-5.2")
    args = ap.parse_args()

    d = Path(args.dir)
    if not d.exists():
        raise SystemExit(f"Directory not found: {d}")

    normalize_script = Path("tools/normalize_meta_schema_version_only.py").resolve()
    stamp_script = Path("tools/stampingMeta/stampingMeta.py").resolve()
    hash_script = Path(args.hash_script).resolve()

    if not normalize_script.exists():
        raise SystemExit(f"Missing: {normalize_script}")
    if not stamp_script.exists():
        raise SystemExit(f"Missing: {stamp_script}")
    if not hash_script.exists():
        raise SystemExit(f"Missing: {hash_script}")

    # Step 1: normalize meta (schema_version only)
    run([sys.executable, str(normalize_script), "--dir", str(d)])

    targets = sorted([p for p in d.glob("*") if p.is_file() and p.suffix.lower() in (".md", ".yaml", ".yml")])

    results: list[tuple[str, str, int, int]] = []  # (file, hash_ok, lines, bytes)
    for p in targets:
        # Step 2: stamp meta
        run(
            [
                sys.executable,
                str(stamp_script),
                "--file",
                str(p),
                "--prompt-id",
                args.prompt_id,
                "--hash-script",
                str(hash_script),
                "--source",
                args.source,
                "--model",
                args.model,
            ]
        )

        # Step 3: verify hash
        h = read_content_hash(p)
        ok = "OK" if (h is not None and SHA256_RE.match(h)) else "NG"
        lines, bytes_ = file_stats(p)
        results.append((p.name, ok, lines, bytes_))

    print("Stamped files:")
    for name, ok, lines, bytes_ in results:
        print(f"- {name}\tcontent_hash={ok}\t(lines={lines}, bytes={bytes_})")
    print(f"File count: {len(results)}")
    print(f"NG count: {sum(1 for _n, ok, *_ in results if ok != 'OK')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
