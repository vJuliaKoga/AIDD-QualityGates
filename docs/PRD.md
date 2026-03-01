# PRD: QA4AIDD Gate + Coach

> 本PRDは、企画書 `artifacts/planning/PLN-PLN-FLW-002.md` を「プロダクト要件」として固定し、
> このリポジトリ（AIDD-QualityGates）が提供する価値・スコープ・受入条件・データ契約を明文化する。

---

## 1. 背景 / Problem Statement

AI活用開発（AIDD）は開発速度を上げる一方で、上流工程（企画〜要件〜設計）の曖昧さが原因で、以下が発生しやすい。

- **仕様の曖昧性**（例:「適切に」「柔軟に」）によりAI/人が誤解釈しやすい
- **仕様と実装の乖離**により手戻りとテスト工数が増加する
- **QA観点の属人化**によりレビュー品質が揺れる
- **判断根拠の不在**により保守・監査・説明で詰む
- **品質の不可視性**により「QAしたかどうか」しか見えない

根本原因は、**構造化されていない知識**／**検証不能な記述**／**トレーサビリティ欠如**。

---

## 2. プロダクト概要 / One-liner

**上流工程品質保証の「構造化・可視化・検証可能化」基盤（AIDD向け）**。

最終判断を人（Coach）が持ち、機械的検証を自動（Gate Runner）が担い、証跡をシステム（JSON/Allure）に残す。

---

## 3. ゴール（Primary / Secondary）

### 3.1 Primary Goal

**仕様書（企画〜要件・設計）の妥当性を検証可能にし、仕様と実装の乖離を防止する。**

### 3.2 Secondary Goals

- 上流工程QA観点を標準化・構造化する
- 判断根拠とプロセスを記録・可視化する
- QA4AIDDの実践手法を社内で段階導入できる形にする（テンプレ/プロンプト/チェックリスト資産化）

---

## 4. 非ゴール（Out of Scope）

以下は Phase 1 の範囲外（将来拡張候補）とする。

- **AIのHow**（モデル選定、プロンプト詳細、RAG構成等）を上流（企画/要件）に書くこと
- ConTrack等の外部トレーサビリティ基盤への強依存（将来は Adapter で連携）
- 常時稼働サーバー必須の提供形態（Phase 1はサーバ不要を前提）

---

## 5. 対象ユーザー / Persona

- **AIDD開発者**：PoC/小規模開発を高速に回しているが、上流の品質保証が弱い
- **QA/PMO/アーキ担当**：レビュー観点を標準化・教育したい
- **CI/Dockerが扱えるメンバー**：ゲートをCIへ載せたい（ただし社内では一部に限定される想定）

---

## 6. 価値提供（Value Proposition）

- **考える順番を固定する**ことで、QAを「運」や「経験」から切り離す
- **Done/Abort + 理由 + 証跡**を必須にすることで、説明可能性を担保する
- 構造・スキーマ・曖昧語・評価（DeepEval等）・トレースをゲート化し、
  次工程に進めない/警告する基準を明確化する

---

## 7. 用語（SSOT）

用語の正は本PRDと `docs/CLAUDE.md` とする。

- **Coach**：人がチェック項目を読み、判断（Done/Abort）と理由/証跡を記録する仕組み（UIまたは代替手段）
- **Gate Runner**：成果物を入力に品質ゲートを実行し、機械可読な結果を出力するCLI/Docker実行物
- **Gate**：機械的に検証できるルール群（曖昧語、スキーマ、チェックリスト完了、DeepEval、トレース等）
- **Pack**：工程ごとの資産セット（チェックリスト、スキーマ、ルール、プロンプト、実行手順）
- **Artifact**：企画/要件/設計などの成果物（MD/YAML/JSON）

---

## 8. ソリューション（2層アーキテクチャ）

### 8.1 Coach（人の最終判断 + 教育/視座共有）

目的：初学者でも「何を見ればよいか」が迷わないよう、工程タブからチェック観点を展開し、**Done/Abort** を記録する。

- 工程タブ例：`[企画][要件][基本設計][詳細設計][実装][テスト]`
- タスク：Todo → 展開（観点/テンプレ/例/参照）→ Done/Abort（理由必須）→ 次項目Unlock
- 出力：`checklistresults.json`（判断ログ）

※ Phase 1 では Coach UI を必須にせず、JSONテンプレ入力やスプレッドシート→JSON変換などで代替してもよい。

### 8.2 Gate Runner（自動検証：Docker/CLI）

Coach出力や、企画/要件/設計のYAML等を入力に品質ゲートを実行し、`output/` と（将来） `allure-results/` を生成する。

---

