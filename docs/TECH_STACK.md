# 技術スタック定義書: QA4AIDD Gate + Coach

> 対象：QA4AIDDの2層（Gate Runner / Coach UI）を成立させるための技術選定と、その理由・制約。
> 参照（正）：`docs/PRD.md` / `artifacts/planning/PLN-PLN-FLW-002.md`

---

## 1. 技術選定の原則（Why these choices）

1. **再現可能性（Reproducible）**：同一入力 → 同一結果（少なくとも判定・レポート形式が同一）
2. **配布容易性（Portable）**：社内でCIが使えない層でもローカルで回せる
3. **機械可読（Machine-readable）**：成果物はJSON/YAMLで構造化し、後工程のゲート・集計に接続できる
4. **説明可能性（Auditable）**：人の判断ログ（理由・証跡）と自動判定（根拠）を保存する
5. **段階導入（Progressive）**：Coach→Runner→CIの順で導入できる（最初からCI前提にしない）

---

## 2. 全体アーキテクチャ（技術視点）

| レイヤ      | コンポーネント  | 技術                                    | 役割                                               |
| ----------- | --------------- | --------------------------------------- | -------------------------------------------------- |
| 人の判断    | Coach UI        | （提案）Web UI（React/TypeScript など） | チェックリスト提示、Done/Abort + 理由 + 証跡の記録 |
| 自動検証    | Gate Runner     | **Python 3.11**（CLI） + **Docker**     | ゲート実行（G1〜G5/PF等）、JSON出力                |
| 証跡ハブ    | Report          | **Allure**（allure-results）            | 自動結果＋判断ログの統合可視化                     |
| データ/規約 | Artifacts/Packs | **YAML/JSON** + **JSON Schema**         | 企画/要件/設計の機械可読化・検証                   |

※ Coach UIはPhase 1で「UIそのもの」を必須にしない場合、ドキュメント+JSONテンプレ入力から開始しても良い。

---

## 3. Gate Runner（CLI/Docker）

### 3.1 言語 / ランタイム

- **Python 3.11**
  - 理由：JSON/YAML処理、検証（jsonschema）、テスト（pytest）と相性が良い
  - Dockerイメージ（`python:3.11-slim`）で配布しやすい

### 3.2 主要ライブラリ（現状のリポジトリに準拠）

- `pyyaml`：YAML読み書き
- `jsonschema`：JSON Schema（Draft 2020-12）検証
- `pytest`：ゲート実行/検証のベース
- `allure-pytest`：Allure results 出力

> 注：DeepEval（`deepeval`）やPromptfooは、環境依存が大きいので **オプション依存**として扱い、
> 追加する場合は `requirements.txt` で明確にpinする（例：`deepeval==3.8.4`）。

### 3.2.1 重要（事実関係）

- このリポジトリの **CI Minimal のRunner実装**は `runner/aidd-gate.py`（pack駆動）である。
- Phase 1 の確実な出力は `output/`（JSON）であり、Allure統合（`allure-results/`）は段階導入とする。

### 3.3 配布形態

- **Docker（推奨）**：CIでもローカルでも同一環境を担保
- **ローカルCLI**：Pythonが入っている前提のメンバー向け

### 3.4 入出力（ファイルシステムI/O）

- 入力（例）
  - `artifacts/`：企画/要件/設計のYAML/MDなど
  - `packs/`：チェックリスト/スキーマ/プロンプト/曖昧語辞書など
  - `checklistresults.json`：Coach（または代替手段）から出力される判断ログ
- 出力（例）
  - `output/`：ゲート結果JSON（集計・差分・トレースの機械可読成果物）
  - `allure-results/`：Allureレポート生成用

> 補足：現状 `runner/Dockerfile` は pytest 実行をデフォルトにしているが、pack駆動Runner（`runner/aidd-gate.py`）は pytest と独立。
> したがって、Allure統合は「pytestでpackをラップする」等の設計が別途必要。

---

## 4. データ形式 / スキーマ / ID規約

### 4.1 機械可読フォーマット

- **YAML**：人間が読みやすく、構造化もしやすい（企画〜設計の主要フォーマット）
- **JSON**：ツール連携・CI集計・Allure添付に強い（出力・中間成果物）

### 4.2 スキーマ

- JSON Schema Draft 2020-12
  - 目的：構造逸脱（最大リスク）を機械的に検出する
  - 代表：`packs/pln_pack/schemas/pln_canonical_v1.schema.json`（企画YAMLの全体像テンプレ）

> 重要：CI Minimal の pack（`packs/pln_pack/pln.pack.yaml`）は、
> 個別スキーマ（goal/scope/inspection_design）を参照する想定のため、
> 「どのpackがどのスキーマを使うか」は `docs/BACKEND_ARCHITECTURE.md` を正とする。

### 4.3 ID規約

- 形式：`{PREFIX}-{PHASE}-{PURPOSE}-{NNN}`（NNNは3桁）
  - 例：`PLN-PLN-SCOPE-001` / `CHK-PLN-AIDD-001`
