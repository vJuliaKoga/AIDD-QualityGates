---
meta:
  artifact_id: PRM-PLN-YAML-003
  file: PRM-PLN-YAML-003.md
  author: '@juria.koga'
  source_type: human
  source: manual
  timestamp: '2026-02-28T23:59:00+09:00'
  content_hash: 18d5ee21503f40946edb58ad1b6ad35ab7760f921ec3938faba6235afff51ed2
---
# プロンプトID: PRM-PLN-YAML-003

# 目的: 企画全文（PLN-PLN-GOAL-001.md）とSCOPE（PLN-PLN-SCOPE-001.yaml）を参照し、

# 破綻点→検査レイヤ対応表（PLN-PLN-TBL-001.yaml）を新規作成して、AI用metaをstampingMeta.pyで確定する。

あなたはClineです。ローカルリポジトリ "AIDD-QualityGates" 上で作業します。

---

## 1) 生成タスク

入力は「企画全文」と「SCOPE YAML」を参照して構いません。以下を読み取り、対応表YAMLを新規作成してください。

- 参照(Markdown): artifacts\planning\PLN-PLN-GOAL-001.md
- 参照(YAML): artifacts\planning\PLN-PLN-SCOPE-001.yaml （存在すれば参照。無ければ参照無しでOK）
- 出力(YAML): artifacts\planning\PLN-PLN-TBL-001.yaml

このYAMLは「破綻点（故障モード）→検査レイヤ→機械的検知・抑止」の対応表です。
QA4AIDDの検査設計の核心として、必ず“機械的に検知できる形”で記述してください。

---

## 2) 出力YAMLの必須要件（MUST）

### 2.1 YAMLトップレベル構造

出力YAMLは必ずトップレベルに以下2つのセクションを持つこと。

- meta:
- inspection_design:

### 2.2 meta（キーは手動/AIで統一）

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

- meta.artifact_id: "PLN-PLN-TBL-001"
- meta.file: "PLN-PLN-TBL-001.yaml"
- meta.author: "gpt-5.2"
- meta.source_type: "ai"
- meta.source: "PRM-PLN-YAML-003"
- meta.model: "gpt-5.2"
- meta.timestamp: 何らかの値（後で stampingMeta.py が上書きするため、仮でよい）
- meta.content_hash:"PENDING"

### 2.3 inspection_design（構造）

inspection_design:
description: string
failure_modes: - id: string
name: string
description: string
examples: [string, ...]
inspection_layers: - id: string
name: string
purpose: string
primary_mechanisms: [string, ...]
tools: [string, ...]
mappings: - failure_mode_id: string
layer_ids: [string, ...]
machine_checks: - id: string
name: string
input_artifacts: [string, ...]
method: string
pass_criteria: string
output_artifacts: [string, ...]
notes: [string, ...]

---

## 3) 抽出・作成ルール（重要）

- failure_modes は必ず以下を含める（あなたの対応表を最低限反映）
  - 解釈ズレ
  - 制約無視
  - 過剰修正
  - テスト汚染（報酬ハッキング）
  - 無意味コード（警告回避）
  - 再現性欠如（揺れ）

- inspection_layers は必ず以下の “検査レイヤ” を含める（番号はidに含めてもOK）
  ① 指示品質検査
  ② 出力構造検査（Schema/Contract）
  ③ 変更影響検査（Diff/Trace/Regression）
  ④ 契約・不変条件検査（Invariants）
  ⑤ 再現性・回帰検査（固定/回帰）

- mappings は、各 failure_mode に対して「主に効く検査レイヤ」を layer_ids に列挙し、
  さらに machine_checks を1つ以上必ず付けること。
  machine_checks は “機械的に検知・抑止する” ためのチェック定義で、
  入力（input_artifacts）→手法（method）→合格条件（pass_criteria）→出力（output_artifacts）
  が分かるように書くこと。

- id ルール:
  - failure_mode_id は "FM-PLN-XXX-001" のように一意なIDにする（ID規約に厳密準拠でなくてもOKだが、英数＋番号で統一）
  - inspection_layer_id は "IL-PLN-001" のように一意にする
  - machine_check.id は "MC-PLN-XXX-001" のように一意にする

※もしID規約に完全準拠させたい場合は、artifact_id体系に寄せても良いが、まずは一意性と可読性を優先。

---

## 4) 生成後に必ず実行するコマンド（MUST）

YAMLを作成・保存したら、必ず以下コマンドを「そのまま」実行し、metaを確定させること：

python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingMeta\stampingMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\artifacts\planning\PLN-PLN-TBL-001.yaml" --prompt-id "PRM-PLN-YAML-003" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"

---

## 5) 完了条件

- [ ] artifacts\planning\PLN-PLN-TBL-001.yaml が作成されている
- [ ] YAMLが meta + inspection_design 構造になっている
- [ ] mappings に全 failure_modes が少なくとも1回は登場する
- [ ] 各 mapping に machine_checks が最低1つある
- [ ] stampingMeta.py の実行に成功し、meta.content_hash が PENDING ではなくなっている
