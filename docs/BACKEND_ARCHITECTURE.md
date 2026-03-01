# バックエンド構造定義書: Gate Runner（QA4AIDD Quality Gates）

> 本書は、QA4AIDDの「自動検証」側（Gate Runner）を、コード構造・入出力・拡張点の観点で定義する。
> 参照：`docs/PRD.md` / `docs/TECH_STACK.md` / `artifacts/planning/PLN-PLN-FLW-002.md`

---

## 1. ゴール / 非ゴール

### 1.1 ゴール

- **Docker/CLIで再現可能**な品質ゲート実行を提供する
- 企画/要件/設計などの成果物（YAML/MD/JSON）を入力として、
  **PASS/WARN/FAIL** を一貫した形式で出力する
- 出力を **機械可読（JSON）** にし、Allureなどの可視化へ接続する

### 1.2 非ゴール

- 常時稼働のサーバー（APIサーバ）を作ること（Phase 1はサーバ不要）
- AIのHow（モデル選定・プロンプト詳細・RAG構成）を企画/要件レイヤに持ち込むこと
- 外部トレーサビリティ基盤（ConTrack等）への強依存（将来はAdapterで対応）

---

## 2. コンポーネント構成（Repository view）

### 2.1 Runner（エントリポイント）

- `runner/aidd-gate.py`
  - Pack YAML（例：`packs/pln_pack/pln.pack.yaml`）を読み、`steps` を順に実行
  - 実行結果を `output/pln_gate_report.json` として出力
  - exit code：
    - FAILがあれば 2（CIブロック）
    - WARNのみは 0（CIは継続、レポートで警告）

> 重要（事実関係）：`runner/aidd-gate.py` は内部的に WARN を exit_code=1 としてレポートへ記録するが、
> **プロセスの終了コードとしては FAIL（2）以外は 0 を返す**（コメントの方針どおり）。
> したがってCIブロック条件は「FAILのみ」であり、WARNは可視化・改善促進のための扱いである。

### 2.2 ゲート実装（個別スクリプト）

現状リポジトリには、個別ゲートスクリプトが存在する（例：G3/G4）。

- `runner/gates/g1_ambiguity.py`：曖昧語チェック（※現状ファイルが空のため、実体は `runner/aidd-gate.py` の `gate_ambiguity()` が担う）
- `runner/gates/g2_checklist_completion.py`：チェックリスト完了検証（※現状ファイルが空のため、実体は `runner/aidd-gate.py` の `gate_checklist()` が担う）
- `runner/gates/g3_schema.py`：スキーマ検証（分割YAMLディレクトリ/単体ファイル）
- `runner/gates/g4_deepeval.py`：DeepEval（MD/YAML参照切替）
- `runner/gates/g5_trace.py`：トレーサビリティ（※現状ファイルが空のため、未実装/要整備）

> 方針：
>
> - Phase 1は `runner/aidd-gate.py`（pack駆動）で「最低限のCI接続」を成立させる
> - 並行して `runner/gates/*` の高機能ゲートを、pack駆動へ統合していく

### 2.3 Packs（工程パック）

- `packs/`：工程ごとの資産（チェックリスト/スキーマ/ルール/プロンプト）
- `packs/pln_pack/pln.pack.yaml`：Planning pack（CI Minimal）

`pln.pack.yaml` は以下を持つ：

- `paths`：辞書やチェックリスト成果物パス
- `artifacts`：対象成果物パス
- `schemas`：スキーマパス
- `steps`：実行するゲート（schema/ambiguity/checklist_completion…）

---

## 3. ディレクトリ設計（入力/出力）

### 3.1 入力（Inputs）

- `artifacts/`
  - 企画/要件/設計の成果物（MD/YAML等）
  - Coach（または代替手段）の出力：`artifacts/checklists/checklistresults.*.json`（pack参照）
- `packs/`
  - checklists（YAML）
  - schemas（JSON Schema）
  - rules（曖昧語辞書）
  - prompts（DeepEval/Promptfoo用）

### 3.2 出力（Outputs）

- `output/`
  - pack実行レポート（例：`output/pln_gate_report.json`）
  - 個別ゲートのレポート（例：`output/G3/...`, `output/target/...`）
- `allure-results/`
  - pytest/allure-pytest により生成されるAllure用成果物

---

## 4. Pack駆動の実行モデル（Minimal Runner）

### 4.1 Step種別（現状：runner/aidd-gate.py）

