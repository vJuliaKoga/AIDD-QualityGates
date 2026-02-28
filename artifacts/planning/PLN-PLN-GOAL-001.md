```yaml
meta:
  artifact_id: PLN-PLN-GOAL-001
  file: PLN-PLN-GOAL-001.md
  author: "@juria.koga"
  source_type: human
  timestamp: 2026-02-28 21:54
  content_hash: 1528a657985081d485d928670b3eb750eebd3eb10d87a744a290effdf3d3dd14
```

# 企画書（最終版・社内展開向け）

## QA4AIDD Gate + Coach

**上流工程品質保証の「構造化・可視化・検証可能化」基盤**（AIDD向け）

---

## 0. エグゼクティブサマリー

AI活用開発（AIDD）は開発速度を上げる一方で、上流工程（企画〜要件〜設計）の曖昧さが原因で、**仕様と実装の乖離、手戻り、テスト工数増**が顕在化しやすい。
本企画は、AIDDにおける品質保証（QA4AIDD）を **「自動ゲート」＋「人の判断」** の2層で担保し、**“動けばOK”から“説明できる品質”へ転換する**ための社内基盤を構築する。

本企画のコアは以下の役割分担にある：

| 役割                     | 担当     | 実現手段                                  |
| ------------------------ | -------- | ----------------------------------------- |
| 判断（最終責任）         | 人       | **Coach UI**（Done/Abort + 理由 + 証跡）  |
| 検証（機械的チェック）   | 自動     | **Gate Runner**（Docker/CLIでゲート実行） |
| 記憶・証跡（説明可能性） | システム | JSON出力 → **Allure集約**                 |

この2層により、CIが使えない層にも「視座共有（教育）」を提供しつつ、CIに載せたいチームはそのまま品質ゲートを組み込める。

---

## 1. 背景と課題（Why Now）

### 1.1 現状の構造的問題

現場で観測されている課題は以下に集約される：

- **仕様の曖昧性**：曖昧語（例：「適切に」「柔軟に」）が頻出し、AIが誤解釈しやすい
- **仕様と実装の乖離**：要件定義・設計書・実UIが一致せず、テスト工数増・手戻りが起きやすい
- **QA観点の属人化**：何を確認すべきかが個人経験に依存し、新人が萎えやすい
- **判断根拠の不在**：なぜそう判断したかが残らず、保守で詰む
- **品質の不可視性**：QA実施の有無は分かっても中身が見えない

根本原因は「構造化されていない知識」「検証不能な記述」「トレーサビリティ欠如」。

### 1.2 社内で解くべき3課題（導入視点）

- QA観点の属人化 → Coach UIでチュートリアル化
- 品質観点の後回し → **企画段階から**工程パックで導入
- 責任の不明確化 → Done/Abort + User + Timestamp を必須化

---

## 2. 目的（Goal）

### 2.1 Primary Goal

**仕様書（企画〜要件・設計）の妥当性を検証可能にし、仕様と実装の乖離を防止する。**

### 2.2 Secondary Goals

- 上流工程QA観点を標準化・構造化する
- 判断根拠とプロセスを記録・可視化する
- QA4AIDDの実践手法を確立し、社内に段階導入する（再現可能なテンプレ/プロンプト/チェックリスト資産化）

---

## 3. 対象ユーザー（社内展開）

- AI活用でPoC/小規模開発を回しているメンバー
- QA/PMO/アーキ担当（レビュー観点を型化したい）
- CI/Dockerが扱えるのは一部である前提（導入はCoach先行が基本）

---

## 4. QA4AIDDの定義（本企画での解釈）

社内定義：

- ① AIに正しく指示を与える
- ② 指示が守られていることを確認する

本企画の実装：

- 正しく指示：構造化テンプレ、曖昧語排除チェック
- 遵守確認：JSON Schema検証、Deep Eval評価、構造一貫性テスト
- 品質可視化：Allure Reportでゲート結果をモニタ

---

## 5. 基本思想（設計哲学）

- 「考えなくていいQA」ではなく **「考える順番を固定するQA」**
- AIに判断を委譲しない（判断は人、検証は自動、証跡はシステム）
- 形骸化を防ぐため、品質ゲートを満たさないものは次工程（/デプロイ）に進めない

---

## 6. ソリューション概要（2層構造）

