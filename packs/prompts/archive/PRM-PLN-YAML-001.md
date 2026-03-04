---
meta:
  artifact_id: PRM-PLN-YAML-001
  file: PRM-PLN-YAML-001.md
  author: '@juria.koga'
  source_type: human
  source: manual
  timestamp: '2026-02-28T21:59:00+09:00'
  content_hash: a588fe8e7beab51fc1fe317ccf040253960437c1e8668667e2ffb23c825ac6f0
---
# プロンプトID: PRM-PLN-YAML-001

# 目的: artifacts\planning\PLN-PLN-GOAL-001.md を読み取り、artifacts\planning\PLN-PLN-GOAL-001.yaml を作成する（Goal成果物のYAML化）。

# 注意: ID規約（{PREFIX}-{PHASE}-{PURPOSE}-{NNN}）に従い、出力YAMLの meta.artifact_id / meta.file を必ず整合させること。

あなたはClineです。ローカルリポジトリ "AIDD-QualityGates" 上で作業します。

---

## 1) 生成タスク

以下のMarkdownを入力として読み取り、Goal成果物のYAMLを新規作成してください。

- 入力(Markdown): artifacts\planning\PLN-PLN-GOAL-001.md
- 出力(YAML): artifacts\planning\PLN-PLN-GOAL-001.yaml

このYAMLは「企画全体」ではなく、あくまで Goal（PLN-PLN-GOAL-001）に関する情報だけを構造化してください。
Markdown内に他の章（背景/課題/設計など）が含まれていても、Goalとして必要な情報だけを抽出します。

---

## 2) 出力YAMLの必須要件（MUST）

### 2.1 YAMLトップレベル構造

出力YAMLは必ずトップレベルに以下2つのセクションを持つこと。

- meta:
- goal:

### 2.2 meta（キーを統一して手動と整合させる）

metaは必ず以下キーを持つこと（キー名は固定）。

- artifact_id
- file
- author
- source_type
- source
- timestamp
- content_hash
- model

AI生成物として、値は以下に従うこと。

- meta.artifact_id: "PLN-PLN-GOAL-001"
- meta.file: "PLN-PLN-GOAL-001.yaml"
- meta.author: "gpt-5.2"
- meta.source_type: "ai"
- meta.source: "PRM-PLN-YAML-001"
- meta.model: "gpt-5.2"
- meta.timestamp: 何らかの値（後で stampingMeta.py が上書きするため、仮でよい）
- meta.content_hash:"PENDING"（最初は必ずPENDING。後で stampingMeta.py が確定値を入れる）

※@など記号を含む可能性のある文字列は必ずダブルクォートで囲む。

### 2.3 goal（構造）

goalセクションは必ずこの構造にすること。

goal:
summary: string
primary_goal: string
secondary_goals: [string, ...]
success_criteria: - metric: string
target: string
measurement: string
scope_in: [string, ...]
scope_out: [string, ...]
abort_conditions: [string, ...]
notes: [string, ...]

---

## 3) 抽出ルール（Markdown→YAML）

- primary_goal:
  - Markdownの「2.1 Primary Goal」配下の文章をそのまま（要約しすぎない）
- secondary_goals:
  - Markdownの「2.2 Secondary Goals」の箇条書きをそのまま配列にする
- summary:
  - 上記を踏まえた1文の要約（Markdownに忠実に、勝手に内容を追加しない）
- success_criteria:
  - Markdownに明確なKPIが無い場合は、1件だけプレースホルダーを入れる（数値を勝手に作らない）
  - 例:
    metric: "TODO: KPI（例：手戻り削減率/乖離率/レビュー指摘件数）"
    target: "TODO: 目標値（数値は後で定義）"
    measurement: "TODO: 計測方法（例：PRレビュー/チケット/テスト結果）"
- scope_in / scope_out / abort_conditions:
  - Markdownに明確に書かれていない場合は、空配列にせず、TODOのプレースホルダー文字列を1つ入れる（後続のチェックで「未定義」を見える化するため）
- notes:
  - Markdown内に「スコアは合否の唯一根拠にしない」「0.70未満は警告」等の運用方針があれば箇条書きでnotesへ

---

## 4) ファイル作成時の注意

- UTF-8で保存
- YAMLのキー順は読みやすさ優先（ソートしない）
- 余計なセクションを作らない（goal以外を入れない）

---

## 5) 生成後に必ず実行するコマンド（MUST）

YAMLを作成・保存したら、必ず以下コマンドを「そのまま」実行し、metaを確定させること：

python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingMeta\stampingMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\artifacts\planning\PLN-PLN-GOAL-001.yaml" --prompt-id "PRM-PLN-YAML-001" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"

---

## 6) 完了条件（チェックリスト）

- [ ] artifacts\planning\PLN-PLN-GOAL-001.yaml が作成されている
- [ ] YAMLが meta + goal 構造になっている
- [ ] meta.content_hash が最終的に PENDING ではなくなっている（スタンプ後）
- [ ] meta.source が "PRM-PLN-YAML-001" になっている
