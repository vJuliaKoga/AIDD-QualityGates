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

あなたはAIDD-QualityGatesリポジトリのメンテナです。
次のレビュー報告書を根拠に、企画split MDと対応YAMLを修正してG4(PLN)のFaithfulnessを改善してください。

# 入力（必読）

- レビューMD: output\G4\reports\pln_eval\RES-PLN-G4-REVIEW-001.md

# 対象（基本）

- split MD: artifacts\planning\PLN-PLN-SPLIT-001\*.md
- YAML: artifacts\planning\yaml\*.yaml
- 1:1対応: YAMLの derived_from に書かれた split MD が、そのYAMLの参照（SSOT）です。
  例) artifacts\planning\PLN-PLN-SPLIT-001\PLN-PLN-ALLURE-001.md
  artifacts\planning\yaml\PLN-PLN-ALLURE-001.yaml

# ゴール

- レビューMDに書かれている「改善バックログ / 指摘事項」を反映し、
  1. FaithfulnessのFAIL原因を減らす（SSOT不足・表現ゆれ・過剰補完を潰す）
  2. Coverage未カバー（もし記載があれば）を潰す
  3. Consistencyのノイズ矛盾（derived_from/ artifact_kind 等）を減らす
- “YAMLが正しいのにMDが薄い” 場合は、YAMLから split MDへ根拠として逆輸入してよい。
  ただし「未合意/仮説」は split MD側に（案）（要検討）などのラベルを付けて追記する。

# 重要ルール（破らない）

- 既存ファイル名は維持すること。
- 大きな変更をする場合は、変更前のファイルを archive フォルダへ退避してから上書きすること。
  - 退避先の例:
    - artifacts\planning\archive\PLN-PLN-SPLIT-001\<YYYYMMDD>\...
    - artifacts\planning\archive\yaml\<YYYYMMDD>\...
      ※リポジトリ内の既存の archive 構造がある場合はそれに合わせる。
- derived_from の1:1対応を崩さないこと（参照先MDを変えるなら derived_from も合わせて更新）。
- 追記は「見出しだけ（〜：）」で終わらず、最低でも箇条書き1〜5個は入れる（Coverage安定化のため）。
- YAML側で長文説明がある場合、必要に応じて箇条書き化・分解して読みやすくする（評価の安定化のため）。
- metaやtimestamp等の自動生成/ノイズ項目は、意味のある変更をしない（Consistencyノイズの原因になるため）。

# 作業手順

1. レビューMDを読み、優先度P0→P1→P2の順に、具体的に修正対象ファイル（YAML/MD）を抽出する。
2. 各修正対象について、次のどちらかを判断して実施する：
   A. 「参照MDが薄い」ためにFaithfulnessが落ちている
   -> YAMLの内容から、根拠として妥当な要点（3〜5箇条書き + 例があれば1つ）を split MDへ追記
   B. 「YAMLが参照を超えて書きすぎ」または「表現ゆれ」で落ちている
   -> (B1) 参照に無い断定・推測を弱める / 削除する / （案）に落とす
   -> (B2) split MDとYAMLで用語・表記を統一する（同義語を寄せる）
3. Coverage未カバーがレビューに列挙されている場合：
   - split MDの “見出しだけ” を解消（箇条書き追記）
   - YAML側に用語/キーの表記を合わせる（例: humanreview など）
4. Consistencyのノイズ矛盾がレビューに列挙されている場合：
   - YAMLの値の揺れ（null vs 文字列、%表記 vs 小数表記など）を統一する
   - “仕様上ファイルごとに異なるのが正しい”項目は、値の書き方を揃える（例: changes を常に空配列にする等）
5. 変更したファイル一覧と、変更理由（レビューMDのどの指摘に対応したか）を、最後に短くまとめる。

# 出力要件

- 実際にファイルを編集して反映すること（提案だけで終わらない）。
- 変更前退避（archive）を行った場合は、退避先パスも明記する。
- 最後に以下を必ず出力する：
  - 変更した split MD の一覧
  - 変更した YAML の一覧
  - 各ファイルの変更点サマリ（箇条書き）
  - （可能なら）G4の再実行コマンド例

# ヒント（迷ったら）

- まずはFaithfulnessが極端に低い/問題が大きいファイルから（レビューMDのP0対象）。
- “YAMLが正しい” と判断したら、SSOTである split MDへ要点を逆輸入するのが最短。
- 追記は「短い箇条書き」で良い。長文で増やしすぎない。
