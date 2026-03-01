# DeepEval 評価レビュー & 改善提案（MD vs 分割YAML v1）

対象評価結果:

- `output/deepeval/planning/eval_md_vs_yaml_v1.json`

評価スクリプト（参考）:

- `DeepEval/evaluate_planning_md_vs_yaml_v1.py`

---

## 1. サマリ（結論）

評価結果の読み取りから、現状の低スコア/低合格率の主因は **「分割YAMLに対する“適用項目（Applicable items）判定”が機能していない」** ことと、
**評価スクリプト側の実装バグ（GEvalのメトリクス名取り回し）** により集計が欠損していることです。

特に、AIDDチェックリスト（`CHK-PLN-AIDD-001.yaml`）の多くの項目に `evidence_hint` が無いため、
スクリプトが「一般項目＝どの分割YAMLにも適用」と解釈してしまい、
本来そのYAMLが責務として持たない観点まで **NO扱いで減点** されやすい状態になっています。

加えて、複数ケースで **Timeout**（RetryError/TimeoutError）が発生しており、評価の安定性も不足しています。

---

## 2. 評価結果の概観（eval_md_vs_yaml_v1.json）

集計（`summary`）:

- YAMLファイル数: 12
- 評価実施: 11 / スキップ: 1
- 合格: 1 / 不合格: 10（合格率 9.09%）
- メトリクス平均:
  - Faithfulness: **0.986**（概ね矛盾は少ない）
  - 企画MD↔YAML突合（チェックリスト準拠）[GEval]: **0.479**（低い）

個別傾向（`details`）:

- `PLN-PLN-AIQUA-001.yaml` は GEval 0.986で合格。
- `PLN-PLN-SCOPE-001.yaml` は GEval 0.479で不合格（「スコープ観点はあるが、他観点が欠落」という判定）。
- `PLN-PLN-CONS-001.yaml` / `PLN-PLN-DES-001.yaml` は 0.23〜0.26程度で不合格。
- `PLN-PLN-FLW-001.yaml` / `PLN-PLN-GOAL-001.yaml` / `PLN-PLN-PROB-001.yaml` / `PLN-PLN-TBL-001.yaml` などで Timeout が多発。

---

## 3. 根本原因（なぜ低スコアになっているか）

### 3.1 「分割YAML前提」の“適用判定”が成立していない

`DeepEval/evaluate_planning_md_vs_yaml_v1.py` の `is_item_applicable_to_doc()` は以下の仕様です:

- `evidence_hint` に `YAML: scope...` 等があれば、そのセクションを含む分割YAMLだけを評価対象にする
- `evidence_hint` が無い場合は「一般項目」扱いで、**present_sections があるなら適用** してしまう

一方で `CHK-PLN-AIDD-001.yaml` は、90番台（090-092）以外の多くの項目に `evidence_hint` がありません。
そのため、例えば `PLN-PLN-DES-001.yaml`（architectureのみ）でも、
入力要件・出力要件・評価・ガバナンス等の項目まで「適用」と判断され、記述が無い＝NOになりやすい構造です。

> これは「分割YAMLでは全項目必須ではない。該当セクションが無ければSKIP」
> という設計意図と逆方向に働きます。

### 3.2 評価スクリプト側のバグ: GEvalメトリクス名が一致していない

評価結果JSONを見ると、GEvalの `metrics[].name` は

- `企画MD↔YAML突合（チェックリスト準拠） [GEval]`
  のように **末尾に ` [GEval]` が付与** されています。

しかしスクリプトは以下の完全一致で探しています:

- `if getattr(m, "name", "") == "企画MD↔YAML突合（チェックリスト準拠）":`

この不一致により、

- `overall_score` が `null` のまま
- `geval_json` の抽出も常に失敗
  となっており、後段の分析/レポート生成の材料が欠けます。

### 3.3 Timeoutの多発（評価の安定性不足）

複数のYAMLで `RetryError ... TimeoutError` が発生しています。
原因候補:

- INPUTに「MD 12000文字 + チェックリスト要約 + 適用項目一覧」を詰め込み、トークンが重い
- 1ケースで Faithfulness + GEval の2回評価が走り、外部API負荷が高い
- throttle_value=1.0 / sleep=0.8 が環境によっては不足

---

## 4. 改善提案（優先度順）

以下、「即効性（すぐ効く）」→「構造改善（中期）」の順で提案します。

### A. 即効性: スクリプトのバグ修正（必須）

対象: `DeepEval/evaluate_planning_md_vs_yaml_v1.py`

1. **GEvalメトリクス名の検出ロジックを部分一致にする**

- 例: `"企画MD↔YAML突合（チェックリスト準拠）" in metric_name` で拾う
- これで `overall_score` が正しく埋まり、集計・可視化が改善します

2. **GEval reasonからJSONを抽出する設計を見直す**

- 現状のDeepEval GEvalでは、`reason` が必ずしも criteria で指定した「JSONのみ」になりません
- 「項目別 YES/NO/HOLD/… の構造化結果」を本当に取りたい場合は、
  - (案1) GEvalではなく **独自のLLM呼び出し（JSON出力専用）を別途実行** して保存
  - (案2) DeepEvalの別メトリクス/CustomMetricで「JSON出力→自前採点」へ変更

### B. 即効性: Timeout低減（評価の安定化）

