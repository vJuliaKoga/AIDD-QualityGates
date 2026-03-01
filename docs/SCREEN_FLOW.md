# 画面遷移定義書: QA4AIDD Gate + Coach

> 対象：Coach UI（人の判断・教育）を中心に、Runner（CLI/Docker）との接続点までを含む。
> 参照（正）：`docs/PRD.md` / `artifacts/planning/PLN-PLN-FLW-002.md`

## 0. 用語

- **Coach**：チェックリスト駆動のUI（または代替入力）。工程タブ→項目確認→Done/Abort（理由必須）を記録する。
- **Runner**：品質ゲート実行（Docker/CLI）。Phase 1 の確実な出力は `output/`（JSON）で、Allure統合（`allure-results/`）は段階導入とする。
- **Allure**：自動ゲート結果＋人の判断ログを集約して可視化するレポート。
- **項目（Checklist Item）**：チェック観点1つ（例：曖昧語・スコープ・監査性等）。

---

## 1. 情報設計の前提（UI哲学）

- 目的は「考えなくていいQA」ではなく **「考える順番を固定するQA」**。
- AIに判断を委譲しない。**最終判断は人**（Done/Abort）、自動は検証と警告。
- 形骸化防止のため、**Abortには理由必須**、証跡リンク（evidence refs）は強く推奨。

---

## 2. 主要画面一覧（Screen List）

| Screen ID | 画面名                       | 目的                             | 主な要素                                              |
| --------- | ---------------------------- | -------------------------------- | ----------------------------------------------------- |
| S-001     | Home / Dashboard             | 現在の進捗と次にやることを明確化 | 工程タブ、進捗サマリ、未完了リスト、最近の判断ログ    |
| S-010     | Stage View（工程タブ）       | 工程ごとのチェックを実行         | カテゴリ一覧、項目一覧、フィルタ（未完了/Abort/Done） |
| S-020     | Item Detail（項目詳細）      | 観点を理解し、判断を記録         | 観点説明、例、参照、入力（Done/Abort/理由/証跡）      |
| S-030     | Evidence Picker（証跡参照）  | 理由に紐づく参照を残す           | パス/URL入力、該当箇所メモ                            |
| S-040     | Decision History（判断ログ） | 説明可能性の担保                 | item別履歴、検索、エクスポート                        |
| S-050     | Export / Artifact Output     | ゲート入力となる成果物出力       | checklistresults.json生成、保存先案内                 |
| S-060     | Runner How-to（実行ガイド）  | 初学者がRunnerを回せるようにする | コマンド例、出力の見方、失敗時の対処                  |

※ Phase 1でS-060はドキュメントリンクでもよい（UIに埋め込まない）。

---

## 3. 画面遷移（Navigation Map）

```text
S-001 Home/Dashboard
  |--(工程タブ選択)-----------------> S-010 Stage View
  |--(未完了項目クリック)-----------> S-020 Item Detail
  |--(判断ログを見る)---------------> S-040 Decision History
  |--(成果物出力)-------------------> S-050 Export
  |--(Runnerガイド)-----------------> S-060 Runner How-to

S-010 Stage View
  |--(項目クリック)-----------------> S-020 Item Detail
  |--(戻る)-------------------------> S-001

S-020 Item Detail
  |--(証跡を追加)-------------------> S-030 Evidence Picker
  |--(Done/Abortを確定)-------------> S-010 (同工程の次項目へ)
  |--(戻る)-------------------------> S-010

S-030 Evidence Picker
  |--(追加して戻る)-----------------> S-020

S-050 Export
  |--(checklistresults.json生成)----> S-001 (進捗更新)
```

---

## 4. 主要ユーザーフロー（User Flows）

### 4.1 初回利用（教育目的）

1. ユーザーがS-001へアクセス
2. 工程タブ（例：企画）を選択しS-010へ
3. カテゴリを順に開き、項目の意図（観点/例/参照）を読む
4. 1項目ずつS-020で判断し、Done/Abortを記録（理由必須）
5. 必要に応じてS-030で証跡参照（ファイルパス/URL）を追加
6. S-050で `checklistresults.json` を出力し、Runner実行へ進む

**期待する結果**：

- 「何を見ればよいか」が固定され、レビューの属人性が下がる
- Done/Abort理由が残り、後から説明できる

### 4.2 Gate Runnerに接続するフロー（Coach→Runner）

1. Coachで `checklistresults.json` を生成（S-050）
2. RunnerをDocker/CLIで実行（S-060で案内）
3. `output/`（JSON）が生成される
4. （将来）Allure統合を行う場合は `allure-results/` を生成し、「自動結果＋人の判断ログ」を統合表示する

### 4.3 Abortが出た場合のリカバリフロー

1. S-010でAbort項目をフィルタ表示
2. 該当のS-020を開き、理由と証跡を確認
3. 企画/要件/設計成果物を修正
4. 再度S-020でDone/Abortを更新（履歴を残す）
5. Runnerを再実行し、Allureで改善を確認

---

## 5. 状態遷移（Checklist Item State Machine）

### 5.1 状態

- `TODO`：未判断
- `DONE`：問題なしとして次工程へ進める判断
- `ABORT`：現状では次工程へ進めない判断（理由必須）

### 5.2 遷移

```text
TODO  --(Done + reason?)-->  DONE
TODO  --(Abort + reason必須)--> ABORT
ABORT --(修正後 Done)--> DONE   (履歴としてABORTは残す)
DONE  --(後日再評価 Abort)--> ABORT (例：前提変更/新リスク)
```

※ Done理由は必須としないが、**“判断根拠の不在”を防ぐため任意入力欄を推奨**。

---

## 6. 入出力（UIが扱うデータ）

### 6.1 入力（表示）

- チェックリスト定義（YAML等）：カテゴリ/項目/リスク/証跡ヒント
- 参照リンク（企画書・テンプレ・例）

### 6.2 出力（保存）

- `checklistresults.json`
  - 最低限：`items[].status`（todo|done|abort）/ `items[].reason`（abort時必須）
  - 推奨：`meta.checkedby` / `meta.timestamp` / `items[].item_id` / `items[].evidencerefs`
  - RunnerのG2相当ゲート（checklist_completion）が検証し、CI接続可能とする

---

## 7. 例外/エラーハンドリング方針（UI）

- 理由必須の場面で未入力の場合：保存不可（エラーメッセージ表示）
- 証跡参照が空の場合：警告（ただし保存は可能）
- checklistresults.json生成失敗：
  - 失敗理由（権限/パス/JSON整形など）を明示し再試行導線を出す

---

## 8. Open Questions（要確認）

- 工程タブの初期表示範囲：Phase 1は `[要件]` のみ表示？（企画では段階導入の示唆あり）
- Done理由を必須にするか：形骸化と入力負荷のトレードオフ（Abortは必須、Doneは推奨）
- 証跡参照の形式：ファイルパスのみ／URLのみ／両対応／スニペット保存の可否
- チェックリスト定義の読み込み元：リポジトリ同梱のみか、外部配布も想定するか

---

## 9. 受入（本定義書の完了条件）

- `docs/PRD.md` の「データ契約（checklistresults.json）」と矛盾がない
- 状態遷移（TODO/DONE/ABORT）と「Abort理由必須」が一貫している
- Runner接続フローで、Phase 1 の出力正が `output/` であることが明確である
