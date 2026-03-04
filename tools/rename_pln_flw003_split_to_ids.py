"""Rename split Markdown files to Planning IDs.

Purpose:
- Rename files in a directory (produced by split step) to IDs following
  `{PREFIX}-{PHASE}-{PURPOSE}-{NNN}.md`.
- Content is NOT modified.

This script prints only a summary (filenames + lines/bytes).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def file_stats(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    return (len(data.splitlines()), len(data))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dir",
        default="artifacts/planning/PLN-PLN-FLW-003_split",
        help="Target directory containing split markdown files",
    )
    args = ap.parse_args()

    d = Path(args.dir)
    if not d.exists():
        raise SystemExit(f"Directory not found: {d}")

    # Hard-mapped PURPOSE codes chosen to be closest to the Japanese titles.
    # IDs are unique by PURPOSE (NNN fixed to 001).
    mapping: dict[str, str] = {
        "エグゼクティブサマリー.md": "PLN-PLN-EXEC-001.md",
        "背景と課題（Why Now）.md": "PLN-PLN-BACKGROUND-001.md",
        "目的（Goal）.md": "PLN-PLN-GOAL-001.md",
        "対象ユーザー（社内展開）.md": "PLN-PLN-USER-001.md",
        "QA4AIDDの定義（本企画での解釈）.md": "PLN-PLN-DEFINITION-001.md",
        "基本思想（設計哲学）.md": "PLN-PLN-PHILOSOPHY-001.md",
        "ソリューション概要（2層構造）.md": "PLN-PLN-SOLUTION-001.md",
        "工程パック戦略（社内導入を現実にする）.md": "PLN-PLN-PACK-001.md",
        "品質保証設計（企画段階から入れる）.md": "PLN-PLN-QA_DESIGN-001.md",
        "スコア運用ポリシー（重要：合否の唯一根拠にしない）.md": "PLN-PLN-SCORE_POLICY-001.md",
        "チェックリスト資産（標準搭載）.md": "PLN-PLN-CHECKLIST-001.md",
        "トレーサビリティ設計（ConTrack前提でも価値が残る形）.md": "PLN-PLN-TRACEABILITY-001.md",
        "ID規約（本企画に明記して採用）.md": "PLN-PLN-ID_CONVENTION-001.md",
        "ID発行・管理（同梱ツールとして明記）.md": "PLN-PLN-ID_ISSUANCE-001.md",
        "Allureによる可視化（品質のハブ）.md": "PLN-PLN-ALLURE-001.md",
        "具体的なデータ仕様（最低限）.md": "PLN-PLN-DATA_SPEC-001.md",
        "配布形態（社内展開：Phase 1はサーバー不要）.md": "PLN-PLN-DISTRIBUTION-001.md",
        "ロードマップ（社内展開）.md": "PLN-PLN-ROADMAP-001.md",
        "成功指標（KPI）.md": "PLN-PLN-KPI-001.md",
        "リスクと対策（最初から明記）.md": "PLN-PLN-RISK-001.md",
        "CI品質保証（Docker）とワークフローツールの接続（実装方針）.md": "PLN-PLN-CI_INTEGRATION-001.md",
        "Coach UI 詳細設計.md": "PLN-PLN-COACH_UI-001.md",
    }

    renamed: list[tuple[str, str, int, int]] = []
    missing: list[str] = []

    for src_name, dst_name in mapping.items():
        src = d / src_name
        dst = d / dst_name
        if not src.exists():
            missing.append(src_name)
            continue

        # Overwrite OK: remove destination if exists.
        if dst.exists():
            dst.unlink()

        src.rename(dst)
        lines, bytes_ = file_stats(dst)
        renamed.append((src_name, dst_name, lines, bytes_))

    # Summary only
    print("Renamed files:")
    for src_name, dst_name, lines, bytes_ in renamed:
        print(f"- {src_name} -> {dst_name}\t(lines={lines}, bytes={bytes_})")

    if missing:
        print("Missing sources (not renamed):")
        for m in missing:
            print(f"- {m}")

    # Final directory listing (IDs only)
    final_files = sorted([p for p in d.glob("*.md")])
    print("\nFinal files:")
    for p in final_files:
        lines, bytes_ = file_stats(p)
        print(f"- {p.name}\t(lines={lines}, bytes={bytes_})")
    print(f"File count: {len(final_files)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
