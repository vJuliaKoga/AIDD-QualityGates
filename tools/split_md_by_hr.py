"""Split a Markdown file into blocks separated by horizontal rules (---).

This tool is designed for *lossless* extraction:
- The output files contain the exact bytes between delimiter lines.
- The delimiter line (---) itself is not included.

Filtering:
- Only blocks that contain a heading like `## N. タイトル` near the start are emitted.

Filename:
- Uses the `タイトル` portion.
- Replaces Windows-invalid characters \\/:*?"<>| with `_`.
- Deduplicates with `__2`, `__3`, ...

Prints a summary (filenames, count, lines/bytes) and an extra check for
`エグゼクティブサマリー.md`.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


HEADING_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
INVALID_WIN_CHARS_RE = re.compile(r"[\\/:*?\"<>|]")


def detect_text_encoding(data: bytes) -> str:
    """Best-effort encoding detection without external deps."""
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            pass
    # Last resort: latin-1 never fails; only used for parsing headings.
    return "latin-1"


def sanitize_filename(name: str) -> str:
    name = name.strip()
    name = INVALID_WIN_CHARS_RE.sub("_", name)
    name = name.rstrip(". ")  # Windows doesn't like trailing dot/space
    if not name:
        name = "untitled"
    return name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--scan-lines", type=int, default=40)
    args = ap.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = in_path.read_bytes()
    encoding = detect_text_encoding(raw)

    # Keep exact original line endings/bytes.
    lines = raw.splitlines(keepends=True)

    hr_idx: list[int] = []
    for i, line in enumerate(lines):
        if line.rstrip(b"\r\n") == b"---":
            hr_idx.append(i)

    emitted: list[tuple[str, Path, int, int]] = []  # (name, path, line_count, bytes)
    name_counts: dict[str, int] = {}

    # Each block: after a --- line to before the next --- line.
    for a, b in zip(hr_idx, hr_idx[1:]):
        block_lines = lines[a + 1:b]
        if not block_lines:
            continue

        heading_title: str | None = None

        # "Near the beginning": scan first N lines.
        for scan_line in block_lines[: max(1, args.scan_lines)]:
            try:
                s = scan_line.decode(encoding).rstrip("\r\n")
            except UnicodeDecodeError:
                # If a single line fails (rare), skip it for heading detection.
                continue
            m = HEADING_RE.match(s)
            if m:
                heading_title = m.group(2)
                break

        if not heading_title:
            # Ignore cover/meta blocks.
            continue

        base = sanitize_filename(heading_title)
        name_counts[base] = name_counts.get(base, 0) + 1
        suffix = "" if name_counts[base] == 1 else f"__{name_counts[base]}"
        filename = f"{base}{suffix}.md"
        out_path = out_dir / filename

        # Lossless write: exact bytes.
        data = b"".join(block_lines)
        out_path.write_bytes(data)

        # Stats
        line_count = len(data.splitlines())
        byte_count = len(data)
        emitted.append((filename, out_path, line_count, byte_count))

    # Verification: executive summary file starts with the expected heading.
    exec_file = out_dir / "エグゼクティブサマリー.md"
    exec_ok = "No"
    if exec_file.exists():
        first_line_bytes = exec_file.read_bytes().splitlines(keepends=False)[:1]
        if first_line_bytes:
            try:
                first_line = first_line_bytes[0].decode(encoding)
            except UnicodeDecodeError:
                first_line = ""
            exec_ok = "Yes" if first_line == "## 0. エグゼクティブサマリー" else "No"

    # Print summary ONLY (no content).
    print("Generated files:")
    for filename, _path, line_count, byte_count in emitted:
        print(f"- {filename}\t(lines={line_count}, bytes={byte_count})")
    print(f"File count: {len(emitted)}")
    print(f"Executive summary starts with heading: {exec_ok}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
