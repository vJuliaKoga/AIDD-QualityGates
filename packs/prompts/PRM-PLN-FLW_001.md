---
meta:
  artifact_id: PRM-PLN-FLW_001
  file: PRM-PLN-FLW_001.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-03T0:27:00+09:00"
  content_hash: f2a14be567789e99720e1468ba33a3cd580a080fde2398450d2eb8d1d6b2524b
---

あなたは「企画書→Canonical YAML化」を行う変換器です。
ただし本タスクではIDの検索・発行・推測・採番を**絶対に行わない**。IDはユーザーが添付した一覧のみが正である。

# 入力

- 企画書: artifacts/planning/PLN-PLN-FLW-003.md
- 構造化テンプレート: artifacts/planning/yaml/pln_canonical_template_v1.yaml
- （参照はしてよいが）ID付与規約: id/id_rules_registry.yaml
  - 注意: 参照のみに限定。IDの発行/検索/更新/次番計算は一切禁止。

# IDソース（唯一の正）

以下のIDリストのみを使用する。ここに無いIDは作らない/補わない/検索しない。

- PLN-PLN-FLW-001
- PLN-PLN-PROB-001
- PLN-PLN-SCOPE-001
- PLN-PLN-CONS-001
- PLN-PLN-DES-001
- PLN-PLN-FLW-002
- PLN-PLN-YAML-001
- PLN-PLN-DES-002
- PLN-PLN-DES-005
- PLN-PLN-DES-006
- PLN-PLN-EVAL-001
- PLN-PLN-DES-003
- PLN-PLN-DES-004
- PLN-PLN-RUN-001
- PLN-PLN-INT-001
- PLN-PLN-UI-001

# 出力（最重要）

- 1つのIDにつき YAMLを1件だけ生成する。
- 各YAMLは次のパスに保存する：
  artifacts/planning/yaml/PLN-PLN-FLW-003/{ID}.yaml
- 追加のindex/meta/content等の分割ファイルは**一切作らない**（禁止）。

# 各YAMLに入れる内容（テンプレ準拠）

- pln_canonical_template_v1.yaml のスキーマに従い、企画書から該当IDに対応する内容だけを抽出して埋める。
- 企画書内の該当セクションは、ユーザーが添付した maps_to_sections を根拠に特定すること。
- 企画書に存在しない情報はテンプレの許容表現で null / "" / TBD などを使い、捏造しない。

# 禁止事項（破ったら失敗）

- IDを新規発行する、registryから検索する、次番を計算する、ID候補を推測する
- 添付リストに無いIDを生成/出力する
- 1IDから複数ファイルを出す（分割ファイル禁止）
- maps_to_sections 以外の根拠で該当箇所を決め打ちする
- 企画書に無い内容を勝手に保管してはならない。"AIによる提案"と明示して別枠に記載すること。

# 実行順序（固定）

For each ID in the list:
A) 添付の title と maps_to_sections を読み取る
B) 企画書から該当セクションを抽出
C) テンプレにマッピングして {ID}.yaml を作成

# このチャットでの出力形式

- 16件のYAMLを、ID順に「ファイルパス」と「YAML全文」を順番に出力する
  例:

  ## artifacts/planning/yaml/PLN-PLN-FLW-003/PLN-PLN-FLW-001.yaml

  ```yaml

  ...
  ```

# 重要：内容の最低品質（ボリューム/粒度）を強制する

- 生成するYAMLは「要約」ではなく「運用に耐える設計ドキュメント」とする。
- 1ファイルあたりの内容量が極端に少ない出力は禁止（10行程度の骨格のみは禁止）。

## 最低ボリューム要件（必須）

各 {ID}.yaml は少なくとも以下を満たすこと：

- “本文フィールド”のうち、箇条書きが合計で最低12項目以上（複数セクション合算でOK）
- 重要セクション（goal/problem/scope/constraints/design/eval/risks/trace のうち該当するもの）を最低3セクション以上埋める
- 各セクションに「なぜそうするか（rationale）」を1〜2文で必ず付ける

## 粒度要件（必須）

- “抽象語だけ”は禁止（例：「品質を上げる」「検証する」だけで終わらせない）
- 必ず「入力→処理→出力」「判定基準」「運用時の例外/Warning」のどれかを含める
- 可能な限り数値/閾値/条件分岐（例：70点/90点、0.70未満Warning等）を明示する

## 横断整合（必須）

- referenced_internal_ids / traceability / links を必ず入れ、関連IDとのつながりを明記する
- 用語（Coach/Runner/Allureなど）はファイル間で表記ゆれ禁止
- “同じポリシー文言”はファイル間で再利用し、勝手に言い換えない

## 生成後セルフチェック（必須）

- 自分の出力を見て「薄すぎる」「抽象的すぎる」場合は、企画書: artifacts/planning/PLN-PLN-FLW-003.mdの内容で補って提出する
