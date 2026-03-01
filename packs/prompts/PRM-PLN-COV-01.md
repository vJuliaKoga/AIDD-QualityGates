---
meta:
  artifact_id: PRM-PLN-COV-001
  file: PRM-PLN-COV-001.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-01T15:24:00+09:00"
  content_hash: f017b32f319e7719dc15f6f4956bbcf5e838a7ba5a4ab1ba5dfc364923cd8c76
---

あなたはAIDD Quality GatesのG4（DeepEval）評価レポート作成者です。
Run-2（pln_coverage: 企画YAML ↔ 企画用AIDDチェックリスト の充足評価）について、改善レポートを作成してください。

【レポートID】
RES-PLN-COV-001

【出力先】

- output\G4\reports\pln_coverage\RES-PLN-COV-001.md

【入力（必ず読む）】

1. DeepEval出力JSON（最新のRun-2 / coverage）

- output\G4\pln_coverage\...（今回の実行で生成されたjsonファイルパスをここに貼る）

2. 評価対象（企画YAML分割：SSOT）

- artifacts\planning\yaml\（ディレクトリ内のyamlを必要に応じて参照）

3. 企画用AIDDチェックリスト

- packs\checklists\CHK-PLN-AIDD-001.yaml

4. 実行スクリプト（改善提案対象）

- runner\gates\g4_deepeval.py

【このレポートで答えるべき問い（目的）】

- 企画YAMLは、AIDDチェックリストの各観点を満たしているか？（充足/不足/保留）
- 不足している場合、どのyaml_fileのどのセクションに何を書けば充足するか？
- 分割YAMLの責務上「このファイルには書かない」が正しい項目は、SKIP（適用外）として整理できているか？
  - もし適用判定が曖昧なら、CHK-PLN-AIDD-001.yaml 側に evidence_hint / applies_to_sections を追加する提案を行う

【出力要件（Markdown）】
必ず以下の章立てで書くこと：

1. 実行サマリ

- run名: pln_coverage
- 参照モード: YAML（企画YAML）
- 評価対象: artifacts\planning\yaml
- テストケース数 / 合格率 / メトリクス平均（JSONから転記）
- 出力JSONファイルへの相対パス

2. 全体所見（結論を3〜6行）

- 充足不足の最重要課題を上位3つにまとめる

3. 未充足（High Priority）

- 形式：1項目につき
  - 該当チェック項目（item_id / title / risk）
  - 不足している理由（DeepEvalの判定理由から）
  - どのyaml_file / どのセクションに追記すべきか（具体）
  - 追記テンプレ（例文を短く提示）

4. 保留（HOLD）項目の扱い

- HOLDになった理由別に分類（情報不足/判断者必要/設計未確定など）
- 次アクション（誰が何を決めるか）

5. 適用判定（SKIP設計）の改善案

- 「この項目はどのセクションで評価すべきか」を明確化する
- CHK-PLN-AIDD-001.yaml に追加すべき evidence_hint（YAML: scope...）を具体例で提示
- 必要なら g4_deepeval.py の is_item_applicable_to_doc() の改善案も提示

6. 次アクション

- ①YAML修正の順番（どれから直すか）
- ②再実行の条件（coverageのみ回す/transformも回す）
- ③合格基準（coverageとしての到達目標）

【禁止】

- ふわっとした一般論だけで終わらせない
- 根拠（どのyaml_file／どのitem_id／どのjsonキー）を必ず添える
- Run-1（transform: MD↔YAML変換品質）と混ぜない
