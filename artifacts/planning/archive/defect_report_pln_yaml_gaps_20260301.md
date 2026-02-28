# 欠陥レポート：企画書（PLN-PLN-GOAL-001.md）↔ 企画YAML（GOAL/SCOPE/TBL）ギャップ

- 作成日: 2026-03-01
- 対象（入力）:
  - `artifacts/planning/PLN-PLN-GOAL-001.md`（企画書・最終版）
  - `artifacts/planning/PLN-PLN-GOAL-001.yaml`（Goal YAML）
  - `artifacts/planning/PLN-PLN-SCOPE-001.yaml`（Scope YAML）
  - `artifacts/planning/PLN-PLN-TBL-001.yaml`（Inspection Design / TBL YAML）
- 参照（期待）:
  - `packs/checklists/CHK-PLN-CONSIST-001.yaml`（MD↔YAML整合チェック）
  - `packs/pln_pack/schemas/*.schema.json`（goal/scope/inspection_design schema）

## 1. 結論（サマリ）

現状の企画YAMLはスキーマ上は成立しうる一方で、**企画としての確定情報が `TODO` のまま残っている項目が複数あり**、
`CHK-PLN-CONSIST-001` の **PLN-CONS-060（meta以外のTODO禁止）に抵触するため、整合チェックでFailする状態**です。

また、企画書（MD）に含まれる重要な設計要素（Problem/Constraints/Architecture/Workflow/Score Policy/ID運用/ロードマップ/リスク等）が、
現状のYAML（GOAL/SCOPE/TBL）だけでは**構造化されておらず、次工程（REQ）へ「検証可能にトレースする」前提が未充足**です。

## 2. 欠陥一覧（不足・欠陥の列挙）

> 表記:
>
> - **Severity**: `Blocker`（次工程に進めない）/ `Major` / `Minor`
> - **Evidence**: 該当ファイル内の該当文字列（抜粋）

### D-001: YAML内に `TODO` が残存し、整合チェック（PLN-CONS-060）に抵触する

- Severity: **Blocker**
- Affects:
  - `artifacts/planning/PLN-PLN-GOAL-001.yaml`
  - `artifacts/planning/PLN-PLN-SCOPE-001.yaml`
- Evidence（例）:
  - Goal YAML
    - `success_criteria[].target: 'TODO: Phase別に設定'`
    - `scope_out: - 'TODO: 企画（Goal）として明確なスコープ外を定義'`
    - `abort_conditions: - 'TODO: 企画（Goal）として明確なAbort条件を定義'`
  - Scope YAML
    - `abort_conditions: - 'TODO: Abort条件...を企画として確定する'`
    - `traceability.links_out[].note: 'TODO: 要件側のID確定後に接続する'`
    - `terminology.allowed_abbreviations_ref: - 'TODO: 略語一覧の参照元...'`
- Expected:
  - `packs/checklists/CHK-PLN-CONSIST-001.yaml` のルール `PLN-CONS-060`:
    - 「**meta以外に TODO/TBD/PENDING が残っていない**」(severity: fail)
- Impact:
  - Gate/Checklist運用上、企画YAMLが **「確定情報として扱えない」**（次工程の自動検証・トレースが前提崩れ）
- Recommendation:
  1. `TODO` を実値に置き換える（最優先）
  2. もしPhase1では未確定を許容したいなら、`CHK-PLN-CONSIST-001` 側の `PLN-CONS-060` を `warning` 扱いに落とす/例外キーを設計する（ただし例外は**明示フィールド**で管理）

---

### D-002: Goal YAML と Scope YAML の責務境界が曖昧で、二重管理・不整合リスクがある

- Severity: **Major**
- Affects:
  - `artifacts/planning/PLN-PLN-GOAL-001.yaml`（`goal.scope_in/scope_out/abort_conditions` を保持）
  - `artifacts/planning/PLN-PLN-SCOPE-001.yaml`（`scope.scope_in/scope_out/abort_conditions` を保持）
- Evidence:
  - Goal YAML でも scope を保持しているが `scope_out/abort_conditions` が `TODO`
  - Scope YAML では scope_out が具体化されている
- Impact:
  - “どちらが正”かが不明で、将来の更新で差分が発生しやすい（G5のトレース以前に、企画内で矛盾が起きる）
- Recommendation:
  - **単一の正（single source of truth）**を決める
    - 案A: Scope情報は `PLN-PLN-SCOPE-001.yaml` のみ、Goal側からは削除（または参照のみ）
    - 案B: Goal側に最小限（scope_inのみ）＋ Scope側が詳細（scope_out/abort）という階層化をスキーマ/チェックリストで規定

---

### D-003: 企画書（MD）の主要要素に対して、対応する企画YAML成果物が不足している（ID台帳にあるのに実体がない）

- Severity: **Major**
- Affects:
  - `artifacts/planning/PLN-PLN-GOAL-001.md`（付録AのID台帳）
  - `artifacts/planning/*.yaml`（現状: GOAL/SCOPE/TBL のみ）
- Evidence（MD付録Aの planning_ids）:
  - `PLN-PLN-PROB-001`（Problem）
  - `PLN-PLN-CONS-001`（Constraints）
  - `PLN-PLN-DES-001/002/003/004`（Architecture/Gates/Traceability/ID convention）
  - `PLN-PLN-FLW-001`（Workflow）
  - `PLN-PLN-EVAL-001`（Score Policy）
  - `PLN-PLN-RUN-001`（ID Issuer）
  - `PLN-PLN-YAML-001`（YAMLization 方針）

  上記のうち、YAMLとして実体が存在するのは現状 `GOAL-001` と `SCOPE-001` のみ（他は未作成）

