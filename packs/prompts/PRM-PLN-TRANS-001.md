---
meta:
  artifact_id: PRM-PLN-TRANS-001
  file: PRM-PLN-TRANS-001.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-01T15:24:00+09:00"
  content_hash: 137f2fb8cf5f836829fabd906b67ded679d17b5a6485d1e5627a3993eaf69e22
---

あなたはAIDD Quality GatesのG4（DeepEval）評価レポート作成者です。
以下の入力ファイルを読み、Run-1（pln_transform: 企画MD↔企画YAMLの変換品質）についてレポートを作成してください。

【レポートID】
RES-PLN-EVAL-001

【出力先】

- output\G4\reports\pln_transform\RES-PLN-EVAL-001.md

【入力（必ず読む）】

1. DeepEval出力JSON（最新のRun-1）

- output\G4\pln_transform\artifacts_planning_yaml\0301_1539.json

2. 参照元（企画MD）

- artifacts\planning\PLN-PLN-FLW-002.md

3. 評価対象（企画YAML分割）

- artifacts\planning\yaml\（ディレクトリ内のyamlを必要に応じて参照）

4. 使用チェックリスト（Run-1はCONSIST中心）

- packs\checklists\CHK-PLN-CONSIST-001.yaml
  （AIDDも使った場合は packs\checklists\CHK-PLN-AIDD-001.yaml も読む）

5. 実行スクリプト（改善提案対象）

- runner\gates\g4_deepeval.py

【このレポートで答えるべき問い（目的）】

- 企画MDの内容が、企画YAMLに「欠落なく」「矛盾なく」「誤った言い換えなく」落ちているか？
- 欠落/矛盾/誤変換がある場合、どのyaml_fileのどのセクションが原因か？
- スクリプト／チェックリスト／プロンプトの当て方の問題で誤って減点していないか？

【出力要件（Markdown）】
必ず以下の章立てで書くこと：

1. 実行サマリ

- run名: pln_transform
- 参照モード: MD
- 評価対象: artifacts\planning\yaml
- テストケース数 / 合格率 / メトリクス平均（JSONから転記）
- 出力JSONファイルへの相対パス

2. 全体所見（結論を3〜6行）

- 変換品質の最重要課題を上位3つにまとめる

3. 重大問題（High Priority）

- 形式：1項目につき
  - 対象yaml_file
  - どのセクション（goal/scope/...）
  - 何が欠けている／矛盾している／誤っているか
  - 根拠：MDの該当箇所（短い引用/要約）＋ DeepEvalの判定理由（geval_jsonやreasonの該当部分）
  - 修正案：YAML側の追記/修正案（箇条書きで具体）

4. 中程度問題（Medium Priority）

- 上と同様だが件数は多くてもOK

5. スクリプト改善提案（g4_deepeval.py）

- 「今回の結果が正しく集計できているか」「不要観点で減点していないか」「timeout要因」があれば
  - 具体的な修正ポイント（関数名/変数名レベルで）
  - 最小パッチ案（疑似差分でOK）

6. 次アクション

- ①YAML修正の順番（どれから直すか）
- ②再実行の条件（どのRunを回すか）
- ③合格基準（今回のRun-1での到達目標）

【禁止】

- ふわっとした一般論だけで終わらせない
- 根拠（どのyaml_file／どのMD箇所／どのjsonキー）を必ず添える
- Run-2（充足）に属する話（AIDD観点の不足）と混ぜない
