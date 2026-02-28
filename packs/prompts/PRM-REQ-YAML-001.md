---
meta:
  artifact_id: PRM-REQ-YAML-001
  file: PRM-REQ-YAML-001.md
  author: '@juria.koga'
  source_type: human
  source: manual
  timestamp: '2026-03-01T00:14:00+09:00'
  content_hash: aa6f75ac9e315fdf94dac298f1ce4cf221fca7791d1711954343c104026527a9
---
# プロンプトID: PRM-REQ-YAML-001

# 目的: PLN-PLN-TBL-001.yaml（検査設計対応表）から、要件定義の雛形（REQ-REQ-BASE-001.yaml）を自動生成し、

# AI用metaをstampingMeta.pyで確定する。

あなたはClineです。ローカルリポジトリ "AIDD-QualityGates" 上で作業します。

---

## 1) 生成タスク

以下のYAMLを読み取り、要件定義の雛形YAMLを新規作成してください。

- 入力(YAML): artifacts\planning\PLN-PLN-TBL-001.yaml
- 出力(YAML): artifacts\requirements\REQ-REQ-BASE-001.yaml

目的は「機械的に検知・抑止する検査設計」を、要件（FNC/NFR/TRACE）に落とし込むことです。
入力YAML内の machine_checks を主なソースとして、REQを構造化してください。

---

## 2) 出力YAMLの必須要件（MUST）

### 2.1 YAMLトップレベル構造

出力YAMLは必ずトップレベルに以下2つのセクションを持つこと。

- meta:
- requirements:

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

- meta.artifact_id: "REQ-REQ-BASE-001"
- meta.file: "REQ-REQ-BASE-001.yaml"
- meta.author: "gpt-5.2"
- meta.source_type: "ai"
- meta.source: "PRM-REQ-YAML-001"
- meta.model: "gpt-5.2"
- meta.timestamp: 何らかの値（後で stampingMeta.py が上書きするため、仮でよい）
- meta.content_hash:"PENDING"

※文字列はダブルクォートで囲む。

### 2.3 requirements（構造）

requirements:
functional: # 機能要件（検査レイヤ/ゲート/レポート生成など）- id: string
title: string
derivedfrom: [string, ...]
description: string
input_artifacts: [string, ...]
method: string
pass_criteria: string
output_artifacts: [string, ...]
priority: string # MUST/SHOULD/COULD
non_functional: # 非機能（再現性・監査性・運用性など）- id: string
title: string
derivedfrom: [string, ...]
description: string
metric: string
target: string
measurement: string
priority: string
traceability: # トレース運用ルール - id: string
title: string
derivedfrom: [string, ...]
rule: string
enforcement: string # CI gate / warning / manual
priority: string

---

## 3) 変換ルール（最重要）

### 3.1 基本

- 入力の mappings[].machine_checks[] を1件につき、最低1つの functional 要件に変換する。
- derivedfrom は必ず以下を含める：
  - "PLN-PLN-TBL-001"
  - 対応する machine_check.id（例: "MC-PLN-INT-001"）
- ID規約：
  - functional は "REQ-REQ-FNC-###"
  - non_functional は "REQ-REQ-NFR-###"
  - traceability は "REQ-REQ-TRC-###"
    ※### は 001 から連番でOK。

### 3.2 機能要件（functional）

- title は machine_check.name をベースにする。
- description/method/pass_criteria/input_artifacts/output_artifacts は machine_check から写経し、必要なら短く整形する。
- priority は原則 MUST。ただし以下は SHOULD でもよい：
  - SAST/メトリクス系（無意味コード検知）が運用段階で導入になるなら SHOULD にして良い
  - まだツールが無い場合は COULD でも可（ただし理由をdescriptionに書く）

### 3.3 非機能要件（non_functional）

- 「再現性欠如（揺れ）」に関する machine_checks は non_functional にも要件を起こす。
  - metric/target/measurement をTODOでよいので埋める（数値を勝手に作らない）
- 監査性（meta/content_hash/証跡）に関する要件も1つ以上起こす。

### 3.4 トレーサビリティ（traceability）

- derivedfrom / tracesto / checklistresults の扱いに関する運用ルールを最低2件作る。
  - 例: "全REQは derivedfrom にPLN IDを必須とする"
  - 例: "G3でschema NGはFail、G2でTodo残はFail、WarningはAllureに残す"
- enforcement を "CI gate" / "warning" / "manual" で明記する。

---

## 4) 生成後に必ず実行するコマンド（MUST）

YAMLを作成・保存したら、必ず以下コマンドを「そのまま」実行し、metaを確定させること：

python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingMeta\stampingMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\artifacts\requirements\REQ-REQ-BASE-001.yaml" --prompt-id "PRM-REQ-YAML-001" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"

---

## 5) 完了条件

- [ ] artifacts\requirements\REQ-REQ-BASE-001.yaml が作成されている
- [ ] requirements.functional に machine_checks の主要項目が落ちている
- [ ] derivedfrom が "PLN-PLN-TBL-001" と machine_check.id を含む
- [ ] stampingMeta.py 実行に成功し meta.content_hash が PENDING ではなくなっている