## 9. 機能要件（Functional Requirements）

### 9.1 Gate Runner（必須）

#### FR-GATE-001：パック駆動のゲート実行

- Pack YAMLを読み、定義された `steps` を順番に実行できる
- 各stepは `PASS/WARN/FAIL` のステータスを返し、詳細をJSONで出力できる

#### FR-GATE-002：最小ゲート種別（CI Minimal）

Phase 1 の最小構成として、少なくとも以下を提供する。

- **スキーマ検証（G3相当）**：JSON Schema Draft 2020-12 による検証
- **曖昧語検出（G1相当）**：辞書ベースで該当語を検出
- **チェックリスト完了検証（G2相当）**：TODO残、Abort理由未記載をFailにできる

#### FR-GATE-003：出力（機械可読）

- `output/<phase>_gate_report.json` など、**後工程が集計・差分比較しやすいJSON**を生成する
- 失敗時は「何が」「どこで」「なぜ」失敗したか（対象ファイル、キー、理由）が追える

### 9.2 Coach（要件としては必須だが、実装は段階導入）

#### FR-COACH-001：チェックリスト駆動UI（または代替入力）

- 工程→カテゴリ→項目（観点/例/参照）を提示できる
- 入力：Done/Abort + 理由（必須） + 証跡参照（推奨）
- 出力：`checklistresults.json`

---

## 10. データ契約（最重要）

### 10.1 Coach → Runner（checklistresults.json）

CoachとRunnerの結合点は `checklistresults.json`。

**CI Minimal（現状のRunner実装が最低限要求する項目）**

- ルートに `items: []` がある
- 各 `items[]` に `status` があり、`todo|done|abort` のいずれか
- `status=abort` のとき `reason` が空でない

**推奨（監査性・説明可能性のために固定したい項目）**

```jsonc
{
  "meta": {
    "stage": "PLN",
    "checkedby": "...",
    "timestamp": "2026-03-01T16:00:00+09:00",
  },
  "items": [
    {
      "item_id": "CHK-PLN-AIDD-090",
      "status": "done",
      "reason": "...",
      "evidencerefs": ["artifacts/planning/PLN-PLN-FLW-002.md#8.1"],
    },
  ],
}
```

### 10.2 出力レポート（pack実行結果）

少なくとも以下を満たす。

- `pack`: 実行したpackへの参照
- `results[]`: `step_id`, `status`, `details` を持つ

---

## 11. 非機能要件（Non-Functional Requirements）

### 11.1 監査性 / 証跡（必須）

- Done/Abort判断ログの保存（checkedby, timestamp, reason, evidencerefs）
- Gate実行結果の保存（JSON、将来はAllure集約）

### 11.2 再現性（必須）

- Docker/CLIで同一入力に対して同一の判定・レポート形式が得られる

### 11.3 セキュリティ / データ取扱い（必須）

- 企画段階で「機密/個人情報/社外秘」等の分類と取り扱い方針を宣言可能であること
- 不要なデータ保持・外部送信を避ける（データ最小化）

---

## 12. スコア運用ポリシー

- **スコアは合否の唯一根拠にしない**（最終判断は人＝CoachのDone/Abort）
- ただし品質劣化検知として **0.70未満は必ずWarning** を出す

---

## 13. 成功指標（KPI）

- Coach UI利用者数
- チェックリスト完了率
- 理由記入率（100%）
- CI組込みチーム数
- 手戻り削減率（導入前後比較）

---

## 14. AI コンポーネント品質要件（G4 DeepEval / PF Promptfoo）

本ツール自体が AI（G4: DeepEval, PF: Promptfoo）を使うため、`packs/checklists/CHK-PLN-AIDD-001.yaml` の観点を自己適用する。

### 14.1 AI利用前提（CHK-PLN-AIDD CAT-010）

| 観点 | 定義 |
|---|---|
| **使う必然性** | 仕様品質（一貫性・完全性・曖昧性）の定量評価を人手で全件実施するコストを削減するため |
| **AIの役割** | スコアリング（評価指標の算出）のみ。合否の最終判断はしない |
| **人の役割（HITL）** | CoachがDone/Abortを最終確定。0.70未満Warningは「AI→人への確認トリガ」 |
| **AIがやらないこと** | 合否の確定・承認・人の判断の代替 |

### 14.2 入力データ（CHK-PLN-AIDD CAT-020）

- **入力ソース**：`artifacts/` 配下のYAML/MD（企画・要件・設計成果物）
- **データ分類**：成果物に機密/個人情報が含まれ得る。外部LLM API利用時は社内データ送信可否を事前に確認する（MUST）
- **データ最小化**：評価に必要な最小テキストのみ送信する設計を推奨。全文送信は避ける（SHOULD）

