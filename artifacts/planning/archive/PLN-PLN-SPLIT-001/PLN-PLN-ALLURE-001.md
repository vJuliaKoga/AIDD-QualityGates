---
meta:
  artifact_id: PLN-PLN-ALLURE-001
  file: PLN-PLN-ALLURE-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:06:58+09:00'
  model: gpt-5.2
  content_hash: 570b99e56a356dd4b1cbd8e435393138e6a6c709a4f67e4f836661a2603c30df
---




## 14. Allureによる可視化（品質のハブ）

Allure Reportは以下を一元表示する：

- **自動ゲート結果**（G1〜G5, PF）：各ゲートの判定・スコア・エビデンス参照
- **G2（人のチェックリスト）スコア**：人による判断ログ（Done/Abort・理由・証跡リンク）をゲート結果として統合表示
- **重み付き合算スコア**：G1〜G5+PFの各スコアをウェイト定義（9.3節）に基づき合算した総合得点
- **各ゲートの内訳・スコア分布**：ゲート別・評価軸別の得点内訳をグラフで確認できる
- **スコア推移**（Deep Eval/Promptfoo）：モデル変動や改修前後の品質変化をトレンドで可視化
- **Abort分析**（カテゴリ分布、理由品質）：判断回避の常態化を検知する
- **Traceability Matrix**（要件→設計→テストの紐付け）：G5の結果を構造化表示

