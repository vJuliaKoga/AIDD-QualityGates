---
meta:
  artifact_id: PLN-PLN-SOLUTION-001
  file: PLN-PLN-SOLUTION-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:07:03+09:00'
  model: gpt-5.2
  content_hash: b02d65677419135f212f5fce1cd46d452ab73fc2feda080f5d7c305a94fe42cf
---




## 6. ソリューション概要（2層構造）

### 6.1 CheckFlow（視座共有＋人の最終判断）

「押せば展開されるQAワークフロー」UI。工程タブ → タスク展開 → 観点/テンプレ/例/参照 → Done/Abort。

- 工程タブ：[企画][要件][基本設計][詳細設計][実装][テスト]（段階導入では表示制御）
- タスクはTodo→展開→Done/Abort（理由必須）→次項目Unlock
- 出力は `checklistresults.json`（チェック者・時刻・理由・エビデンス参照）

**Coachの目的**

- 初学者が「何を見ればいいか」を迷わない（観点をチュートリアル化）
- 「最終判断を人が負う」ことを、Done/Abortの操作とログで強制する
- 監査・説明に耐える「判断ログ」を残す

### 6.2 Gate Runner（自動検証：Docker/CLI）

Coachの出力や、企画/要件/設計のYAML等を入力に、品質ゲートを実行し `output/` と `allure-results/` を生成する。

- 配布はDocker/CLI（CIでもローカルでも同じ結果）
- 出力はAllureに集約し、品質の可視化ハブにする（自動ゲート結果＋人の判断ログ＋ダッシュボード添付）

