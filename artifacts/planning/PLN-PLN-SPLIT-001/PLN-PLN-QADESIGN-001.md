---
meta:
  artifact_id: PLN-PLN-QADESIGN-001
  file: PLN-PLN-QADESIGN-001.md
  author: gpt-5.2
  source_type: ai
  source: codex
  prompt_id: PRM-PLN-MD-001
  timestamp: '2026-03-03T21:07:02+09:00'
  model: gpt-5.2
  content_hash: fe048cf2ea213efa489912e0c86757e55abd32f23f9375f0070d51144a93fa6b
---




## 8. 品質保証設計（企画段階から入れる）

### 8.1 企画段階で必須にするQA観点（PLNパック）

企画段階で品質が決まるため、PLNパックには最低限以下を標準装備する：

1. **検証可能性**：成功条件/KPIが測定可能で、テスト可能な言葉か
2. **スコープ**：スコープ内/外、Abort条件が事前に定義されているか
3. **リスク/運用**：運用保守・証跡・権限の考慮があるか（最低限の宣言）

※この"企画→要件へトレース可能"を自動検証できるよう、企画内の主張（Goal/Prob/Scope/Cons等）にPLN-IDを付与し、要件側の `derivedfrom` へ接続する方針を採用する。

### 8.2 品質ゲート（G1〜G5 + PF）設計

本企画の品質ゲートは「構造の逸脱を最大リスク」として設計する。

#### Gate一覧（工程横断）

| Gate | 内容 | 入力 | 出力 | ツール |
| ---- | ---- | ---- | ---- | ------ |
| G1 | 曖昧語チェック + 内容lint | `.yaml` / `.md` | `ambiguityreport.json` | 曖昧語検出ツール |
| G2 | Checklist完了検証（Coach判断ログ） | `checklist.json` | `checklistvalidation.json` | チェックリストツール |
| G3 | Schema検証 + 構造lint | `*.yaml` | `schemareport.json` | 構造解析ライブラリ |
| G4 | Deep Evalスコアリング | `prompts/`, `requirements/` | `deepevalscores.json` | DeepEval |
| G5 | トレーサビリティ（全ID参照） | 全ID参照マトリクス | `tracematrix.json` | 整合性検証ツール |
| PF | Promptfoo評価 | `prompts/`, `configs/` | `promptfooresults.json` | Promptfoo |

#### 設計崩壊防止における各ゲートの役割

- **G1 (Ambiguity Check)**：要件定義の「揺れ」を初期段階で摘み取り、後工程での解釈不一致による手戻りを防ぐ。
- **G2 (Checklist Validation)**：文脈に応じた「人間による高度な判断」を構造化データとしてCIに接続する。
- **G3 (Schema/Structure)**：設計の整合性を強制し、将来的な改修コスト増大（技術的負債の罠）を阻止する。
- **G4 (Deep Eval)**：AIによる生成物の整合性（Faithfulness等）を定量化し、出力品質の客観的指標とする。
- **G5 (Traceability)**：要件IDと実装の紐付けを検証。要求のない実装（孤立した定義）や実装漏れを機械的に特定する。
- **PF (Promptfoo)**：プロンプト変更時の性能退行（リグレッション）を数値化し、出力の安定性を担保する。

#### 統合ゲートの効率性

これら全てのゲート結果は、CI/CDパイプライン上で単一の「統合報告書（JSON）」として集約される。これにより、判定箇所を一元化し、パイプラインの実行パフォーマンスを最大化させる。

