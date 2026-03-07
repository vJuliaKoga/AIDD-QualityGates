---
meta:
  artifact_id: PLN-PLN-TRACEABILITY-001
  file: PLN-PLN-TRACEABILITY-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:07:03+09:00'
  model: gpt-5.2
  content_hash: 0de0e2e244f38e7362d061adc738917612f0342559d3b1602753827801ad586d
---




## 11. トレーサビリティ設計（ConTrack前提でも価値が残る形）

### 11.1 2層設計

- **Core（本ツール）**：ID抽出／参照整合（derivedfrom/tracestoの存在確認）／カバレッジ算出／未紐付け一覧／Allure出力
- **Adapter（将来）**：ConTrack API連携（存在確認、リンク生成、関係解決）

この方針により、ConTrackが既にあっても「品質ゲートとしての検査・可視化・ブロック」という価値が本企画側に残る。

