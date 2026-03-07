from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent

    exclude_dirs = [
        (root / ".git").resolve(),
        (root / "tools" / "checklist" / "CheckFlow" / "node_modules").resolve(),
        (root / "tools" / "checklist" / "CheckFlow" / "server" / "node_modules").resolve(),
    ]

    def is_excluded(p: Path) -> bool:
        pr = p.resolve()
        for ex in exclude_dirs:
            exs = str(ex)
            prs = str(pr)
            if prs == exs or prs.startswith(exs + os.sep):
                return True
        return False

    def children(d: Path) -> tuple[list[Path], list[Path]]:
        try:
            entries = list(d.iterdir())
        except PermissionError:
            return [], []

        files = sorted([e for e in entries if e.is_file()], key=lambda x: x.name.lower())
        dirs = sorted([e for e in entries if e.is_dir()], key=lambda x: x.name.lower())
        return files, dirs

    lines: list[str] = ["C:."]

    def walk(d: Path, prefix: str) -> None:
        files, dirs = children(d)

        # files first (tree default)
        for f in files:
            lines.append(f"{prefix}|   {f.name}")

        if files and dirs:
            lines.append(f"{prefix}|")

        for i, sub in enumerate(dirs):
            last = i == len(dirs) - 1
            conn = "\\---" if last else "+---"

            if is_excluded(sub):
                lines.append(f"{prefix}{conn}{sub.name} (excluded)")
                continue

            lines.append(f"{prefix}{conn}{sub.name}")
            child_prefix = prefix + ("    " if last else "|   ")
            walk(sub, child_prefix)

    walk(root, "")

    Path(".cline_tree.txt").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote .cline_tree.txt")


if __name__ == "__main__":
    main()
