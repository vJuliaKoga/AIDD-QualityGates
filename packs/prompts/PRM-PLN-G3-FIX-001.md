---
meta:
  artifact_id: PRM-PLN-G3-FIX-001
  file: PRM-PLN-G3-FIX-001.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-01T18:53:00+09:00"
  content_hash: 121658052f315f8d3a412fe15b68860e4b2764c228972055c678a576a879669b
---

あなたはリポジトリ内のPLN成果物（YAML）を、G3 schema（pln_canonical_v1）に必ず通るように最小差分で修正する担当です。
今回「修正」工程が追加され、changelog等の構造差分が混入してG3でFAILするケースがあるため、FAILしたら必ず修正してください。

# 目的

- g3_scheme（G3 Schema検証）をPASSさせる
- 変更は「schemaエラー解消に必要な最小限」に限定する（過剰修正禁止）
- “修正工程”で追加された変更履歴（changelog / change_log 等）が原因でFAILする場合は、必ず「metaから出す」方針で直す

# 実行

1. まずG3を実行し、エラーを取得する
   - 対象ディレクトリ：artifacts\planning\yaml\v2
   - コマンド例（repo root想定）:
     python runner/gates/g3_schema.py packs/pln_pack/schemas/pln_canonical_v1.schema.json <対象YAMLまたはディレクトリ> output/G3
   - g3_schema.py は JSON Schema Draft2020-12 で検証し、FAIL時に errors[].json_path と message を出力する

2. 出てきた errors を1件ずつ潰す形でYAMLを修正する
   - errors の json_path を必ず手掛かりにして、原因箇所を特定する
   - 修正後にG3を再実行し、PASSするまで繰り返す

# “修正工程”追加に伴うよくあるFAILの直し方（重要）

- pln_canonical_v1 では meta は additionalProperties=false で、metaに許可されていないキーがあるとFAILする
- したがって meta.change_log / meta.changelog / meta.changeLog 等がある場合は、必ず meta から削除して「外に出す」こと

## change_log を “metaから出す” 具体ルール

- 変更履歴の内容は失わない
- 移動先は以下の優先順で使う（schemaに適合する形にする）:
  1. 既存の top-level `changes`（配列）があるならそこへ追記
  2. `changes` が null / 無いなら、配列として新設してそこへ入れる
- 形式例:
  meta:
  ...（許可キーのみ）
  changes:
  - "[v2] 〜〜"
  - "[v2] 〜〜"

# schema準拠の必須要件（抜けやすいので必ず確認）

- top-level 必須キー（meta, derived_from, rationale, changes, ssot_note, artifact_kind, primary_section, goal, problem, scope, constraints, architecture, workflow, score_policy, ai_quality_requirements, inspection_design, config_artifacts, id_issuer, integration, traceability）が揃っていること
- meta は必須キー（artifact_id, file, author, source_type, source, prompt_id, timestamp, model, content_hash, schema_version）を持ち、かつそれ以外のキーを持たないこと
- schema_version は "pln_canonical_v1" であること

# メタ更新ルール（最小限＆一貫性）

- 今回の修正に合わせて meta.prompt_id は PRM-PLN-FIX-002 にする
- timestamp は更新（ISO文字列でOK）
- content_hash も更新（あなたの手順で一貫して再計算できるなら更新。できない場合は、既存運用のルールに従う）
- それ以外のフィールドは不用意に変えない

# 禁止事項

- schemaを緩める（additionalPropertiesを安易にtrueにする等）行為は禁止
- 依存追加・大規模リファクタ・関係ないファイル編集は禁止
- “通すためだけ” のダミー値追加は禁止（意味を保ったまま整形・移動で直す）

# 最終成果

- G3がPASSすること
- 何をどう直したかを、変更点として簡潔に報告（例: meta.change_log を changes に移動し、metaの未許可キーを除去、など）