- Impact:
  - “企画→要件へトレース可能”方針（MD 8.1/11章）に対し、
    **トレース元となる企画主張がYAML化されていないため、機械的検証（G5）が成立しにくい**
- Recommendation:
  - `PROB/CONS/DES/FLW/EVAL/RUN` 等を、
    - （1）新しいYAMLアーティファクトとして追加する（推奨）
    - （2）既存のGOAL/SCOPE/TBLに統合する（ただしスキーマ拡張＋整合チェック更新が必要）

---

### D-004: 企画書（MD）の重要な記述が、現状のYAMLモデル（GOAL/SCOPE/TBL）では表現されていない

- Severity: **Major**
- Gap（MDで明記されているが、YAMLに構造化されていない例）:
  - 背景/課題（Why Now、根本原因）
  - 対象ユーザー（ペルソナ）
  - QA4AIDDの定義（社内定義①②と、本企画実装の対応）
  - 設計哲学（判断=人/検証=自動/証跡=システム、次工程ブロック方針 等）
  - ゲート一覧（G1〜G5 + PF）と入出力（planning_v1採用明記）
  - Score運用ポリシー（Warning運用、Allure上の扱い、0.70採用理由）
  - トレーサビリティ2層設計（Core/Adapter）
  - ID発行・管理（issue_id.py の仕様）
  - 配布形態、ロードマップ、リスクと対策
- Impact:
  - “説明できる品質”へ転換するという企画の核（証跡・規約・運用）が、
    YAML上では取り出しにくく、機械検証・参照・差分比較に弱い
- Recommendation:
  - 企画YAMLを「目的/範囲」だけで止めず、
    **機械検証に必要な運用ポリシー・ゲート定義・ID運用**までを構造化対象に含める

---

### D-005: トレーサビリティ接続が未確定（REQ側ID未接続）

- Severity: **Major**
- Affects:
  - `artifacts/planning/PLN-PLN-SCOPE-001.yaml`
- Evidence:
  - `traceability.links_out[]` に `to: REQ-REQ-SCOPE-001` があるが `note` が `TODO`
- Impact:
  - G5（トレース）で“企画→要件”のリンクが検査対象になる場合、現状は未成立
- Recommendation:
  - REQ側のスコープ/要求成果物IDを確定して接続する（または Phase1 では `planned_link` として区別するフィールド設計を行う）

---

### D-006: 略語一覧の参照が未確定（allowed_abbreviations_ref が TODO）

- Severity: **Minor**（ただし用語ブレが発生しているならMajor）
- Affects:
  - `artifacts/planning/PLN-PLN-SCOPE-001.yaml`
- Evidence:
  - `terminology.allowed_abbreviations_ref: - 'TODO: 略語一覧の参照元...'`
- Impact:
  - 用語/略語の解釈ブレ（FM-PLN-INT-001）に対する抑止策が未完成
- Recommendation:
  - 参照先を明記（例: MD内セクション番号、または abbreviations YAML を新設）

---

### D-007: TBL（Inspection Design）の機械チェックが、運用依存の未定義パラメータを含み再現性が不足する

- Severity: **Major**
- Affects:
  - `artifacts/planning/PLN-PLN-TBL-001.yaml`
- Evidence（例）:
  - `重大語（運用で定義）`
  - `禁止前提語辞書は運用で拡張`
  - `閾値（運用で定義）`
  - `許容リストを更新して運用`
- Impact:
  - “同じ入力→同じ判定”が難しく、Gate設計としての実装着地が曖昧になる（FM-PLN-REP-001に繋がる）
- Recommendation:
  - 辞書/閾値/許容リストを **設定ファイル（YAML等）として成果物化**し、TBLの `input_artifacts` で明示参照する

---

### D-008: Scope YAMLのdeliverables IDが、企画書付録AのID台帳と整合していない（登録漏れ）

- Severity: **Minor**
- Affects:
  - `artifacts/planning/PLN-PLN-SCOPE-001.yaml`（deliverables: `PLN-PLN-DES-010/011/012`）
  - `artifacts/planning/PLN-PLN-GOAL-001.md`（付録A planning_ids）
- Evidence:
  - MD側 `planning_ids` に `PLN-PLN-DES-010/011/012` が存在しない
- Impact:
  - “企画内IDは台帳で管理する”運用を採用する場合、参照/レビュー時に抜けが出る
- Recommendation:
  - 台帳を「必須一覧」なのか「代表例」なのかを明確化し、
    必須管理なら planning_ids に追記、代表例ならその旨を明記

## 3. 次アクション（提案）

1. **Blocker解消（D-001）**: `TODO` を埋める or 整合チェックの例外設計を決める
2. **責務整理（D-002）**: Goal/Scopeの重複フィールドの扱いを決め、整合ルールを更新
3. **不足アーティファクト追加（D-003/D-004）**: `PROB/CONS/DES/FLW/EVAL/RUN` をYAML成果物として追加（または統合するならスキーマ拡張）
4. **運用パラメータの成果物化（D-007）**: 辞書・閾値・許容リストを設定ファイルとして追加し、TBLから参照
