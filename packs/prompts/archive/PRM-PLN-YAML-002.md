---
meta:
  artifact_id: PRM-PLN-YAML-002
  file: PRM-PLN-YAML-002.md
  author: '@juria.koga'
  source_type: human
  source: manual
  timestamp: '2026-02-28T22:40:00+09:00'
  content_hash: f17f7bb717d9b0f8e863b3b95bc67145a77c35f17fafcae91d08f2a1d6c1a875
---
# プロンプトID: PRM-PLN-YAML-002

# 目的: 企画全文（PLN-PLN-GOAL-001.md）から SCOPE（PLN-PLN-SCOPE-001）に必要な情報だけを抽出し、

# artifacts\planning\PLN-PLN-SCOPE-001.yaml を新規作成して、AI用metaをstampingMeta.pyで確定する。

あなたはClineです。ローカルリポジトリ "AIDD-QualityGates" 上で作業します。

---

## 1) 生成タスク

入力となるMarkdownは「企画全文」のみ存在します。以下を読み取り、SCOPE成果物のYAMLを新規作成してください。

- 入力(Markdown): artifacts\planning\PLN-PLN-GOAL-001.md
- 出力(YAML): artifacts\planning\PLN-PLN-SCOPE-001.yaml

このYAMLは「企画全体」ではなく、あくまで SCOPE（PLN-PLN-SCOPE-001）に関する情報だけを構造化してください。
企画全文の中から、SCOPEとして必要な情報だけを抽出します。

---

## 2) 出力YAMLの必須要件（MUST）

### 2.1 YAMLトップレベル構造

出力YAMLは必ずトップレベルに以下2つのセクションを持つこと。

- meta:
- scope:

### 2.2 meta（キーは手動/AIで統一する）

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

- meta.artifact_id: "PLN-PLN-SCOPE-001"
- meta.file: "PLN-PLN-SCOPE-001.yaml"
- meta.author: "gpt-5.2"
- meta.source_type: "ai"
- meta.source: "PRM-PLN-YAML-002"
- meta.model: "gpt-5.2"
- meta.timestamp: 何らかの値（後で stampingMeta.py が上書きするため、仮でよい）
- meta.content_hash:"PENDING"（最初は必ずPENDING。後で stampingMeta.py が確定値を入れる）

※文字列はダブルクォートで囲む。

### 2.3 scope（構造）

scopeセクションは必ずこの構造（キー名）にすること。
scope:
summary: string
scope_in: [string, ...]
scope_out: [string, ...]
assumptions: [string, ...]
deliverables: - id: string
name: string
acceptance: [string, ...]
abort_conditions: [string, ...]
traceability:
links_out: - from: string
to: string
relation: string
note: string
terminology:
glossary: - term: string
definition: string
allowed_abbreviations_ref: [string, ...]
qa_from_planning:
required_checks: - id: string
title: string

---

## 3) 抽出ルール（企画全文→SCOPE YAML）

SCOPEは企画全文の以下を優先して抽出すること：

- 「7. 工程パック戦略」：対象工程とパックの範囲
- 「8. 品質保証設計（企画段階から入れる）」：企画段階の必須QA観点（検証可能性/スコープ/運用）
- 「16. 配布形態」「17. ロードマップ」：Phase1の境界（SaaS除外など）
- 「11. トレーサビリティ設計」：Core/Adapterやトレース方針
- 「14. Allureによる可視化」：Allureを必須成果物に含める
- 「6. ソリューション概要」：Coach UI / Gate Runner は必須成果物として deliverables に入れる

未記載のものは空配列にせず、必ず "TODO: ..." を1つ以上入れて薄味を防ぐこと。

deliverablesは必ず以下4つを含める（最低限）：

1. Coach UI
2. Gate Runner（Docker/CLI）
3. Allureレポート集約
4. 企画YAML化テンプレ＋スキーマ（goal.schema.json / scope.schema.json を前提にしてよい）

deliverables[*].id はID規約に従う形式にする（例: "PLN-PLN-DES-001" 等）。
※本文に明示IDが無い場合は、上記例のように妥当なIDを付けてよい。

traceability.links_out は最低限以下を含める：

- from: "PLN-PLN-GOAL-001" to: "PLN-PLN-SCOPE-001" relation: "tracesto"
- from: "PLN-PLN-SCOPE-001" to: "REQ-REQ-SCOPE-001" relation: "derivedfrom"
  未確定なら note に TODO を書く。

---

## 4) 作成後に必ず実行するコマンド（MUST）

YAMLを作成・保存したら、必ず以下コマンドを「そのまま」実行し、metaを確定させること：

python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingMeta\stampingMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\artifacts\planning\PLN-PLN-SCOPE-001.yaml" --prompt-id "PRM-PLN-YAML-002" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"

---

## 5) 完了条件

- [ ] artifacts\planning\PLN-PLN-SCOPE-001.yaml が作成されている
- [ ] YAMLが meta + scope 構造になっている
- [ ] stampingMeta.py の実行に成功している
- [ ] meta.content_hash が最終的に PENDING ではなくなっている（スタンプ後）
- [ ] meta.source が "PRM-PLN-YAML-002" になっている