### 6.1 Coach UI（視座共有＋人の最終判断）

「押せば展開されるQAワークフロー」UI。工程タブ → タスク展開 → 観点/テンプレ/例/参照 → Done/Abort。

- 工程タブ：[企画][要件][基本設計][詳細設計][実装][テスト]（段階導入では表示制御）
- タスクはTodo→展開→Done/Abort（理由必須）→次項目Unlock
- 出力は `checklistresults.json`（チェック者・時刻・理由・エビデンス参照）

**Coachの目的**

- 初学者が「何を見ればいいか」を迷わない（観点をチュートリアル化）
- 「最終判断を人が負う」ことを、Done/Abortの操作とログで強制する
- 監査・説明に耐える「判断ログ」を残す

### 6.2 Gate Runner（自動検証：Docker/CLI）

Coachの出力や、企画/要件/設計のYAML等を入力に、品質ゲートを実行し `output/` と `allure-results/` を生成する。

- 配布はDocker/CLI（CIでもローカルでも同じ結果）
- 出力はAllureに集約し、品質の可視化ハブにする（自動ゲート結果＋人の判断ログ＋ダッシュボード添付）

---

## 7. 工程パック戦略（社内導入を現実にする）

本体（フレーム）は共通、工程ごとの「チェックリスト/スキーマ/プロンプト/テンプレ」を **パック**として提供する。

- PLN（企画）パック：企画を機械可読にする／企画段階のQA観点を入れる
- REQ（要件）パック：要件妥当性チェック（human+Deep Eval）、スキーマ、曖昧語、トレース
- BAS/DET：設計工程の拡張
- 実装/運用は将来拡張

---

## 8. 品質保証設計（企画段階から入れる）

### 8.1 企画段階で必須にするQA観点（PLNパック）

企画段階で品質が決まるため、PLNパックには最低限以下を標準装備する：

1. **検証可能性**：成功条件/KPIが測定可能で、テスト可能な言葉か
2. **スコープ**：スコープ内/外、Abort条件が事前に定義されているか
3. **リスク/運用**：運用保守・証跡・権限の考慮があるか（最低限の宣言）

※この“企画→要件へトレース可能”を自動検証できるよう、企画内の主張（Goal/Prob/Scope/Cons等）にPLN-IDを付与し、要件側の `derivedfrom` へ接続する方針を採用する。

### 8.2 品質ゲート（G1〜G5 + PF）

本企画の品質ゲートは「構造の逸脱を最大リスク」として設計する。

#### Gate一覧（工程横断）

| Gate | 内容                                     | 入力                    | 出力                     |
| ---- | ---------------------------------------- | ----------------------- | ------------------------ |
| G1   | 曖昧語チェック                           | .yaml/.md               | ambiguityreport.json     |
| G2   | Checklist完了検証（Coachの判断ログ検証） | checklist.json          | checklistvalidation.json |
| G3   | Schema検証                               | \*.yaml                 | schemareport.json        |
| G4   | Deep Evalスコアリング                    | prompts/, requirements/ | deepevalscores.json      |
| G5   | トレーサビリティ                         | 全ID参照                | tracematrix.json         |
| PF   | Promptfoo評価                            | prompts/                | promptfooresults.json    |

この一覧と入出力は planning_v1 の設計を正式採用。

#### G2（人の判断をCIに接続）

G2は「JSON読込でビルドPass/Fail」が可能で、最短1週間の実装で成立する想定。
（例）必須：Todoが残っていればFail／Abortに理由がなければFail／Abort率が高ければWarning、など。

---

## 9. スコア運用ポリシー（重要：合否の唯一根拠にしない）

### 9.1 ポリシー

- **スコアは合否の唯一根拠にしない**（最終判断は人＝CoachのDone/Abort）
- ただし、品質劣化を早期検知するために **0.70未満はWarningを必ず出す**
  - Allure上でWarningとして表示
  - “理由要約／改善ガイド／再実行条件”をセットで出す（初学者が萎えないため）

この0.70は、要件妥当性チェックリスト雛形にある `pass_threshold: 0.7` を社内標準の警告ラインとして採用する。

### 9.2 Deep Eval / Promptfooの扱い

- Deep Eval：品質の“定量指標”。モデル変動を前提に、スコア推移を記録し劣化を検知する（Allureに推移も集約）。
- Promptfoo：プロンプト品質の回帰テストとして位置づけ、テンプレ改善サイクルの根拠にする。

