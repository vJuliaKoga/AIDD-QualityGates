---
meta:
  artifact_id: PLN-PLN-DATASPEC-001
  file: PLN-PLN-DATASPEC-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:06:59+09:00'
  model: gpt-5.2
  content_hash: f2de9d11734e69933277f31fe8f7c512c6665c9e3a28b019ec4ac04c57f66d99
---




## 15. 具体的なデータ仕様（最低限）

### 15.1 checklistresults.json（Coach出力）

- `checkedby` / `timestamp` / `status(Done|Abort)` / `reason` / `evidencerefs` を保持し、G2が検証する

### 15.2 Gate出力（Runner）

- `output/` に各ゲートのレポートJSON＋サマリ（exitcode含む）
- `allure-results/` を生成してレポートに統合