| kind                   | 意味                 | 入力                      | 出力/判定                                 |
| ---------------------- | -------------------- | ------------------------- | ----------------------------------------- |
| `schema`               | JSON Schema検証      | target YAML + schema JSON | errorsがあればFAIL                        |
| `ambiguity`            | 曖昧語検出           | targets + dictionary      | hitでWARN/FAIL（設定）                    |
| `checklist_completion` | 判断ログの検証（G2） | checklistresults.json     | TODO残/Abort理由なしでFAIL、Abort率でWARN |

> 注：この表は「packで扱える step kind」としての契約であり、
> `runner/gates/*` スクリプト群の実装状況とは独立。

### 4.2 Packの拡張方針

- 新しいゲート種別を追加する場合：
  - `runner/aidd-gate.py` に `kind` を追加
  - `packs/<phase>_pack/*.pack.yaml` に step を追加
  - 出力JSONのフォーマットは `StepResult`（step_id/status/details）で統一

---

## 5. G2（人の判断ログ）のデータ契約（最重要）

### 5.1 現状の期待（runner/aidd-gate.py）

- `checklistresults.json` の形：
  - ルートに `items: []`
  - 各 `items[]` に `status`（todo|abort|done）と `reason` が入る

### 5.2 推奨（契約として固定すべき）

Coach UIとRunnerの結合点は **checklistresults.json** なので、ここを先に固める。

推奨スキーマ（例）：

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
      "status": "done", // todo|done|abort
      "reason": "...", // abort時は必須
      "evidencerefs": ["path/to/doc#L10"],
    },
  ],
}
```

> 次の改善候補：
>
> - G2側が `item_id` の存在を要求する（監査性）
> - `checkedby/timestamp` を meta に集約し、各itemにも上書き可能にする

---

## 5.5 G4（DeepEval）/ PF（Promptfoo）のフェイルセーフ

G4とPFは「オプションゲート」として扱う。以下の動作を実装すること（MUST）。

| 状況 | 動作 | exit code |
|---|---|---|
| APIキー未設定 | `SKIP`（警告メッセージのみ） | 0 |
| タイムアウト | `WARN`（JSONに記録） | 0 |
| 外部API接続不可 | `WARN`（JSONに記録） | 0 |
| スコア < 0.70 | `WARN`（改善ガイドをセット） | 0 |
| スコア >= 0.70 | `PASS` | 0 |

> **MUST NOT**：G4/PFの失敗・未設定を理由に exit code 2（CIブロック）を返さない。

### G4データ入力の注意（MUST）

- 入力成果物に機密/個人情報が含まれる場合は、外部LLM APIへの送信前に社内データ送信可否を確認する
- 評価に必要な最小テキストのみ送信する（全文送信を避ける）

> **【実装完了後に追記】** G4/PFのプロンプト設計・入力サニタイズ・タイムアウト値は Phase 4 実装時に確定し、本定義書を更新する。

---

## 6. Allure統合（証跡ハブ）

### 6.1 現状

- `runner/Dockerfile` は pytest を実行し `allure-results/` を生成する想定
- ただし pack駆動Runner（aidd-gate.py）は pytest とは独立のため、
  Allureへの統合は「pytestで包む」または「Allure resultsを書き出す」設計が別途必要

> 事実：ローカル環境で `pytest` を実行する場合、Pythonの `allure` モジュール（`allure-pytest` が提供）が
> インストールされていないと `ModuleNotFoundError: No module named 'allure'` が発生し得る。
> 依存関係は `requirements.txt` に記載されているため、利用者は `pip install -r requirements.txt` を事前に実行する。

### 6.2 方針（Phase 1）

- まずは `output/*.json` を正として整備し、Allure統合は後追いで段階導入
- もしくは pack実行を pytest テストとしてラップし、Allureへ載せる

---

## 7. セキュリティ / 運用

- 入力成果物に機密が含まれる可能性があるため、
  出力（output/allure-results）に機密が残る運用を前提に取り扱いを規定する
- 依存パッケージはpin/固定（DeepEval等を導入する場合は特に重要）

---

## 8. Open Questions

- `runner/gates/g1_ambiguity.py` / `g2_checklist_completion.py` / `g5_trace.py` の実装差分を、
  `runner/aidd-gate.py` とどう統合するか
- `packs/pln_pack` が現状「workflows/checklists/docs/prompts/rules」を含まない（pack.yamlの設計例との差）
  - packsの最終形（配布資産）をどこまで揃えるか

---

## 9. 受入（本定義書の完了条件）

- `docs/PRD.md` の「FR/データ契約/ポリシー」と矛盾しない
- CI Minimal の実体が `runner/aidd-gate.py` であること、および `runner/gates/g1/g2/g5` が現状空であることを明記し、嘘がない
- Phase 1 の出力正が `output/`（JSON）であることが明確である
