# RES-PLN-EVAL-001（G4 / Run-1: pln_transform）評価レポート

## 1. 実行サマリ

- run名: **pln_transform**
- 参照モード: **MD**
- 評価対象: `artifacts\planning\yaml`
- テストケース数 / 合格率 / メトリクス平均（JSONから転記）
  - yaml_files: **12**（evaluated: **11**, skipped: **1**）
  - total_test_cases: **11**
  - passed / failed: **3 / 8**
  - pass_rate: **0.2727**（= 27.3%）
  - metric_averages:
    - Faithfulness: **1.0**
    - 参照↔YAML突合（チェックリスト準拠） [GEval]: **1.0**
- 出力JSON（最新のRun-1）: `output\G4\pln_transform\artifacts_planning_yaml\0301_1539.json`

> 注: 上記の metric_averages は「スコアが `null` になったケース」を平均計算から落としているため、**見かけ上 1.0 になっている**可能性があります（詳細は後述）。

---

## 2. 全体所見（結論）

1. 本Run-1の不合格（8/11）は、企画YAMLの変換品質というより **DeepEval実行の失敗（FaithfulnessのLengthFinishReasonError）** に強く支配されています。現状の合格率 27.3% は、変換品質を反映していません。
2. **CONSISTチェックリスト（CHK-PLN-CONSIST-001）の実質評価が行われていない**（GEvalが「適用項目なし→SKIP」扱いになっている）ため、「欠落/矛盾/誤変換」を検出できていません。
3. ただし手動確認では、少なくとも **`PLN-PLN-GOAL-001.yaml` がチェックリスト要求（PLN-CONS-100）を満たしていない**疑いが濃厚で、Run-1が正しく動けばFail要因になりえます。

---

## 3. 重大問題（High Priority）

### HP-1: FaithfulnessMetric がほぼ全件で LengthFinishReasonError → 合否が変換品質ではなく「評価失敗」で決まっている

- 対象yaml_file: **複数**（例: `PLN-PLN-CONS-001.yaml`, `PLN-PLN-DES-001.yaml`, `PLN-PLN-FLW-001.yaml`, `PLN-PLN-GOAL-001.yaml`, `PLN-PLN-INT-001.yaml`, `PLN-PLN-PROB-001.yaml`, `PLN-PLN-SCOPE-001.yaml`, `PLN-PLN-TBL-001.yaml`）
- セクション: 各ファイルの present_sections（constraints/architecture/workflow/goal/...）
- 問題内容:
  - DeepEval出力JSON上、Faithfulness が `score: null` になり `success: false` となっており、その原因が **LengthFinishReasonError（length limit reached）** です。
  - 結果として `details[].tr_success=false` となり、**変換の欠落・矛盾以前にテストが成立していません**。
- 根拠:
  - DeepEval JSON: `details[].metrics[]` の `error` に以下（同型のエラー）が多数。
    - 例（`PLN-PLN-CONS-001.yaml`）: `details[?].metrics[0].error = "LengthFinishReasonError: Could not parse response content as the length limit was reached ... completion_tokens=32768 ..."`
- 修正案（評価の成立を最優先）:
  - `runner/gates/g4_deepeval.py` 側で Faithfulness の「生成量」を抑制する（後述のスクリプト改善案参照）
  - 参照MDを docごとに必要部分へ絞る（MD全文一括のままだと、Faithfulnessの内部プロンプトが肥大化しやすい）
  - まずは Run-1（pln_transform）では **Faithfulnessを無効化**し、CONSIST（構造・必須キー）に寄せる（Run-2側で別軸として扱う）

---

### HP-2: GEval が「項目別の判定JSON」を返していない（geval_json が常に null）→ どの欠落/矛盾で減点されたか追えない

- 対象yaml_file: **evaluated=11 の全件**
- セクション: 全般
- 問題内容:
  - `runner/gates/g4_deepeval.py` は GEval の `reason` を `safe_parse_json()` でJSON化し、`details[].geval_json` に格納する設計です。
  - しかし実際の出力では `details[].geval_json` が全件 `null` で、項目別の YES/NO/HOLD/SKIP が取得できていません。
  - これにより、「欠落/矛盾/誤変換がある場合、どのyaml_fileのどのセクションが原因か？」が **JSON上からは答えられない**状態です。
