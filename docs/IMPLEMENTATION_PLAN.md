# 実装計画: QA4AIDD Gate + Coach

> 本書は、企画（PLN-PLN-FLW-002.md）を実装へ落とすための、段階導入前提の実装計画（マイルストーン/タスク/完了条件/リスク）を定義する。
> 参照：`docs/PRD.md` / `docs/BACKEND_ARCHITECTURE.md` / `docs/FRONTEND_GUIDELINES.md`

---

## 1. 実装方針（大原則）

1. **最終判断は人（Coach）**：スコアは参考で、Done/Abortが最終判定
2. **検証は自動（Runner）**：構造・スキーマ・曖昧語・トレース等は機械的に検出
3. **証跡は成果物として残す**：JSON/YAMLで保存し、Allure等で可視化
4. **段階導入**：Coach先行（教育）→ Runner任意（ローカル）→ CI接続（チーム単位）
5. **AIのHowは隔離**：企画/要件にモデルやプロンプト詳細を持ち込まない

---

## 1.1 スコープ制約（この計画で扱う/扱わない）

- 本計画は「このリポジトリが提供する品質ゲート基盤」を対象とする。
- Coach UIの実装は段階導入であり、Phase 1 では **UIがなくても checklistresults.json を生成できれば良い**。
- Allure統合は価値が高いが、Phase 1 の正の出力は `output/`（JSON）である。

---

## 2. マイルストーン（Phase Plan）

### Phase 0：定義と契約を固める（最優先）

**目的**：後工程の手戻り要因（データ契約・ID・入出力）を最初に固定する。

- P0-1: `checklistresults.json` のスキーマ（契約）を確定
  - Runner（G2）の入力期待と一致させる
  - Coach UIの出力仕様を固定する
- P0-2: Pack（pln.pack.yaml）の最小仕様と拡張方針を確定
- P0-3: ID規約運用（issue_id.py）を利用手順として整備

**完了条件（Definition of Done）**

- `docs/BACKEND_ARCHITECTURE.md` の「G2データ契約」に沿ったサンプルJSONがあり、
  G2が解釈できることを確認できている

> 重要：この完了条件は「コードを改修して達成する」ではなく、
> **まずドキュメントと契約の確定（SSOT化）を完了させる**ことを指す。

### Phase 1：Runner（CI Minimal）を安定化

**目的**：CIが使える/使えない双方に「自動ゲート」を提供する。

- P1-1: `runner/aidd-gate.py` の pack 実行を標準手順化
- P1-2: PLN pack（`packs/pln_pack/pln.pack.yaml`）の参照パス整備
- P1-3: 出力 `output/pln_gate_report.json` のフォーマット固定（後続集計のため）
- P1-4: Docker実行の手順化（README/コマンド例）

**完了条件**

- ローカル/CIで同じpackを実行でき、FAIL/WARN/PASSが再現する

> 事実：`runner/aidd-gate.py` は WARN を終了コードに反映しない（FAIL以外は0）。
> したがって「CIでブロックする」条件は FAIL のみであり、WARNはレポートで扱う。

### Phase 2：Coach（教育/判断ログ）を最小で立ち上げる

**目的**：人の最終判断と理由・証跡を残す仕組みを先に成立させる。

- P2-1: Coach UIのMVP（S-001/S-010/S-020/S-050）
- P2-2: `checklistresults.json` の生成（ABORT理由必須）
- P2-3: 判断ログの履歴（最低限：更新前を残す）

**完了条件**

- ユーザーがチェックリストを読み、Done/Abortを入力し、理由と証跡を残し、
  JSONを出力できる

### Phase 3：Runner×Coach接続（G2の価値を最大化）

**目的**：人の判断ログを自動ゲートに接続し、形骸化を抑止する。

- P3-1: packの `paths.checklist_results` をCoach出力に接続
- P3-2: G2の判定ロジック（TODO残/Abort理由なし/Abort率）を運用ポリシー化
- P3-3: Allureへの統合方針を決定（pytestラップ or Allure results生成）

**完了条件**

- Coach出力を含めてpack実行が通り、G2でFail/Warnが出せる

### Phase 4：高機能ゲート（G3/G4/G5/PF）を段階統合

**目的**：品質ゲートを工程横断の標準として揃える。

