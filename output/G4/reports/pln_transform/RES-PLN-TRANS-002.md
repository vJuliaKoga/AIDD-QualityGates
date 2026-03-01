---
meta:
  artifact_id: RES-PLN-TRANS-002
  file: RES-PLN-TRANS-002.md
  author: Cline
  source_type: ai
  prompt_id: PRM-PLN-TRANS-001
  source: output/G4/pln_transform/artifacts_planning_yaml_v2/0301_1957.json
  timestamp: "2026-03-01T19:58:00+09:00"
  model: (report)
  content_hash: PENDING
---

# RES-PLN-TRANS-002（G4 / Run-1: pln_transform）評価レポート

> 対象: **企画MD ↔ 企画YAML 分割**の変換品質（欠落なく／矛盾なく／誤った言い換えなく）

本レポートの根拠は、**Run-1（最新）のDeepEval出力JSON** `output\G4\pln_transform\artifacts_planning_yaml_v2\0301_1957.json` と、同JSONが指す参照MD/評価対象YAML/チェックリスト/スクリプト（PRM-PLN-TRANS-001で指定）に限定します。
（過去レポート `RES-PLN-TRANS-001` の内容を根拠として転記・流用はしていません。）

---

## 1. 実行サマリ

- run名: **pln_transform**
- 参照モード: **MD**
- 評価対象: `artifacts\planning\yaml\v2`
- テストケース数 / 合格率 / メトリクス平均（DeepEval出力JSONから転記）
  - yaml_files: **11**
  - evaluated / skipped: **11 / 0**
  - total_test_cases: **11**
  - passed / failed: **5 / 6**
  - pass_rate: **0.4545**（= 45.45%）
  - metric_averages:
    - 参照↔YAML突合（チェックリスト準拠） [GEval]: **1.0**
    - Faithfulness: **1.0**
- 出力JSONファイル: `output\G4\pln_transform\artifacts_planning_yaml_v2\0301_1957.json`

補足（平均値の解釈）:

- 上記 `metric_averages` は、`details[].metrics[].score` が **null** のケース（例: Faithfulnessが LengthFinishReasonError で失敗）を平均計算に含めないため、見かけ上 1.0 になり得ます。
  - 根拠: `summary.metric_averages` は 1.0 だが、後述の通り **6件**で Faithfulness が `score:null` + `error: LengthFinishReasonError`（`details[].metrics[name=Faithfulness].error`）

---

## 2. 全体所見（結論を3〜6行）

1. 本Run-1の不合格（6/11）は、企画YAMLの変換品質そのものではなく **FaithfulnessMetric が LengthFinishReasonError で失敗していること**に強く支配されています（`details[].metrics[name=Faithfulness].error`）。

2. `CHK-PLN-CONSIST-001.yaml`（CONSISTルール）を投入しているにもかかわらず、GEvalが「適用項目なし→SKIP」前提で動いており、**欠落/矛盾/誤変換の特定に必要な項目別判定（YES/NO/HOLD）が生成されていません**（`details[].geval_json=null`）。

3. Run-1（pln_transform）としての目的（MD内容がYAMLへ落ちているかの検証）に対し、現状の出力JSONは「どのYAMLのどのセクションが原因で減点されたか」を追跡できず、**改善サイクルを回せる成果物になっていない**状態です。

---

## 3. 重大問題（High Priority）

### HP-1: FaithfulnessMetric が 6件で LengthFinishReasonError → 合否が「変換品質」ではなく「評価実行失敗」で決まっている

- 対象yaml_file（6件）/ セクション（present_sections）:
  - `PLN-PLN-AIQUA-002.yaml`（ai_quality_requirements, traceability）
  - `PLN-PLN-CONS-002.yaml`（constraints, traceability）
  - `PLN-PLN-DES-002.yaml`（architecture, traceability）
  - `PLN-PLN-FLW-002.yaml`（workflow, traceability）
  - `PLN-PLN-GOAL-002.yaml`（goal, traceability）
  - `PLN-PLN-PROB-002.yaml`（problem, traceability）