対象: `DeepEval/evaluate_planning_md_vs_yaml_v1.py`（または `runner/gates/g4_deepeval.py` への寄せ）

提案:

- `DEEPEVAL_ASYNC_CONFIG.throttle_value` を 2.0〜 に増やす
- `SLEEP_BETWEEN_CASES` を 1.5〜 に増やす
- `MAX_RETRY_PER_CASE` を 3〜4 に増やす
- 参照MDを「全文」ではなく、
  - doc.present_sections と対応する章だけ抽出（例: scopeならスコープ章、constraintsなら制約章）
  - もしくは `runner/gates/g4_deepeval.py` の `build_reference_context_yaml_for_doc()` のように
    “必要セクションだけ”に絞った参照を構築

### C. 最重要（品質面）: 「適用項目（Applicable）判定」を正しくする

対象: `packs/checklists/CHK-PLN-AIDD-001.yaml` と / または `evaluate_planning_md_vs_yaml_v1.py`

#### 方針案（推奨）: チェックリストに evidence_hint を拡充する

現状、090-092以外は evidence_hint がほぼ無いため、分割YAMLでのSKIP制御ができません。

以下のように、各itemに「この項目はどのYAMLセクションで宣言されるべきか」を明示します（例）:

- 010-013（AI利用前提）: `YAML: goal` / `YAML: scope` / `YAML: ai_quality_requirements`
- 020-023（入力・権利・分類）: `YAML: ai_quality_requirements` / `YAML: constraints`
- 030,032-034（出力・根拠・不確実性・禁止）: `YAML: ai_quality_requirements` / `YAML: goal`
- 040-043（評価指標・AC・重大度）: `YAML: ai_quality_requirements` / `YAML: score_policy` / `YAML: goal`
- 050-053（失敗モード）: `YAML: ai_quality_requirements` / `YAML: constraints`
- 060-062（ガバナンス）: `YAML: constraints` / `YAML: ai_quality_requirements` / `YAML: traceability`
- 080-081（コスト上限・フェイルセーフ）: `YAML: constraints` / `YAML: ai_quality_requirements`

こうしておくと、例えば `architecture` しか持たない分割YAMLに、
入力/出力/ガバナンス等を強制しなくてよくなり、
**「分割YAMLは責務外ならSKIP、責務ならYES/NO/HOLD」** の評価が成立します。

#### 方針案（代替）: スクリプト側で evidence_hint 未設定項目をSKIPに倒す

`is_item_applicable_to_doc()` の末尾ロジックを変え、

- evidence_hint が無い項目は「分割YAMLでは適用しない（SKIP）」
  または
- item_id prefix（010/020/…）に応じて “推定セクションマップ” を適用

これでも改善しますが、チェックリスト自体が「どこで何を宣言するか」を明示できるため、
チェックリスト側に evidence_hint を持たせる方が運用上は堅いです。

### D. YAML側の改善案（分割YAMLの責務を明確化）

今回、`PLN-PLN-AIQUA-001.yaml` は「多くのAIDD観点」を内包しているため高得点です。
一方、`PLN-PLN-SCOPE-001.yaml` 等はスコープとしては充実しているのに、
評価が「他観点が無い」と解釈し低スコアになっています。

改善の方向性は2つあります:

1. **“責務分割”を徹底し、チェックリスト適用も分割に追従させる（推奨）**

- scope YAMLにはscope系項目（091など）だけが適用されるようにする（= evidence_hintを整備）

2. **各分割YAMLに「このファイルで満たすチェック項目の宣言（YES/NO/HOLD）」を持たせる**

- 例: 各YAMLに `checklist_status:` セクションを追加し、対象項目だけ列挙
- ただし「分割YAMLが冗長になる」副作用あり

---

## 5. 追加観点（Faithfulnessで出た軽微な矛盾）

- `PLN-PLN-CONS-001.yaml`:
  - constraints を「企画段階で確定した不変条件」と断定している点が、参照根拠からは強すぎる可能性（Faithfulness 0.9375）。
  - 対応: `constraints.summary` の断定表現を弱め、`invariant: true` が付与された制約のみ不変とする等に寄せる。

- `PLN-PLN-INT-001.yaml`:
  - Gate Runner に「prompt injection detection gate がある」と誤って述べた旨（Faithfulness 0.98）。
  - 対応: 実際のゲート定義（G1〜G5/PF）と一致する記述に修正し、注入対策は G1/G3の前処理や別ルールとして整理する。

---

## 6. 再評価手順（最小）

現行の実行は以下（PowerShell）:

```powershell
runner\gates\scripts\run_g4_pln.ps1
```

改善案（Timeoutが出る場合の推奨）:

- throttle/sleep/retry を増やした版で再実行
- 参照を「必要セクションのみ」に絞った版（`runner/gates/g4_deepeval.py` の参照YAML抽出ロジック）を採用

---

## 7. 次アクション（推奨ロードマップ）

1. **（必須）スクリプトのGEvalメトリクス名取り回しバグを修正**
2. **AIDDチェックリストに evidence_hint を追加**（分割YAMLの適用判定を成立させる）
3. **Timeout対策**（参照縮約 + throttle/sleep/retry調整）
4. 必要であれば **項目別判定JSONを別途生成**（GEval理由のJSON化に依存しない）