---

## 10. チェックリスト資産（標準搭載）

### 10.1 要件妥当性チェックリスト（CHK-REQ-REVIEW-001）

本ツールの中核となる「要件レビュー」チェックリスト。

- human_review + deep_eval の両モード
- 重み付け、判定ロジック、deep_eval_promptのひな形まで含む
- 検証可能性／AI可読性／トレーサビリティ／スキーマ準拠／運用考慮（ログ・権限）など、AIDDで落ちがちな観点をまとめて提供

### 10.2 企画MD↔企画YAML整合性（PLNパックに搭載）

企画を“機械可読化”する入口として、企画文書をYAML化し、構造・ID・metaを検証するゲートを置く（詳細はPLNパックのチェックリストに反映）。
（この思想は planning_v1 の工程パック構成例にも含まれる）

---

## 11. トレーサビリティ設計（ConTrack前提でも価値が残る形）

### 11.1 2層設計

- **Core（本ツール）**：ID抽出／参照整合（derivedfrom/tracestoの存在確認）／カバレッジ算出／未紐付け一覧／Allure出力
- **Adapter（将来）**：ConTrack API連携（存在確認、リンク生成、関係解決）

この方針により、ConTrackが既にあっても「品質ゲートとしての検査・可視化・ブロック」という価値が本企画側に残る。

---

## 12. ID規約（本企画に明記して採用）

### 12.1 ルール（共通）

**ID基本形：`{PREFIX}-{PHASE}-{PURPOSE}-{NNN}`**（NNNは3桁）。

- PREFIX：成果物種別（PLN/REQ/BAS/DET/CHK/PRM/RES/ABT/DEC…）
- PHASE：工程（PLN/REQ/BAS/DET/OPS…）
- PURPOSE：用途（GOAL/PROB/SCOPE/CONS/FNC/NFR/DES/EVAL/AMB/YAML…）

### 12.2 推奨パターン（本企画書）

本企画書の主張・方針・スコープなども **PLN-PLN-<PURPOSE>-NNN** としてIDを付与する。
（例：PLN-PLN-GOAL-001 は企画ゴール）

---

## 13. ID発行・管理（同梱ツールとして明記）

### 13.1 ID発行（issue_id.py）

本企画は、ID採番のための最小ユーティリティを同梱する。`issue_id.py` は以下を行う：

- IDレジストリ（id_rules_registry.yaml）を読み、指定キー（PREFIX-PHASE-PURPOSE）の次IDを発行
- レジストリの `next_nnn` 更新
- 発行ログ（id_issued_log.yaml）への追記
- stdoutへ発行ID出力（他ツール連携を想定）

※現状は single-user 前提（ロックなし）で運用開始し、チーム同時利用が増えた段階でロック/集中管理へ拡張する。

---

## 14. Allureによる可視化（品質のハブ）

Allure Reportは以下を一元表示する：

- 自動ゲート結果（G1〜G5, PF）
- スコア推移（Deep Eval/Promptfoo）
- Abort分析（カテゴリ分布、理由品質）
- Traceability Matrix（要件→設計→テストの紐付け）

---

## 15. 具体的なデータ仕様（最低限）

### 15.1 checklistresults.json（Coach出力）

- `checkedby` / `timestamp` / `status(Done|Abort)` / `reason` / `evidencerefs` を保持し、G2が検証する

### 15.2 Gate出力（Runner）

- `output/` に各ゲートのレポートJSON＋サマリ（exitcode含む）
- `allure-results/` を生成してレポートに統合

---

## 16. 配布形態（社内展開：Phase 1はサーバー不要）

- Gate Runner：Docker/CLI（配布しやすい・保守コスト最小）
- Coach UI：ローカルまたは簡易ホスティングで配布（まず“視座共有”を優先）

---

## 17. ロードマップ（社内展開）

Phase 1（1ヶ月）：REQパック配布（Coach先行、Runnerは任意）
Phase 2（2ヶ月）：PLNパック追加（企画段階から品質観点を導入）
Phase 3（3ヶ月〜）：BAS/DET拡張、ConTrack Adapter実装検討

---

## 18. 成功指標（KPI）

