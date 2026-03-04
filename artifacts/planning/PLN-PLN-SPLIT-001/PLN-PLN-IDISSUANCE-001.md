---
meta:
  artifact_id: PLN-PLN-IDISSUANCE-001
  file: PLN-PLN-IDISSUANCE-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:07:01+09:00'
  model: gpt-5.2
  content_hash: a06343314ed280c7c693cc0a32f14179292cb5c01ea2c3fdb96feadaa6aeac3e
---




## 13. ID発行・管理（同梱ツールとして明記）

### 13.1 ID発行（issue_id.py）

本企画は、ID採番のための最小ユーティリティを同梱する。`issue_id.py` は以下を行う：

- IDレジストリ（id_rules_registry.yaml）を読み、指定キー（PREFIX-PHASE-PURPOSE）の次IDを発行
- レジストリの `next_nnn` 更新
- 発行ログ（id_issued_log.yaml）への追記
- stdoutへ発行ID出力（他ツール連携を想定）

※現状は single-user 前提（ロックなし）で運用開始し、チーム同時利用が増えた段階でロック/集中管理へ拡張する。

