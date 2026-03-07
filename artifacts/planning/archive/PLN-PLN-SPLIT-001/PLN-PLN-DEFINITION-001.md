---
meta:
  artifact_id: PLN-PLN-DEFINITION-001
  file: PLN-PLN-DEFINITION-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:07:00+09:00'
  model: gpt-5.2
  content_hash: 5d3a359af976c90a4892f4f69a366d7dfb8c7970a876ee0f50e2900c980c58a3
---




## 4. QA4AIDDの定義（本企画での解釈）

社内定義：

- ① AIに正しく指示を与える
- ② 指示が守られていることを確認する

本企画の実装：

- 正しく指示：構造化テンプレ、曖昧語排除チェック
- 遵守確認：JSON Schema検証、Deep Eval評価、構造一貫性テスト
- 品質可視化：Allure Reportでゲート結果をモニタ