- Coach UI利用者数、チェックリスト完了率、理由記入率（100%）、CI組込みチーム数、手戻り削減率など（Phase別に設定）

---

## 19. リスクと対策（最初から明記）

- 形骸化／適当Done：ゲートでブロック、理由品質の最低基準を設ける
- AIモデル変動：モデル固定＋スコア推移監視＋Warning運用
- 導入ハードル：Coach先行で教育→Runner任意→CIへ段階移行

---

# 付録A：本企画のID定義（planning_id.yaml）

ID規約（`{PREFIX}-{PHASE}-{PURPOSE}-{NNN}`）を前提に、この企画書内の主要要素へIDを割り振った **企画ID台帳**です。
（規約は id_rules_registry.yaml を参照し、正規表現も一致させています）

```yaml
meta:
  artifact_id: PLN-PLN-DES-001
  title: "QA4AIDD Gate + Coach（社内展開）企画ID台帳"
  author: "@juria.koga"
  source_type: "human"
  id_convention:
    format: "{PREFIX}-{PHASE}-{PURPOSE}-{NNN}"
    allowed_pattern_regex: "^[A-Z]{2,5}-[A-Z]{2,5}-[A-Z0-9_]+-\\d{3}$"
    registry_file: "id_rules_registry.yaml"
  generated_at: "2026-02-28T00:00:00+09:00"
  references:
    - "planning_v2.2.md"
    - "planning_v1.md"

planning_ids:
  # --- 目的/課題/範囲/制約 ---
  - id: PLN-PLN-GOAL-001
    title: "Primary Goal：仕様書妥当性を検証可能にし、仕様と実装の乖離を防止する"
    maps_to_sections:
      - "2.1 Primary Goal"

  - id: PLN-PLN-PROB-001
    title: "Problem：曖昧性・乖離・属人QA・判断根拠不在・不可視"
    maps_to_sections:
      - "1.1 現状の構造的問題"

  - id: PLN-PLN-SCOPE-001
    title: "Scope：上流工程（企画/要件/基本設計/詳細設計）を対象に、2層（Coach+Runner）で品質保証"
    maps_to_sections:
      - "6 ソリューション概要"
      - "7 工程パック戦略"

  - id: PLN-PLN-CONS-001
    title: "Constraints：Phase1はサーバー不要で開始（Docker/CLI＋ローカル/簡易ホスティング）"
    maps_to_sections:
      - "16 配布形態"

  # --- 設計（2層・データ・ID・Allure） ---
  - id: PLN-PLN-DES-001
    title: "Architecture：判断=人（Coach）/検証=自動（Runner）/証跡=Allure"
    maps_to_sections:
      - "0 エグゼクティブサマリー"
      - "6 ソリューション概要"

  - id: PLN-PLN-FLW-001
    title: "Workflow：Coach→checklistresults.json→Runner→output/allure-results→Allure"
    maps_to_sections:
      - "6.1 Coach UI"
      - "6.2 Gate Runner"
      - "14 Allureによる可視化"

  - id: PLN-PLN-YAML-001
    title: "Planning YAMLization：企画段階の成果物を機械可読化し、構造/ID/metaを検証可能にする"
    maps_to_sections:
      - "8 品質保証設計（企画段階から）"

  - id: PLN-PLN-DES-002
    title: "Quality Gates：G1曖昧語/G2チェックリスト/G3スキーマ/G4 Deep Eval/G5トレース/PF Promptfoo"
    maps_to_sections:
      - "8.2 品質ゲート"

  - id: PLN-PLN-EVAL-001
    title: "Score Policy：スコアは合否の唯一根拠にしない。0.70未満はWarningを必ず出す"
    maps_to_sections:
      - "9 スコア運用ポリシー"

  - id: PLN-PLN-DES-003
    title: "Traceability Design：Core（検査・可視化）＋Adapter（ConTrack連携）"
    maps_to_sections:
      - "11 トレーサビリティ設計"

  - id: PLN-PLN-DES-004
    title: "ID Convention：{PREFIX}-{PHASE}-{PURPOSE}-{NNN} を企画にも適用"
    maps_to_sections:
      - "12 ID規約"

  - id: PLN-PLN-RUN-001
    title: "ID Issuer：issue_id.py を同梱し、registry更新＋発行ログを残す"
    maps_to_sections:
      - "13 ID発行・管理"
```

---