- 何が起きているか:
  - 上記6件はいずれも `details[].tr_success=false` で Fail 判定。
  - Fail の直接原因は `Faithfulness` が `score:null` かつ `error: LengthFinishReasonError` となっていること。
  - つまり **MD↔YAMLの欠落/矛盾が検出された結果のFailではなく、Faithfulnessの評価応答が長すぎてパース不能になったFail** です。

- 根拠（DeepEval出力JSON）:
  - 例: `details[yaml_file="PLN-PLN-AIQUA-002.yaml"].metrics[name="Faithfulness"].error`
    - `LengthFinishReasonError: Could not parse response content as the length limit was reached ... completion_tokens=32768 ...`
  - 同型の `error` が上記6件に存在。

- 修正案（まず「評価が完走する」状態へ）:
  - g4_deepeval.py 側: Faithfulness の **include_reason を抑制**、または Run-1では **FaithfulnessをOFF** にし、GEval（CONSIST中心）を主判定にする（後述「5. スクリプト改善提案」）。
  - 参照（MD）を「全文」ではなく、各YAMLの `present_sections` に応じて **該当章だけ抜粋**して渡す（現状は `build_test_case()` で先頭12000文字カットのみ）。

---

### HP-2: GEvalの判定JSONが出力されず `geval_json=null` のまま → 「どのyaml_fileのどのセクションが原因か」を説明不能

- 対象yaml_file: evaluated=11 の全件
- セクション: 全般

- 何が欠けているか:
  - レポート目的に必須の「項目別判定（YES/NO/HOLD/SKIP）」「根拠（MD引用/要約）」が、JSONとして残っていません。
  - g4_deepeval.py は `metrics[name="参照↔YAML突合（チェックリスト準拠）"].reason` を `safe_parse_json()` でパースして `details[].geval_json` に格納する設計ですが、今回のRunでは `details[].geval_json` が全件 `null` です。

- 根拠:
  - DeepEval出力JSON: `details[].geval_json == null`
  - DeepEval出力JSON: `details[].metrics[name="参照↔YAML突合（チェックリスト準拠） [GEval]"].reason` が、指定のJSONフォーマットではなく英語説明文になっている（例: “The evaluation steps require checking for applicable checklist items ...”）。

- 修正案:
  - g4_deepeval.py 側: **GEvalの出力がJSONでない場合は失敗として扱う**（Fail寄せ）か、少なくとも `geval_json_raw` として退避して追跡可能にする。
  - 併せて、GEval criteria の「JSONだけを出力」の拘束を強める（後述「5」）。

---

### HP-3: CHK-PLN-CONSIST-001（CONSISTルール）が Run-1 の評価軸として機能していない（実質「適用項目なし→SKIP」）

- 対象yaml_file: evaluated=11 の全件
- セクション: 全般

- 何が起きているか:
  - Run-1のチェックリスト入力は `CHK-PLN-CONSIST-001.yaml` です（根拠: `meta.checklists[0]`）。
  - しかし g4_deepeval.py の「適用チェック項目一覧」は主に `items` 形式（AIDDチェックリスト）を想定しており、`CHK-PLN-CONSIST-001.yaml` の `rules` はテキスト化されて INPUT に混ざるだけです（`summarize_consist_checklist()`）。
  - 実際のGEvalの `reason` は「適用項目なし→SKIP」を前提に満点（1.0）になっており、**CONSISTのルール違反（必須キー欠落等）を検出できていない**状態です。

- 根拠:
  - チェックリスト: `packs/checklists/CHK-PLN-CONSIST-001.yaml` は `checklist.rules[]` で構成
  - DeepEval出力JSON: 多数の `metrics[name="参照↔YAML突合（チェックリスト準拠） [GEval]"].reason` が
    - “no applicable checklist items ... treat all as SKIP”
      を明示

