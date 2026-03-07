---
meta:
  artifact_id: PLN-PLN-CHECKLIST-001
  file: PLN-PLN-CHECKLIST-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: "2026-03-03T21:06:59+09:00"
  model: gpt-5.2
  content_hash: aa6a48b2d0510a8c3430f9709d398f7dee90a5bd8fcbd469ab8501a05549ed3f
---

## 10. チェックリスト資産（標準搭載）

### 10.1 要件妥当性チェックリスト（CHK-REQ-REVIEW-001）

本ツールの中核となる「要件レビュー」チェックリスト。

- human_review
- 重み付け、判定ロジック
- 検証可能性／AI可読性／トレーサビリティ／スキーマ準拠／運用考慮（ログ・権限）など、AIDDで落ちがちな観点をまとめて提供

### 10.2 企画MD↔企画YAML整合性（PLNパックに搭載）

企画を"機械可読化"する入口として、企画文書をYAML化し、構造・ID・metaを検証するゲートを置く（詳細はPLNパックのチェックリストに反映）。
（この思想は planning_v1 の工程パック構成例にも含まれる）