- P4-1: G3（Schema）をpackへ統合（分割YAML対応含む）
- P4-2: G4（DeepEval）を運用モードとして追加（必須ではなく警告中心）
- P4-3: G5（Trace）を「Core（検査・可視化）」として実装し、Adapterは将来に分離
- P4-4: PF（Promptfoo）を独立ジョブとして組み込み、回帰評価を可能にする

**完了条件**

- 主要ゲートが、同一成果物群から一貫した形式でレポートを生成できる

---

## 3. 具体タスクリスト（Backlog）

### 3.1 Runner（バックエンド）

- [ ] packに `deep_eval` / `traceability` 等の kind を追加するか設計判断
- [ ] `output/` 配下の命名規則と保存形式を統一（後続のAllure集約を見据える）
- [ ] DeepEval導入時の依存固定（`deepeval==x.y.z`、APIキーなどの扱い）

### 3.2 Coach（フロントエンド）

- [ ] チェックリスト（YAML）の取り込み方式決定（同梱 vs アップロード）
- [ ] ABORT理由必須・保存不可のUI実装
- [ ] JSON出力と保存先案内（ローカルファイル）

### 3.3 共通（運用/ガバナンス）

- [ ] スコア運用ポリシー（0.70未満Warning、ただし合否の唯一根拠にしない）を明文化
- [ ] 機密/個人情報の取り扱い（入力/出力の保管場所、共有範囲）
- [ ] `CHK-PLN-AIDD-001.yaml` の各カテゴリ（CAT-040 ゴールドデータ、CAT-070 ドリフト検知）の整備計画

### 3.4 【実装完了後に追記】未実装スクリプト一覧

以下のスクリプトは企画書（`artifacts/planning/PLN-PLN-FLW-002.md`）に記載されているが、本実装完了後に追記・確認すること。現時点では使用方法の探索・手順確認は不要。

| スクリプト | 対応企画書セクション | 状態 |
|---|---|---|
| `id/issue_id.py` | §13 ID発行・管理 | 未実装 |
| `id/id_rules_registry.yaml` | §13 ID発行・管理 | 未実装 |
| `runner/gates/g1_ambiguity.py` | §8.2 Gate G1 | 空ファイル（実体は `aidd-gate.py` 内） |
| `runner/gates/g2_checklist_completion.py` | §8.2 Gate G2 | 空ファイル（実体は `aidd-gate.py` 内） |
| `runner/gates/g5_trace.py` | §8.2 Gate G5 | 未実装 |
| `runner/gates/g4_deepeval.py` | §8.2 Gate G4 / §9 | Phase 4 で統合予定 |
| Promptfoo（PF） | §8.2 Gate PF / §9 | Phase 4 で統合予定 |

---

## 7. 受入（本計画の品質条件）

- `docs/PRD.md` の非ゴール（How隔離、サーバ不要）と矛盾しない
- データ契約（checklistresults.json）を Phase 0 で最優先に固定する構造になっている
- Phase 1 の成果物（CI Minimal）が `output/`（JSON）であることを明記している

---

## 4. リスクと対策（実装計画としての）

| リスク                          | 影響                        | 対策                                                       |
| ------------------------------- | --------------------------- | ---------------------------------------------------------- |
| checklistresults.json契約が曖昧 | CoachとRunnerが接続できない | Phase 0でスキーマ固定 + サンプル + 自動検証                |
| DeepEvalの環境依存/コスト       | CIで不安定、遅い/高い       | まずはオプション扱い、pin固定、timeout回避（1 YAML=1case） |
| 形骸化（適当Done）              | 品質ゲートが機能しない      | 理由必須、G2でブロック、Abort分析                          |
| CIが使えない層が多い            | 導入が進まない              | Coach先行 + Docker/CLIでローカル運用                       |

---

## 5. 成果物一覧（この計画が生むもの）

- `checklistresults.json` スキーマ/サンプル
- `packs/<phase>_pack/*.pack.yaml` の拡張
- Gate Runner（CLI/Docker）実行手順
- Coach UI（MVP）
- Allure統合（段階導入）

---

## 6. 参照

- 企画書：`artifacts/planning/PLN-PLN-FLW-002.md`
- AIDD企画段階チェックリスト：`packs/checklists/CHK-PLN-AIDD-001.yaml`
- PRD：`docs/PRD.md`
- 画面遷移：`docs/SCREEN_FLOW.md`
- 技術スタック：`docs/TECH_STACK.md`
- フロントエンド指針：`docs/FRONTEND_GUIDELINES.md`
- バックエンド構造：`docs/BACKEND_ARCHITECTURE.md`