### 14.3 出力要件（CHK-PLN-AIDD CAT-030）

- **出力型**：JSON（`gate_id` / `axis_scores` / `score_total` / `pass|warn|fail` / `evidence`）
- **根拠提示**：スコアの根拠（評価軸・証跡参照）をJSONに含める（MUST）
- **不確実性**：0.70未満は Warningとして出力し、スコアを唯一根拠にしない
- **禁止出力**：根拠なき合否確定出力 / 機密情報の再掲 / 推測断定（MUST NOT）

### 14.4 評価可能性（CHK-PLN-AIDD CAT-040）

- **評価指標**：DeepEval スコア（軸別）、人の判断との乖離率（ドリフト検知）
- **評価データ（ゴールド）**：Phase 4 以降で整備（担当者・更新頻度を実装計画に明記）
- **受入基準**：0.70以上を基本ライン（Warning 閾値）
- **重大度分類**：FAIL = スキーマ逸脱・必須項目欠落 / WARN = 品質スコア低下 / INFO = 軽微な観点

### 14.5 失敗モード（CHK-PLN-AIDD CAT-050）

- **幻覚対策**：G4スコアを合否の唯一根拠にしない（§12 スコア運用ポリシーとして明文化済）
- **誤りの影響**：G4スコアが誤っても最終判断はCoach（HITL）なので致命的影響なし
- **プロンプト注入対策**：入力成果物のサニタイズ方針は G4 実装時（Phase 4）に定義する（【実装完了後に追記】）

### 14.6 コスト・性能・フェイルセーフ（CHK-PLN-AIDD CAT-080）

- **コスト上限**：G4/PFは「オプションゲート」とし、必須ゲート（G1/G2/G3）の後に任意実行
- **フェイルセーフ**：G4/PFが利用不可（APIキー未設定・タイムアウト等）の場合は `SKIP/WARN` にとどめ、`FAIL` に昇格させない（MUST）
- **レイテンシ**：G4のタイムアウト値は Phase 4 実装時に決定（【実装完了後に追記】）

### 14.7 ガバナンス・運用（CHK-PLN-AIDD CAT-060/070）

- **責任者**：G4スコアの採否判断はCoach担当者が負う
- **監査性**：G4スコアとその証跡（根拠参照）をJSONに保存し、Allureで追跡可能にする
- **モデル更新方針**：DeepEval のバージョンは `requirements.txt` でpin固定。更新時はスコア推移を比較して採否を判断する（SHOULD）

---

## 15. Open Questions（要確認）

- Coach UIの配布形態：完全ローカル（静的）か、簡易ホスティングか
- 「ブロック（Fail）」条件の初期セット：何をFailにし、何をWarningに留めるか（企画書 §20.5 参照）
- Deep Eval / Promptfoo の入力データ整備（ゴールド作成計画・責任者）

---

## 16. 参照（正）

- 企画書：`artifacts/planning/PLN-PLN-FLW-002.md`
- AIDD企画段階チェックリスト：`packs/checklists/CHK-PLN-AIDD-001.yaml`
- 画面遷移：`docs/SCREEN_FLOW.md`
- 技術スタック：`docs/TECH_STACK.md`
- FE指針：`docs/FRONTEND_GUIDELINES.md`
- BE構造：`docs/BACKEND_ARCHITECTURE.md`
- 実装計画：`docs/IMPLEMENTATION_PLAN.md`

---

## 17. 現状の実装ステータス（As-Is / 2026-03-01時点）

本PRDは要件定義だが、**「現状できること/できないこと」を明記**し、ドキュメントに嘘が混入しないようにする。

### 16.1 Runner（CI Minimal）の実体

- pack駆動の最小Runnerは `runner/aidd-gate.py`。
- G1/G2相当は `runner/aidd-gate.py` 内部（`gate_ambiguity()` / `gate_checklist()`）で成立している。
- `runner/gates/g1_ambiguity.py` / `runner/gates/g2_checklist_completion.py` は現状 **空ファイル**。

### 16.2 Pack（PLN pack）の現状

- `packs/pln_pack/pln.pack.yaml` は存在するが、
  `packs/pln_pack/schemas/goal.schema.json` 等を参照しており、現状のリポジトリ構成では **参照先が不足しているため、そのままでは実行失敗する**。
  - 失敗例：`FileNotFoundError: ... packs/pln_pack/schemas/goal.schema.json`

> 本PRDは「何を実現したいか」を正として維持しつつ、
> 実装ステータスの事実は `docs/progress.txt` と合わせて更新する。