- 根拠:
  - DeepEval JSON: `details[].geval_json` が全件 `null`
  - DeepEval JSON: `details[].metrics[]` のうち `name = "参照↔YAML突合（チェックリスト準拠） [GEval]"` の `reason` が、指定JSONではなく英語の説明文になっている
    - 例: `"The evaluation steps require checking for applicable checklist items ..."`
- 修正案:
  - GEvalの「出力がJSONのみ」という制約をより強制（プロンプト修正 + パース失敗時は success=false にする、など）
  - もしくは GEval を「LLMが返したJSON」ではなく **スクリプト側でルール評価→JSON化**（LLMに丸投げしない）

---

### HP-3: Run-1（CONSIST中心）のはずが、実質「適用項目なし→SKIP」になっていて CONSISTルールが評価されていない

- 対象yaml_file: evaluated=11 の全件
- セクション: 全般（特に GOAL/SCOPE 必須キー等の検査）
- 問題内容:
  - 本Runの `meta.checklists` は `CHK-PLN-CONSIST-001.yaml` のみです（DeepEval JSON: `meta.checklists`）。
  - 一方 `g4_deepeval.py` の GEval は「適用チェック項目一覧（= AIDD items想定）」を中心に判定する作りです。
  - CONSISTは `summarize_consist_checklist()` でテキスト化され **INPUTに混ぜ込まれているだけ**で、GEvalに「このrulesを個別に検査して判定を返せ」とは言っていません。
  - その結果、GEval側が「適用項目が無いのでSKIP扱い」と解釈し、ほぼ満点（1.0）になっています。
- 根拠:
  - DeepEval JSON: `meta.checklists = [...CHK-PLN-CONSIST-001.yaml]`（AIDD未使用）
  - DeepEval JSON: 多数のGEval `reason` に「適用項目なし→SKIP」と明記
    - 例（`PLN-PLN-GOAL-001.yaml`）: `details[?].metrics[1].reason` に「no applicable checklist items ... SKIP」趣旨
  - CHK-PLN-CONSIST-001.yaml には Fail 相当の必須ルールが存在（例: PLN-CONS-100, PLN-CONS-110）
- 修正案:
  - CONSISTの `rules` を AIDD items 相当の「評価対象項目リスト」に変換し、GEvalへ「項目別判定（YES/NO/HOLD）」させる
  - あるいは、CONSISTルールはLLM評価ではなく **決定性のある静的検査**（ファイル存在、必須キー、空配列禁止、TODO残存禁止等）としてスクリプト内で実装する

---

### HP-4: （変換品質そのものの疑義）`PLN-PLN-GOAL-001.yaml` が CONSIST必須キー（PLN-CONS-100）を満たしていない可能性

- 対象yaml_file: `artifacts\planning\yaml\PLN-PLN-GOAL-001.yaml`
- セクション: `goal`
- 問題内容:
  - CHK-PLN-CONSIST-001 のルール **PLN-CONS-100** は以下を要求しています:
    - `PLN-PLN-GOAL-001.yaml` に `goal.primary_goal / success_criteria / scope_in / scope_out / abort_conditions` が存在
  - 現状の `PLN-PLN-GOAL-001.yaml` は以下の形で、**scope_in/scope_out/abort_conditions が summary（\*\_summary）としてのみ存在**しています。
    - `goal.scope_in_summary`
    - `goal.scope_out_summary`
    - `goal.abort_conditions_summary`
  - そのため、ルール文言通りに評価すると **欠落（missing required keys）** になります。
- 根拠:
  - チェックリスト: `packs\checklists\CHK-PLN-CONSIST-001.yaml` > `rule_id: PLN-CONS-100`
  - YAML実体: `artifacts\planning\yaml\PLN-PLN-GOAL-001.yaml` の `goal` 配下に `scope_in` / `scope_out` / `abort_conditions` が存在しない
  - 参照MD（要旨）: `artifacts\planning\PLN-PLN-FLW-002.md` 8.1 に「成功条件/KPI」「スコープ」「Abort条件」を企画段階で必須にする旨が明記
