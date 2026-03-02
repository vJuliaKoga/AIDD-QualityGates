---
meta:
  artifact_id: PRM-PLN-G4-FIX-001
  file: PRM-PLN-G4-FIX-001.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-01T15:24:00+09:00"
  content_hash: 137f2fb8cf5f836829fabd906b67ded679d17b5a6485d1e5627a3993eaf69e22
---

あなたはAIDD-QualityGatesリポジトリの「planning/yaml」整備担当です。
以下の評価レポートと評価JSON（DeepEval出力）に基づき、v1フォルダ内のYAMLを修正して、v2フォルダへ保存してください。
目的は「評価がFAILのものを最優先で修正」し、チェックリスト（特にCONSIST）を満たすことです。

# 入力（参照）

- 評価レポート: output\G4\reports\pln_transform\RES-PLN-TRANS-001.md
- DeepEval JSON: output\G4\pln_transform\artifacts_planning_yaml\0301_1539.json

# 対象フォルダ

- 入力（修正前）:
  C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\artifacts\planning\yaml\v1
- 出力（修正後）:
  C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\artifacts\planning\yaml\v2

# 最重要方針

1. まず FAIL の修正（tr_success=false の対象）を最優先する
2. 修正は「最小変更」を基本とし、既存の構造・意図を壊さない
3. TODO / T.B.D / 空配列など、チェックリストに抵触しそうな曖昧値は残さない（可能なら具体化）
4. 参照整合性（derived_fromの実在パス）を必ず正す
5. 変更した箇所は各YAMLの meta.change_log（なければ meta に追加）へ要点を1〜3行で記録する

# 修正の優先順位（レポート指摘に従う）

A. derived_from の参照が "PLN-PLN-FLW-001.md" を指している場合は、
実在する "artifacts/planning/PLN-PLN-FLW-002.md" に置換する（アンカーがあるなら維持/補正）
B. PLN-PLN-GOAL-001.yaml の goal 配下で、必須キー欠落が疑われるため以下を満たす

- goal.primary_goal
- goal.success_criteria
- goal.scope_in
- goal.scope_out
- goal.abort*conditions
  もし scope*\* や abort_conditions の実体が別ファイル（例: PLN-PLN-SCOPE-001.yaml）にあるなら、
  その内容をコピーして埋める（summary だけで済ませない）
  C. 他の FAIL 対象も、チェックリスト（CHK-PLN-CONSIST-001）に抵触し得る「必須キー不足」「参照不整合」を優先して直す

# 具体的な作業手順

1. DeepEval JSON（0301_1539.json）を読み、details[].tr_success=false の yaml_file を FAIL対象として一覧化
2. 各 FAIL YAML（v1から読み込み）について、上記A/B/Cの順で修正
3. 修正後のYAMLを v2 に同名で保存（ファイル名は変えない）
4. v2出力後、あなたの最終回答に以下を必ず含める：
   - 修正したファイル一覧（FAIL→修正内容の要約）
   - 特に derived_from 置換の対象件数
   - PLN-PLN-GOAL-001.yaml で追加/修正したキー一覧

# 厳守ルール

- YAMLのインデント/型（配列・辞書・文字列）を破壊しない
- 既存キーを削除しない（不要と思っても残す）
- 不明な値は「推測で創作」しない。既存YAMLや関連YAMLから抽出できる場合のみ具体化し、それも難しければ“欠落扱いを避ける”最小安全策（例: 空でない短文）を採るが、その場合は change_log に「根拠不足」を明記する
- 出力は必ず v2 に行う（v1は変更しない）

# 追加ヒント（レポートの指摘を反映）

- 多数のFAILはFaithfulness評価のLengthFinishReasonError起因だが、ここではYAML側の「明確な整合性不備（derived_from、必須キー欠落）」を優先して直す
- GOALは summary だけでなく、scope_in/out/abort_conditions を実体キーとして持つことを優先する

それでは実行してください。
