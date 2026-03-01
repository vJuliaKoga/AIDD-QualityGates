# フロントエンド指針: Coach UI（QA4AIDD Gate + Coach）

> 本書は、Coach UIを実装する際に「仕様が揺れない」ための実装指針（ガイドライン）を定義する。
> 参照：`docs/PRD.md` / `docs/SCREEN_FLOW.md` / `docs/TECH_STACK.md`

---

## 1. 目的 / 非目的

### 1.1 目的

- チェックリスト駆動UIを、**迷わず実装できる粒度**に落とす
- 「人が最終判断する（Done/Abort）」をUI・データで強制する
- `checklistresults.json` を安定して生成し、Runner（G2）へ接続できる状態にする

### 1.2 非目的

- モデル選定・プロンプト詳細・RAG構成など **AIのHow** はフロントで決めない（設計/実装へ隔離）
- いきなり社内認証・RBAC・サーバー常駐を必須にしない（Phase 1はサーバ不要が前提）

---

## 1.3 前提（このリポジトリにおける「事実」）

- Coach UIは現状このリポジトリに実装がなく、本書は **実装指針（将来の契約）** を定義する。
- Phase 1 のCI Minimalは `runner/aidd-gate.py`（pack駆動）であり、Coachは **JSON出力（契約）** を満たせばUIである必要はない。

---

## 2. UX原則（Coachらしさ）

1. **次に何をするかが常に1つに絞れる**（Next Actionが見える）
2. **判断（Done/Abort）の責任をUI操作で強制**（理由必須・履歴保存）
3. **学習（チュートリアル）として機能**（観点/例/参照/証跡ヒントを同画面で提示）
4. **証跡ファースト**（後追い説明のために、リンク/パス/メモを残しやすくする）
5. **オフライン/ローカル優先**（最初はファイル入出力で成立させる）

---

## 2.1 画面遷移の正（SSOT）

画面と遷移は `docs/SCREEN_FLOW.md` を正とする。

- 画面ID・役割・状態遷移（TODO/DONE/ABORT）を本書で二重定義しない
- 本書は「実装上の迷いをなくすための追加ルール（データ契約・実装境界・テスト）」に集中する

---

## 3. 画面構成（最低限）

`docs/SCREEN_FLOW.md` を実装の正とする。

### 必須（MVP）

- S-001 Home/Dashboard
- S-010 Stage View（工程タブ）
- S-020 Item Detail（項目詳細：Done/Abort/理由/証跡）
- S-050 Export（checklistresults.json生成）

### 任意（Phase 1の後半〜）

- S-040 Decision History（判断ログ）
- S-060 Runner How-to（実行ガイド）

---

## 4. データ設計（フロントが持つべき境界）

### 4.1 入力（読み込み）

- **チェックリスト定義（YAML）**
  - 例：`packs/checklists/CHK-PLN-AIDD-001.yaml`
  - UIは以下を表示できること：
    - category（カテゴリ）
    - item_id / title / risk
    - evidence_hint（あれば）

> 実装の選択肢
>
> - 方式A：ビルド時にチェックリストを同梱（静的UI）
> - 方式B：ユーザーがファイルをアップロードして読み込む（柔軟だが実装増）

### 4.2 出力（保存）

- `checklistresults.json`
  - **最低限（CI Minimalで必須）**
    - `items: []`
    - `items[].status`（`todo|done|abort`）
    - `items[].reason`（abort時は必須）
  - **推奨（監査性・説明可能性）**
    - `meta.checkedby`
    - `meta.timestamp`
    - `items[].item_id`
    - `items[].evidencerefs`（パス/URL/該当箇所）
  - 形式の正は `docs/PRD.md`（データ契約）と `docs/BACKEND_ARCHITECTURE.md`（G2契約）を参照する

### 4.3 正規化方針

- チェックリスト定義（YAML）と、判断ログ（JSON）は **別物** として扱う
  - YAMLは「観点の定義」
  - JSONは「判断の事実（証跡）」

---

## 5. 状態管理（State）

### 5.1 最小状態モデル

- `selectedStage`：現在の工程（PLN/REQ/...）
- `selectedItemId`：現在の項目
- `decisions`：項目ごとの判断ログ（最新 + 履歴）
- `dirty`：未保存の変更があるか

### 5.2 状態遷移（重要）

- TODO/DONE/ABORT の状態遷移は `docs/SCREEN_FLOW.md` を踏襲
- ABORTは理由必須（UIで保存不可）
- DONE→ABORT（再評価）も許容し、履歴として残す

---

## 6. バリデーション（入力制約）

### 6.1 必須ルール

- `status = ABORT` のとき `reason` は必須
- `checkedby` は必須（ローカルならユーザー名入力でよい）
- `timestamp` は自動入力（ISO 8601推奨）

### 6.2 推奨ルール

- `evidencerefs` は空でも許容するが、警告を出す（証跡不足の防止）
- DONEでも任意で理由を残せる（将来の説明可能性のため）

---

## 7. コンポーネント設計（例）

### 7.1 コンポーネント分割

- `StageTabs`：工程タブ
- `CategoryList`：カテゴリ一覧
- `ChecklistItemList`：項目一覧（フィルタ/検索）
- `ItemDetail`：項目詳細（観点/例/参照/入力フォーム）
- `EvidenceEditor`：証跡入力（URL/パス/メモ）
- `ExportPanel`：JSON出力（ダウンロード/保存先案内）

### 7.2 データアクセス境界

- YAMLの読み込み・パースは `ChecklistRepository` に集約（UIから隠蔽）
- JSONエクスポートは `ChecklistResultsExporter` に集約

---

## 8. アクセシビリティ / ローカリゼーション

- キーボード操作（Tab移動、Enter確定）を壊さない
- 用語は日本語を正とし、将来の英語化は辞書で差し替え可能にする

---

## 9. セキュリティ（フロント観点）

- 機密情報をUIへ貼り付けさせない（注意文、テンプレで誘導）
- 出力JSONに個人情報/機密が混入し得るため、保存先と取り扱い注意を明示する
- 外部送信が発生する設計（サーバ連携等）はPhase 1ではデフォルトOFF

---

## 10. テスト方針（フロント）

- ユニット：
  - ABORT理由必須のバリデーション
  - JSON出力スキーマ（最低限キーが入る）
- E2E（任意）：
  - 1項目をTODO→ABORT→DONEへ遷移させ、履歴が残る

---

## 11. Doneの定義（実装完了条件）

- チェックリスト（YAML）を読み込み、カテゴリ/項目が表示できる
- 各項目に対してDone/Abortが入力できる
- Abort理由必須がUIで強制される
- `checklistresults.json` を出力でき、Runner（G2）が読める形式になっている

---

## 12. Open Questions

- checklistresults.jsonの正確なスキーマ（items配列の形、id項目名の統一）をどこで確定するか
  - 現状 `runner/aidd-gate.py` は `items[].status/reason` を参照している
  - UI側の出力仕様は、G2の入力期待に合わせて早期に固定する必要がある

---

## 13. 受入（本指針の完了条件）

- `docs/PRD.md` のデータ契約と矛盾がない
- ABORT理由必須が「UI上で保存不可」として実装できる粒度で書かれている
- 仕様（Why/What）と実装（How）を混線させない（How隔離ポリシーを侵さない）