- 修正案:
  - Run-1（pln_transform）では、CONSIST `rules` を **ChecklistItem（item_id=rule_id）に変換**し、GEvalに「rule_id単位でYES/NO/HOLD」を返させる。
  - もしくは、`CHK-PLN-CONSIST-001` の内容（存在確認/必須キー/ TODO禁止等）は **LLMではなく静的検査**に寄せ、Run-1の主目的（欠落/矛盾検出）を確実に成立させる。

---

## 4. 中程度問題（Medium Priority）

### MP-1: `summary.metric_averages` が「評価失敗（null + error）」を反映せず、Runの健康状態が読み取れない

- 対象: `summary.metric_averages`
- 問題:
  - `Faithfulness` 平均が 1.0 だが、実際は6件で `score:null` + `error: LengthFinishReasonError`。
  - Runの成立性（評価が完走しているか）をサマリだけでは判断できません。
- 根拠:
  - `summary.metric_averages.Faithfulness == 1.0`
  - `details[].metrics[name="Faithfulness"].score == null` が6件
- 対応案:
  - サマリに `metric_error_counts`（例: Faithfulness error 6件）/ `null_score_counts` を併記する。

---

### MP-2: `CHK-PLN-CONSIST-001` のルールが v2（\*-002.yaml）構成と噛み合っていない可能性があり、Run-1の目的に対して評価対象がズレる

- 対象: `packs/checklists/CHK-PLN-CONSIST-001.yaml` と、今回評価したYAML群（`details[].yaml_file`）
- 問題:
  - チェックリストの必須ルールは `PLN-PLN-GOAL-001.yaml` / `PLN-PLN-SCOPE-001.yaml` を名指し（例: `PLN-CONS-100`, `PLN-CONS-110`）。
  - 一方、今回の評価対象はすべて `*-002.yaml`（根拠: `details[].yaml_file` 一覧）。
  - この状態だと、Run-1の「欠落/矛盾/誤変換の特定」に直結する必須ルールが、評価対象ファイル名の不一致で適用されない（あるいは判定不能）リスクがあります。
- 根拠:
  - チェックリスト: `PLN-CONS-100` / `PLN-CONS-110` のtitle
  - DeepEval出力JSON: `details[].yaml_file` が `PLN-PLN-*-002.yaml` のみ
- 対応案:
  - Run-1（v2）用に、チェックリストの名指し対象を v2（\*-002）へ更新、または v1/v2 を両対応できるルールへ変更（例: GOAL-001|GOAL-002 の両許容）。

---

## 5. スクリプト改善提案（runner/gates/g4_deepeval.py）

### 5.1 今回の結果が正しく集計できているか

結論: **正しく集計できていません**。

- Run-1のFail要因の大半が `Faithfulness` の LengthFinishReasonError で、変換品質ではなく「評価失敗」です（HP-1）。
- さらに `geval_json` が残らないため、どのYAMLのどのセクションが原因か追跡できません（HP-2）。
- `CHK-PLN-CONSIST-001`（rules）が評価項目として扱われておらず、Run-1の問い（欠落/矛盾/誤変換の特定）に答えられていません（HP-3）。

---

### 5.2 具体的な修正ポイント（関数名/変数名レベル）と最小パッチ案

#### (A) Run-1では Faithfulness をオプション化し、LengthFinishReasonError を根絶する

- 目的: 「まず完走させる」「変換品質の判定は GEval + CONSIST（静的/項目別）へ寄せる」
- 対象: `build_metrics()` / `main()`

疑似差分（例）:

```diff
@@
 FAITHFULNESS_THRESHOLD = 0.5
@@
 def build_metrics(enable_faithfulness: bool) -> List[Any]:
@@
-    if enable_faithfulness:
-        metrics.append(FaithfulnessMetric(threshold=FAITHFULNESS_THRESHOLD, include_reason=True))
+    if enable_faithfulness:
+        # LengthFinishReasonError 回避（まず評価成立を優先）
+        metrics.append(FaithfulnessMetric(threshold=FAITHFULNESS_THRESHOLD, include_reason=False))
@@
 def main(...):
-    metrics = build_metrics(enable_faithfulness=True)
+    enable_faith = os.getenv("AIDD_ENABLE_FAITHFULNESS", "0") == "1"
+    metrics = build_metrics(enable_faithfulness=enable_faith)
```