- ID採番：`id/issue_id.py` によりレジストリ更新と発行ログを残す

> **【実装完了後に追記】** `id/issue_id.py`（レジストリ: `id/id_rules_registry.yaml`、ログ: `id/id_issued_log.yaml`）は未実装。本実装完了後に利用手順を追記する。

---

## 5. Coach UI（人の判断ログ：HITL）

### 5.1 目的（技術要件化）

- チェックリストを「読む→判断する→理由と証跡を残す」までをUIで強制する
- 出力を `checklistresults.json` として保存し、Gate Runner（G2）で検証可能にする

### 5.2 推奨スタック（提案）

Coach UIは、現状リポジトリに実装が無いため **提案**として定義する。

- フロント：React + TypeScript（Next.js または Vite）
- 状態管理：軽量（React state / Zustand 等）
- ストレージ：ローカルファイル（ダウンロード）またはローカルStorage（Phase 1）
- 配布：静的ホスティング or ローカル起動（サーバ不要を優先）

選定理由：

- 社内の導入障壁が低い（ブラウザで完結）
- JSON出力が容易（Runnerへの接続が素直）

---

## 6. LLM評価（Deep Eval / Promptfoo）

### 6.1 DeepEval（G4）

- 目的：上流成果物の品質を定量評価し、劣化を検知する
- 運用：
  - **スコアを合否の唯一根拠にしない**（最終判断はCoachのDone/Abort）
  - ただし **0.70未満はWarning** を必ず出す（再確認トリガ）

**フェイルセーフ（MUST）**
- APIキー未設定 / タイムアウト / 接続不可の場合は `SKIP` または `WARN` にとどめ、`FAIL` に昇格させない
- G4は「必須ゲート（G1/G2/G3）」の後に任意実行とする

**データ最小化（MUST）**
- 外部LLM APIへは評価に必要な最小テキストのみ送信する
- 機密/個人情報を含む成果物を送信する前に社内の外部送信可否ポリシーを確認する

**コスト管理（SHOULD）**
- DeepEvalのバージョンは `requirements.txt` でpin固定し、更新時はスコア推移を比較して採否を判断する
- 評価ケースは1 YAML = 1ケースを基本とし、API利用コストを最小化する

> **【実装完了後に追記】** G4のAPIキー管理・タイムアウト設定・スコア保存形式は Phase 4 実装時に確定する。

### 6.2 Promptfoo（PF）

- 目的：プロンプト品質の回帰テスト（テンプレ改善サイクルの根拠）
- 備考：Node.js依存が発生するため、Runnerと独立に実行できる構成を推奨

**フェイルセーフ（MUST）**
- PFが利用不可の場合は `SKIP/WARN` にとどめ、CIブロック（exit code 2）を返さない

> **【実装完了後に追記】** PFのセットアップ手順・実行方法・出力形式は Phase 4 実装時に確定する。

---

## 7. 互換性 / 制約（Constraints）

- Phase 1は **サーバ不要**（ローカル or 簡易ホスティング）
- CIが使えない層が存在する前提 → Docker/CLIで「同じ結果」を出すことを優先
- 機密/個人情報を扱い得る →
  - データ最小化（不要な保持・外部送信を避ける）
  - モデル利用や外部API利用がある場合は明示・隔離（企画/要件にはHowを書かない）

---

## 8. バージョニング / 依存管理ポリシー

- Python依存は `requirements.txt` で管理し、
  外部依存（DeepEval等）は **pin（固定）** を原則とする
- Pack（チェックリスト/スキーマ/プロンプト）は「資産」なので、
  変更は互換性（破壊的変更）に注意し、バージョンや履歴を残す

---

## 9. Open Questions（要確認）

- Coach UIをPhase 1でどの程度作るか（UI実装 vs JSONテンプレ入力）
- DeepEval/Promptfooを「必須ゲート」とする工程範囲（PLNのみ？REQ以降？）
- Runnerの単一CLI（`runner/aidd-gate.py`）へ、既存の `runner/gates/*` をどう統合するか

---

## 9.1 As-Is Note（2026-03-01時点の事実）

- `packs/pln_pack/pln.pack.yaml` は個別スキーマ（goal/scope/inspection_design）を参照する想定だが、
  現状 `packs/pln_pack/schemas/goal.schema.json` 等の参照先が不足しており、
  `python runner/aidd-gate.py --pack packs/pln_pack/pln.pack.yaml` はそのままでは失敗する。
- したがって Phase 1 の技術的な現状は「Runner自体はあるが、pack資産の整備が追いついていない」状態。

---

## 10. 受入（本定義書の完了条件）

- `requirements.txt` 記載の依存（pyyaml/jsonschema/pytest/allure-pytest）と矛盾がない
- Phase 1 の正の出力が `output/`（JSON）であることが明確である
- Coach UIのスタックは「提案」であり、企画/要件の正ではない（How隔離ポリシーと矛盾しない）
