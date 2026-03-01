# CLAUDE.md（プロジェクト記憶 / 作業規約）

このファイルは、AI/人がこのリポジトリで作業する際の**共通前提**と**守るべき契約**を短く固定する。

参照（正）：

- 企画書：`artifacts/planning/PLN-PLN-FLW-002.md`
- PRD：`docs/PRD.md`
- 画面遷移：`docs/SCREEN_FLOW.md`
- 技術スタック：`docs/TECH_STACK.md`
- FE指針：`docs/FRONTEND_GUIDELINES.md`
- BE構造：`docs/BACKEND_ARCHITECTURE.md`
- 実装計画：`docs/IMPLEMENTATION_PLAN.md`
- AIDD企画段階チェックリスト：`packs/checklists/CHK-PLN-AIDD-001.yaml`

---

## 0. このファイルの役割

- **短く固定する**：詳細は各定義書へ。ここは「破ってはいけない契約」だけを書く。
- **嘘を書かない**：現状の実装・ファイル配置と一致しない内容は書かない。
- **結合点を守る**：特に `checklistresults.json` の契約はプロダクトの一部。

---

## 1. このプロジェクトの目的（Why）

AI活用開発（AIDD）において、上流工程（企画〜要件〜設計）の曖昧さに起因する手戻り・乖離を防ぐため、
**品質保証を「自動ゲート」＋「人の判断」** の2層で担保し、
**“動けばOK”から“説明できる品質”へ転換する**。

---

## 2. 基本思想（守る）

- 「考えなくていいQA」ではなく **「考える順番を固定するQA」**
- AIに判断を委譲しない：
  - **判断（最終責任）= 人（Coach）**
  - **検証 = 自動（Runner / Gates）**
  - **証跡 = システム（JSON/Allure）**
- 形骸化防止：品質ゲートを満たさないものは、次工程へ進めない（少なくともWARN/FAILとして可視化する）

---

## 3. 重要ポリシー（AIDD）

### 3.1 AIのHowを企画/要件から隔離する

企画/要件（上流）では、以下を**書かない/決めない**：

- モデル選定
- プロンプト詳細
- RAG構成
- ベクタDB/埋め込み設計

これらは設計/実装フェーズで扱う（分離することが品質の前提）。

### 3.2 スコア運用ポリシー

- **スコアは合否の唯一根拠にしない**（最終はCoachのDone/Abort）
- ただし **0.70未満はWarning** を必ず出す（劣化検知）

### 3.3 AI コンポーネント品質ポリシー（G4/PF向け）

本ツール自体がAI（G4: DeepEval, PF: Promptfoo）を使うため、以下ポリシーを守る。

**MUST（必須）**
- AIの役割は「定量評価・劣化検知」のみ。合否確定・承認をAIに委ねない
- G4/PFが利用不可（APIキー未設定・タイムアウト）の場合は `SKIP/WARN` にとどめ、`FAIL` に昇格させない（フェイルセーフ）
- 外部LLM APIへの入力前に社内データの外部送信可否を確認する
- G4スコアの証跡（評価軸・参照）をJSONに含める

**SHOULD（推奨）**
- Deep Evalバージョンは `requirements.txt` でpin固定する
- 評価に必要な最小テキストのみ送信する（データ最小化）
- コスト上限を設け、G4/PFは「必須ゲート（G1/G2/G3）」の後に任意実行とする

**MUST NOT（禁止）**
- G4スコアのみで次工程へのPass/Failを確定させない
- 機密情報・個人情報を含む入力をそのまま外部LLM APIへ送信しない

---

## 4. データ契約（最重要）

### 4.1 checklistresults.json（Coach→Runner）

- `items: []` を持つ
- CI Minimal（現状のRunner実装）に対する最低限：`items[].status` と `items[].reason`（abort時必須）
- 推奨：各itemに `item_id`, `status`, `reason`, `evidencerefs` を入れる
- `status=abort` のとき `reason` は必須
- `meta.checkedby` と `meta.timestamp` を保持する

※ Runner側（G2）が読める形で固定する。詳細は `docs/BACKEND_ARCHITECTURE.md` を参照。

### 4.2 ID規約

- `{PREFIX}-{PHASE}-{PURPOSE}-{NNN}`（NNNは3桁）
- 新しい成果物/主張/チェック項目を増やす場合は、ID採番の運用を守る（`id/issue_id.py`）

---

## 5. リポジトリ作業ルール（AIが守る）

- 変更は「目的→差分→影響範囲→検証コマンド」をセットで行う
- 既存ファイル/規約がある場合は、**追加より先に整合**を優先する
- 可能ならスクリプトは非対話で実行できる形にする（CI/ローカルの再現性）

---

## 6. よくある作業コマンド（例）

### pack実行（CI Minimal）

```bash
python runner/aidd-gate.py --pack packs/pln_pack/pln.pack.yaml --outdir output
```

### pytest + Allure results

```bash
pytest -q --alluredir=allure-results
```

> **【実装完了後に追記】以下のコマンドは対応スクリプトが未実装のため、本実装完了後に動作確認・追記すること。**
>
> - `id/issue_id.py`（ID採番）: 企画書 §13 参照。未実装のため `id/` ディレクトリおよびスクリプトの整備が先決。
> - `runner/gates/g1_ambiguity.py` / `g2_checklist_completion.py` / `g5_trace.py`: 現状は空ファイル。実体は `runner/aidd-gate.py` 内の `gate_ambiguity()` / `gate_checklist()` が担う（`docs/BACKEND_ARCHITECTURE.md` 参照）。
> - G4（`runner/gates/g4_deepeval.py`）および PF は環境依存が大きいため、Phase 4 統合時に別途手順を確定する。

---

## 7. 作業開始時チェック（人/AI共通）

- `docs/PRD.md` を読み、今やる変更が **Goal/Non-goal** に反していないか確認
- 変更が `checklistresults.json` に影響するなら、
  - `docs/PRD.md` のデータ契約
  - `docs/BACKEND_ARCHITECTURE.md` の G2契約
    を同時に更新し、矛盾を残さない