- 修正案（YAML側）:
  - 最短の整合: `PLN-PLN-GOAL-001.yaml` に以下を **実値で追加**（TODO禁止ルールに注意）
    - `goal.scope_in`: `PLN-PLN-SCOPE-001.yaml#scope.scope_in` の内容を転記
    - `goal.scope_out`: `PLN-PLN-SCOPE-001.yaml#scope.scope_out` の内容を転記
    - `goal.abort_conditions`: `PLN-PLN-SCOPE-001.yaml#scope.abort_conditions` の内容を転記
  - もし「SSOTとしてSCOPEに寄せ、GOALは要約のみ」が設計意図なら、チェックリスト PLN-CONS-100 を設計に合わせて修正（ただし本レポートでは“現ルール基準”で問題として扱う）

---

### HP-5: `derived_from` が存在しない参照（`PLN-PLN-FLW-001.md`）を指している → 参照整合性が崩れている

- 対象yaml_file: 複数（例: `PLN-PLN-GOAL-001.yaml`, `PLN-PLN-SCOPE-001.yaml`, `PLN-PLN-DES-001.yaml`, `PLN-PLN-EVAL-001.yaml`, `PLN-PLN-TBL-001.yaml`, `PLN-PLN-AIQUA-001.yaml` ほか）
- セクション: `derived_from`
- 問題内容:
  - 参照元MDとしてこのRunで指定されているのは `artifacts\planning\PLN-PLN-FLW-002.md` です（DeepEval JSON `meta.md_path`）。
  - しかし複数のYAMLが `derived_from: - artifacts/planning/PLN-PLN-FLW-001.md...` を指しています。
  - リポジトリの `artifacts/planning/` 直下には `PLN-PLN-FLW-002.md` しか見当たらず、`PLN-PLN-FLW-001.md` が存在しません（ディレクトリ一覧より）。
  - これにより、企画MD→企画YAML変換の「出典リンク」が壊れており、追跡不能です。
- 根拠:
  - 参照MD: `output/G4/pln_transform/artifacts_planning_yaml/0301_1539.json` > `meta.md_path = ...PLN-PLN-FLW-002.md`
  - 実ファイル: `artifacts/planning/` 直下は `PLN-PLN-FLW-002.md` のみ
  - YAML例: `PLN-PLN-GOAL-001.yaml` > `derived_from: - artifacts/planning/PLN-PLN-FLW-001.md`
- 修正案（YAML側）:
  - `derived_from` の参照を、存在する `PLN-PLN-FLW-002.md`（必要なら `#見出しアンカー` 付き）に一括置換

---

## 4. 中程度問題（Medium Priority）

### MP-1: 集計値（metric_averages）が実態を反映しない（エラー/NULLが平均から除外される）

- 対象yaml_file: 全般（集計ロジック）
- セクション: `summary.metric_averages`
- 問題内容:
  - `Faithfulness` の多くが `score: null` でありながら、平均が 1.0 になっています。
  - 平均算出が「scoreが取れたケースのみ」になっているため、失敗ケースがサマリに表れません。
- 根拠:
  - DeepEval JSON: `summary.metric_averages.Faithfulness = 1.0`
  - DeepEval JSON: 多数 `details[].metrics[Faithfulness].score = null` かつ `error` あり
- 修正案:
  - `metric_averages` に **error_count / null_count** を併記する
  - もしくは `null` を 0.0 として平均に含め「評価不能はFail相当」として見える化する

### MP-2: `RES-PLN-TRANS-001.md` が空（readできない/存在しても無内容）で、過去レポート比較ができない

- 対象: `output\G4\reports\pln_transform\RES-PLN-TRANS-001.md`
- 問題内容:
  - 本ファイルは読み取り結果が空でした（ツール結果: "tool did not return anything"）。
  - 過去Runとの差分比較ができず、改善サイクルが回りにくい状態です。
- 修正案:
  - 既存レポートの出力先/ファイル名ルールを整理し、上書き/出力漏れを防ぐ（本Runでは `RES-PLN-EVAL-001.md` が正）

---

## 5. スクリプト改善提案（g4_deepeval.py）

### 5.1 今回の結果が正しく集計できているか（結論）

- **できていません**。
  - 失敗の大半が `FaithfulnessMetric` の `LengthFinishReasonError` であり、変換品質ではなく評価実行失敗に引っ張られています。
  - GEvalの「項目別判定JSON」が `geval_json` として残っておらず、原因追跡が不可能です。
  - CONSISTルールが実質「適用項目なし→SKIP」扱いになっており、不要観点で減点しない設計意図と逆に「必要観点すら評価しない」状態です。

### 5.2 具体的な修正ポイント（関数名/変数名レベル）