根拠:

- `details[].metrics[name="Faithfulness"].error` が LengthFinishReasonError（HP-1）

---

#### (B) CONSIST `rules` を「評価項目化」して GEval が rule_id 単位の判定JSONを返せるようにする

- 目的: Run-1の目的（欠落/矛盾/誤変換の特定）に対し、**どのrule_idがNOになったか**を JSON で残す
- 対象: `summarize_consist_checklist()` / `load_checklists()` / `format_applicable_items_for_prompt()`

方針:

- `CHK-PLN-CONSIST-001.yaml` の `checklist.rules[]` を `ChecklistItem(item_id=rule_id, title=title, risk=severity相当)` に変換し、`aidd_items` に合流させる。

疑似差分（概念）:

```diff
@@
 def load_checklists(paths: List[Path]) -> Tuple[str, str, List[ChecklistItem]]:
@@
     for p in paths:
         chk = load_yaml_safe(p)
         ctext = summarize_consist_checklist(chk)
         if ctext:
             consist_texts.append(ctext)
+
+        # NEW: CONSIST rules を評価項目化
+        consist_items.extend(parse_consist_rules_as_items(chk))
@@
-    return consist_rules_text, aidd_summary, aidd_items
+    return consist_rules_text, aidd_summary, (aidd_items + consist_items)
```

根拠:

- `CHK-PLN-CONSIST-001.yaml` は rules 形式
- GEval `reason` が「適用項目なし→SKIP」になり、実質評価されていない（HP-3）

---

#### (C) GEvalの「JSONのみ出力」違反を検知し、追跡可能な形で保存/失敗扱いにする

- 目的: `details[].geval_json` を必ず残し、「どの項目がNGか」を追跡可能にする
- 対象: `safe_parse_json()` / `main()` の `parsed = safe_parse_json(ge_reason)` 周辺

疑似差分（例）:

```diff
@@
 parsed = safe_parse_json(ge_reason) if isinstance(ge_reason, str) else None
+if parsed is None and isinstance(ge_reason, str):
+    # 追跡不能を防ぐ（最低限 raw を残す）
+    parsed = {
+        "parse_error": True,
+        "raw_reason": ge_reason[:2000],
+    }
```

根拠:

- `details[].geval_json == null` が全件（HP-2）

---

## 6. 次アクション

### ① YAML修正の順番（どれから直すか）

Run-1（pln_transform）の目的に対し、まず「評価が成立し、原因追跡できる」状態を作るのが先決です。

1. **g4_deepeval.py を修正**し、Faithfulness LengthFinishReasonError を止める（HP-1）
2. **CONSIST rules を項目別判定として出力**できるようにし、`geval_json` を必ず残す（HP-2/HP-3）
3. チェックリスト（`CHK-PLN-CONSIST-001`）と評価対象（\*-002.yaml）の整合を取り、Run-1で必須ルールが実際に適用される状態にする（MP-2）

### ② 再実行の条件（どのRunを回すか）

- Run-1（pln_transform）を再実行
  - 条件:
    - `details[].metrics[name="Faithfulness"].error` が 0 件（少なくとも LengthFinishReasonError が 0 件）
    - `details[].geval_json` が evaluated 全件で `null` ではない（項目別の結果が残る）

### ③ 合格基準（今回のRun-1での到達目標）

- まず到達すべき最低基準（評価基盤の成立）:
  - evaluated=11 がすべて「評価完走」し、`LengthFinishReasonError` が発生しない
  - `geval_json` が全件で追跡可能（rule_id / item_id 単位の YES/NO/HOLD/SKIP と evidence が存在）
- その上で、Run-1本来の基準（MD↔YAML変換品質の検出）:
  - `CHK-PLN-CONSIST-001.yaml` のルール違反がある場合、どの `yaml_file` のどのセクションが原因かを `geval_json.results[]` で指摘できること
