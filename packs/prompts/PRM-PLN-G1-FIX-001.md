---
meta:
  artifact_id: PRM-PLN-G1-FIX-001
  file: PRM-PLN-G1-FIX-001.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-01T20:48:00+09:00"
  content_hash: f77d909cd8d0f93fe773ae3ffed4dd920ea307919d38e40252dbf2f13f2db356
---

あなたはYAML成果物の品質改善担当です。
次の曖昧語検出結果(JSON)を根拠に、artifacts\planning\yaml\v3 配下のYAMLを修正してください。

# 作業ID（ID規約準拠 / G1テスト結果を利用するため G1- を必ず含む）

WORK_ID: PRM-G1-FIX-001

# 入力（根拠データ）

- 曖昧語検出結果: output\G1\artifacts_planning_yaml_v2\0301_2059.json
  - gate: G1_AMBIGUITY
  - findings に記載された (file, line, term, category, context, note, excluded) を参照すること

# 修正対象

- 対象ディレクトリ: artifacts\planning\yaml\v3
- JSON findings の "file" に対応する v3 側の同名ファイルを修正すること
  例: artifacts\planning\yaml\v3\PLN-PLN-AIQUA-002.yaml など

# 修正方針（重要）

1. JSON findings の excluded=false の指摘のみを修正対象とする（excluded=true は変更しない）。
2. 指摘された曖昧語（term）が現れる箇所を、曖昧さが残らない表現に置換する。
   - 置換は文意を保ちつつ「条件/基準/閾値/担当/手順/例外/優先順位」を明示すること。
   - 例: 「必要に応じて」→「以下の条件A/Bのいずれかに該当する場合は〜」のように条件を列挙
   - 例: 「適切に」→「○○の基準(XX)を満たすように」など評価基準を明記
   - 例: 「柔軟に」→「優先順位(1..n)と例外条件を定義し、その範囲内で変更可能」など裁量範囲を限定
   - 例: 「なるべく」→「期限/上限/下限/努力義務の範囲を数値または明確な条件で指定」
3. YAMLの構造（キー、階層、配列、スキーマ意図）は崩さない。必要最小限の差分にする。
4. 変更後に、修正箇所ごとに「何を」「なぜ（JSONのnoteに基づく）」を短く説明する。
5. 出力は以下の2部構成で返すこと：
   A) 変更後のYAML（変更したファイルごとに全文 or 変更ブロックが明確に分かる形式）
   B) 変更サマリ（ファイル名 / 該当term / before→after / 変更理由）

# 参考（検出結果の読み方）

- findings[].file: v2のファイルパス（v3でも同名を想定）
- findings[].line: v2での行番号（v3では行番号がズレる可能性があるので、termとcontext文字列で該当箇所を特定）
- findings[].category: DESC / PROC_REQ / QUOTE など
- findings[].severity: HIGH/MED/LOW（優先度の目安）
- findings[].context と note を必ず根拠として扱う

まず、JSON findings を集計して「修正対象ファイル一覧（excluded=falseのみ）」を提示し、
その後に各ファイルを修正してください。