#### (A) FaithfulnessMetric の扱い（timeout/length回避）

- 対象: `build_metrics(enable_faithfulness: bool)` / `main()`
- 変更案:
  - PLNのpln_transform（MD↔YAML変換）では Faithfulness をデフォルト無効化、または `include_reason=False` を検討
  - `build_test_case()` の `ref_for_input` 先頭12000文字カットだけでは不足（MD全文が長い）。docの `present_sections` に応じた「参照MDの抜粋」へ変更

疑似差分（最小パッチ例）:

```diff
@@ def build_metrics(enable_faithfulness: bool) -> List[Any]:
-    if enable_faithfulness:
-        metrics.append(FaithfulnessMetric(threshold=FAITHFULNESS_THRESHOLD, include_reason=True))
+    if enable_faithfulness:
+        # length/timeout回避：理由生成を抑制（まず評価成立を優先）
+        metrics.append(FaithfulnessMetric(threshold=FAITHFULNESS_THRESHOLD, include_reason=False))
```

```diff
@@ def main(...):
-    metrics = build_metrics(enable_faithfulness=True)
+    # Run-1(pln_transform)ではまずCONSIST成立を優先し、Faithfulnessはオプション化
+    enable_faith = os.getenv("AIDD_ENABLE_FAITHFULNESS", "0") == "1"
+    metrics = build_metrics(enable_faithfulness=enable_faith)
```

#### (B) CONSISTルールを「評価項目」として扱い、GEvalが判定JSONを返せるようにする

- 対象: `summarize_consist_checklist()` / `build_metrics()` / `build_test_case()`
- 問題:
  - CONSISTがテキストで渡されるだけで、GEvalの出力JSON（results）に rule_id 単位の判定が乗らない
- 変更案（方向性）:
  1. CONSIST rules を `ChecklistItem` 互換に変換（`item_id=rule_id`, `title=title`, `risk=severity` 相当）
  2. `format_applicable_items_for_prompt()` に CONSIST由来の項目も渡し、GEvalに「各rule_idをYES/NOで判定させる」

疑似差分（概念）:

```diff
@@ def load_checklists(paths):
-    consist_rules_text = ...
-    aidd_summary = ...
-    return consist_rules_text, aidd_summary, aidd_items
+    consist_rules_text = ...  # 参考として残す
+    consist_items = parse_consist_rules_as_items(chk)  # NEW
+    # Run-1では aidd_items は空でも、consist_itemsがあれば GEval はそれを評価できる
+    return consist_rules_text, aidd_summary, (aidd_items + consist_items)
```

#### (C) GEvalの「JSONのみ出力」違反を検知して fail にする

- 対象: `safe_parse_json()` / `main()` の `parsed = safe_parse_json(ge_reason)`
- 変更案:
  - `parsed is None` の場合、`tr_success` を False 扱いにする、またはメトリクスのsuccessを False にする（DeepEvalの枠内で難しければスクリプト側でpost-check）
  - 目的は「原因追跡可能な成果物（geval_json）を必須にする」

---

## 6. 次アクション

### ① YAML修正の順番（どれから直すか）

1. `PLN-PLN-GOAL-001.yaml`（PLN-CONS-100に抵触しうる必須キー欠落の解消）
2. `derived_from` の参照修正（`PLN-PLN-FLW-001.md` → 実在する `PLN-PLN-FLW-002.md`）
3. その後、他YAML（CONS/DES/FLW/INT...）は「参照整合」と「必須キーの整合」を横断チェック

### ② 再実行の条件（どのRunを回すか）

- Run-1（pln_transform）を再実行
  - 条件:
    - Faithfulness を無効化、または length/timeout 回避策を入れて **11ケースが評価完走すること**
    - GEval が `geval_json` を生成し、rule_id / item_id 単位で追跡できること

### ③ 合格基準（今回のRun-1での到達目標）

- 最低基準（評価基盤の成立）:
  - `details[].metrics[].error` が 0 件（少なくとも LengthFinishReasonError を解消）
  - `details[].geval_json` が evaluated 全件で `null` ではない（判定JSONが残る）
- 変換品質としての基準（CONSIST中心）:
  - CHK-PLN-CONSIST-001 の必須ルール（特に PLN-CONS-100, PLN-CONS-110）を満たすこと
  - pass_rate は暫定目標として **>= 0.9**（まずは「評価が落ちない」状態の確認）
