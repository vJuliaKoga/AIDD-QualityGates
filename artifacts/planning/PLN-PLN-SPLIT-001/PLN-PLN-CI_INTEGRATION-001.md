---
meta:
  artifact_id: PLN-PLN-CI_INTEGRATION-001
  file: PLN-PLN-CI_INTEGRATION-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:06:59+09:00'
  model: gpt-5.2
  content_hash: 7056c1d6b59c9bfcc30b984bf2573c34f28b2f867f102f8ab339962894c24230
---




## 20. CI品質保証（Docker）とワークフローツールの接続（実装方針）

### 20.1 基本方針（役割分担）

- **CI（Gate Runner / Docker）**：自動評価を実行し、各ゲート・各評価軸のスコアを **機械可読な成果物**として出力する（再現可能・比較可能）。
- **ワークフローツール（最終工程）**：チェックリスト（Coach相当）の入力・承認を行い、CI成果物をアップロードして **最終サマリを1枚に集約**する。
- **証跡ハブ（Allure）**：自動ゲート結果＋人の判断ログ（理由・証跡リンク）＋サマリを統合して保管する（後追い説明可能性の担保）。

### 20.2 接続フロー（推奨）

1. CIで Gate Runner を実行（G1/G3/G4/G5/PF など）
   - 出力：`output/*.json`（ゲート別JSON）, `allure-results/`（Allure用）, 付随証跡（差分/リンク/ログ）
2. ワークフローツール最終工程で CI成果物（zip等）をアップロード
3. 同工程でチェックリスト入力を確定（Coach相当）
4. 集約コマンド（軽量）で以下を生成し、Allureに統合
   - 合計点（自動＋チェックリスト）
   - スコア分布（軸別/ゲート別）
   - 判定（**最終は人のDone/Abortを主**、自動はWarn/Infoを中心）

### 20.3 成果物仕様（最低限）

- **自動評価成果物（CI）**：各ゲートJSONに以下を含める
  - `gate_id` / `axis_scores`（評価軸ごとの点数）/ `score_total` / `pass|warn|fail` / `evidence`（根拠参照）
- **チェックリスト成果物（Workflow/Coach）**：`checklistresults.json` 相当
  - `item_id` / `risk_level` / `selection` / `score` / `reason` / `evidence_refs`

### 20.4 採点UI案（チェックリスト：リスクレベル×選択式）

- チェック項目は **リスクレベル（High/Med/Low）** を持たせ、重み付けできるようにする。
- 入力は **上下選択ボックス（例：OK / Concern / NG）** を基本にして採点負荷を下げる。
- `Concern/NG` は原則 **理由必須**（証跡リンク/該当箇所参照を推奨）として、形骸化を抑止する。

### 20.5 判定ポリシー（スコアの扱い）

- **スコアは合否の唯一根拠にしない**（最終判断は人のDone/Abort）。
- 一方で運用上の安全策として、**0.70未満は必ずWarning**を出す（劣化検知・再確認トリガ）。
- "ブロック（Fail）"にする条件は、重大ゲート（例：スキーマ逸脱、必須情報欠落等）に限定し、段階的に導入する。

