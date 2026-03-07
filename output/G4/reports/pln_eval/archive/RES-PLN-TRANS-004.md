---
meta:
  artifact_id: RES-PLN-TRANS-004
  file: RES-PLN-TRANS-004.md
  author: gpt-5.2
  source_type: ai
  source: Cline
  prompt_id: PRM-PLN-TRANS-001
  timestamp: "2026-03-02T18:45:00+09:00"
  model: gpt-5.2
  content_hash: 256e609d19ae688d81346cae36fe9529c22a9620cc4d306640d831656b8a6a84
---

# RES-PLN-TRANS-004 — G4(pln_transform) 評価レポート（Run-1）

---

## 1. 実行サマリ

- run名: **pln_transform**
- 参照モード: **MD**
  - 根拠: DeepEval出力JSON `inputs.ref_files` が `artifacts\planning\PLN-PLN-FLW-003.md`（拡張子 .md）で、`runner/gates/g4_deepeval.py` の `infer_ref_mode_by_ext()` によりMD扱い
  - 参考: JSON上の `inputs.ref_mode` は `AUTO`
- 評価対象: **`artifacts\planning\yaml\PLN-PLN-FLW-003`**
- テストケース数 / 合格率 / メトリクス平均（JSON転記）
  - total: **18**
  - passed: **1** / failed: **17**
  - 合格率: **5.56% (1/18)**
  - faithfulness: **avg=0.0254**（passed 0/16）
  - coverage: **avg=0.6750**（passed 0/1）
  - consistency: **avg=0.7776**（passed 1/1）
- 出力JSON（最新Run-1）: `output\G4\pln_transform\artifacts_planning_yaml_PLN-PLN-FLW-003\0303_1623.json`

---

## 2. 全体所見（結論）

1. **Faithfulness が全ファイルほぼ壊滅（avg=0.0254）だが、判定理由（reason）が空**で、どこで「創作」判定されたか追えない（JSON `results[].reason == ""`）。
2. YAML自体にはMD由来の内容が多く入っている一方で、**MDに無い具体例・適用ケース・将来拡張案が混入**している箇所があり、変換要件（欠落なく・矛盾なく・誤言い換えなく）を満たさない。
3. Coverage（54/80）とConsistency（contradictions=28）は、**抽出・比較ロジック由来の誤検出/誤減点が混ざっている**（見出しを「論点」として扱う／`meta.*` を矛盾として数える等）。

---

## 3. 重大問題（High Priority）

### HP-1: `PLN-PLN-DES-006.yaml` に MD に無い「適用ケース/例/中間リスク」等が混入

- 対象yaml_file: `artifacts\planning\yaml\PLN-PLN-FLW-003\PLN-PLN-DES-006.yaml`
- どのセクション: `score_policy.risk_levels.levels[]` / `score_policy.future_extension`
- 何が誤っているか（創作）:
  - `applicable_cases` に **MD 8.5 に存在しない具体ドメイン例**が含まれる
    - YAML: `applicable_cases` に「金融・医療等のリスク感度が高いドメイン」等
  - `examples` に **MDに無い点数例**が含まれる（「G1 曖昧語が 7 件 → 減点（-3点）だが通過」など）
  - `future_extension` に **MDに無い MEDIUM Risk（80点）** が追加されている
- 根拠:
  - MD該当箇所（8.5）: MD `## 8.5` には「LOW Risk: 70点以上 / HIGH Risk: 90点以上」と運用指針の表のみ（適用ケース例や80点の中間レベルの記載なし）
  - DeepEval側の判定根拠:
    - JSON `results[]` 該当: `Faithfulness :: PLN-PLN-DES-006.yaml` が **score=0.0 / passed=false**（ただし `reason` は空）
      - 出力JSON: `results[?test_name=="Faithfulness :: PLN-PLN-DES-006.yaml"]`
- 修正案（YAML側）:
  - `score_policy.risk_levels.levels[].applicable_cases` は **MDに記載がある範囲に限定**し、MDに無い具体ドメイン例は削除
  - `score_policy.risk_levels.levels[].examples` は **MDに無い数値例なら削除**（必要ならMD側に追記した上で再生成）
  - `score_policy.future_extension`（MEDIUM Risk 80点等）は **削除**、または `inspection_design.exceptions`（PLN-PLN-YAML-001 の例外方針）に合わせて「AIによる提案」枠として別キーに隔離し、本文由来と混在させない

---

### HP-2: `PLN-PLN-RUN-001.yaml` が MD 13.1 の範囲を超えて仕様を“作り込んでいる”

- 対象yaml_file: `artifacts\planning\yaml\PLN-PLN-FLW-003\PLN-PLN-RUN-001.yaml`
- どのセクション: `id_issuer.functions.items[]` / `id_issuer.data_files.*` / `id_issuer.usage_workflow`
- 何が誤っているか（創作/過剰具体化）:
  - MD 13.1 は「レジストリ読込→nextID発行→next_nnn更新→発行ログ追記→stdout出力」「single-user前提（ロックなし）」までだが、YAMLは
    - `error_condition`（自動新規登録は行わない等）
    - `retention: 全発行履歴を保持（削除禁止）`
    - `usage_workflow` の手順（キーが無い場合は手動追加してから実行 等）
    - `warning_conditions` の詳細
      など **MDに無い運用規約/仕様** を追加している。
- 根拠:
  - MD該当箇所（13.1）引用要約:
    - 「issue_id.py は以下を行う：レジストリ読込・next_nnn更新・発行ログ追記・stdoutへ発行ID出力」
    - 「single-user前提（ロックなし）」
  - DeepEval側の判定根拠:
    - JSON `Faithfulness :: PLN-PLN-RUN-001.yaml` が **score=0.0 / passed=false**（ただし `reason` 空）
- 修正案（YAML側）:
  - `id_issuer` 配下は **MDで列挙されている4機能と single-user 前提**に限定（新規に決めた運用規約は入れない）
  - どうしても必要な運用規約は、MD側（13章）に追記してSSOTをMDへ戻してから再変換

---

### HP-3: 付録A（planning_id.yaml）の内容が YAML分割成果物として未反映（欠落）

- 対象yaml_file: （欠落）
  - 評価対象ディレクトリ `artifacts\planning\yaml\PLN-PLN-FLW-003` に、MD「付録A：本企画のID定義（planning_id.yaml）」に相当するファイルが存在しない（`list_files` 結果16ファイルのみ）
- どのセクション: MD「付録A：本企画のID定義（planning_id.yaml）」
- 何が欠けているか:
  - MDには `planning_ids:` として、各IDの `maps_to_sections` を持つ「企画ID台帳」が掲載されているが、YAML群には同等の台帳（ID→セクション対応）がない。
- 根拠:
  - MD該当箇所: `## 付録A：本企画のID定義（planning_id.yaml）` 以下の YAMLスニペット
  - DeepEval側: Coverage詳細 `details.coverage.items[]` は “ref_items_count=80” のうち **26件が未カバー**（`covered_items=54/80`）
    - 出力JSON: `details.coverage.ref_items_count=80`, `details.coverage.covered_count=54`
- 修正案（YAML側）:
  - 付録Aの YAMLスニペットを、そのまま **分割YAMLとして追加**（例: `PLN-PLN-TBL-001.yaml` 等）
  - `artifact_id` は MDのID規約に従い `issue_id.py` で新規発行し、台帳ファイルとして `artifact_kind` を明示
  - 既存YAML（Goal/Problem/Scope...）から当該台帳への `referenced_internal_ids` を追加し、SSOTを明確化

---

## 4. 中程度問題（Medium Priority）

### MP-1: Coverage の未カバーに「見出し（構造ラベル）」が多数混入し、欠落検出が不安定

- 対象yaml_file: `GLOBAL（集合評価）`
- セクション: `details.coverage.items[]`
- 内容:
  - 未カバー例（JSONより）:
    - `item="1.1 現状の構造的問題"` が `covered=false / best_sim=0.0`
    - `item="1.2 社内で解くべき3課題（導入視点）"` が `covered=false / best_sim=0.0`
  - ただし YAML側には内容（箇条書きの具体項目）が `PLN-PLN-PROB-001.yaml` に存在するため、
    **見出し文言そのものが無いだけで「内容欠落」とは言い切れない**。
- 根拠:
  - JSON: `details.coverage.items` の該当行
  - YAML: `PLN-PLN-PROB-001.yaml` の `problem.structural_problems.items[]` に 1.1 の内容が存在
- 修正案:
  - YAML側で「見出し文字列」まで合わせるより、**Coverage抽出側が見出しを論点に含めない**方が安定（→ スクリプト改善提案へ）

---

### MP-2: Consistency の contradictions=28 は大半が `meta.*` 等の“当然異なる値”で、矛盾としての有用性が低い

- 対象yaml_file: `GLOBAL（横断評価）`
- セクション: `details.consistency.contradictions[]`
- 内容:
  - `type=path_value_conflict` として
    - `path="meta.artifact_id"`（各ファイルで異なるのが正常）
    - `path="meta.file"`（同上）
    - `path="meta.model"`（DES-003のみ `claude-sonnet-4-6`）
      などが矛盾扱いされている。
- 根拠:
  - JSON: `details.consistency.contradictions` の上記エントリ
- 修正案:
  - `meta.*` / `content_hash` / `timestamp` / `model` などを **デフォルト ignore** に入れ、
    本当に矛盾扱いしたいドメイン値（閾値、責務、条件など）にフォーカスさせる（→ スクリプト改善提案へ）

---

### MP-3: Faithfulness の判定理由が空で、誤変換箇所特定に使えない

- 対象yaml_file: 全ファイル
- セクション: JSON `results[].reason`
- 内容:
  - `Faithfulness :: *.yaml` の `reason` が全て空（少なくとも本JSONでは空）
- 根拠:
  - JSON: `results[0..15].reason == ""`
- 修正案:
  - `g4_deepeval.py` で `include_reason=True` にし、`metric.reason` をJSONへ格納（→ スクリプト改善提案へ）

---

## 5. スクリプト改善提案（runner\gates\g4_deepeval.py）

### 5.1 今回の結果が正しく集計できているか（結論）

- **Faithfulness は「集計」はできているが、トリアージ不能**（reason未出力）。
- **Consistency は `meta.*` を矛盾扱いしており、contradictions数がノイズ優勢**。
- **Coverage は “見出し” を論点として抽出**しており、内容が入っていても未カバーになりうる。

### 5.2 不要観点で減点していないか

- Faithfulness で `actual_output` に YAML全文（`meta.*` 含む）を渡しているため、
  **MDに存在しない `meta.content_hash` 等が「創作」扱いされやすい**。
  - 根拠（コード）: `eval_one_faithfulness()` が `actual_output=truncate(yaml_content, ...)`（YAML本文をそのまま渡す）

### 5.3 timeout/長時間化要因

- `FAITH_ACTUAL_MAX` / `FAITH_CTX_MAX` が 0 の場合「無制限」になり、参照blob（MD全文）＋YAML全文をそのまま投げる。
  - 本Runでは `Faithfulness :: PLN-PLN-FLW-001.yaml` の `duration_ms=495610` 等、極端に長いケースがある（JSON `results[].duration_ms`）。

### 5.4 最小パッチ案（疑似差分）

#### (A) Faithfulness: reason出力 + meta除外 + デフォルトtruncate

```diff
--- a/runner/gates/g4_deepeval.py
+++ b/runner/gates/g4_deepeval.py
@@
-FAITH_ACTUAL_MAX = int(os.environ.get("AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS", "0") or "0")
-FAITH_CTX_MAX = int(os.environ.get("AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS", "0") or "0")
+# 0 (=無制限) はタイムアウト/劣化要因になりやすいので、未指定時は安全側デフォルトを採用
+FAITH_ACTUAL_MAX = int(os.environ.get("AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS", "3500") or "3500")
+FAITH_CTX_MAX = int(os.environ.get("AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS", "4500") or "4500")
@@
 def build_faith_metric(truths_limit: int):
@@
-        "include_reason": False,
+        "include_reason": True,
@@
 def eval_one_faithfulness(...):
+    # meta 等、参照に無いことが前提のフィールドは Faithfulness 対象から除外
+    # （変換品質＝本文の忠実性を見たい）
+    try:
+        obj = yaml.safe_load(yaml_content) or {}
+        if isinstance(obj, dict) and "meta" in obj:
+            obj.pop("meta", None)
+        yaml_for_eval = yaml.dump(obj, allow_unicode=True, sort_keys=False)
+    except Exception:
+        yaml_for_eval = yaml_content
@@
-    tc = LLMTestCase(... actual_output=truncate(yaml_content, actual_max), ...)
+    tc = LLMTestCase(... actual_output=truncate(yaml_for_eval, actual_max), ...)
@@
     metric.measure(tc)
     score = float(metric.score)
     passed = bool(metric.is_successful())
-    return score, passed, ""
+    return score, passed, getattr(metric, "reason", "") or ""
```

#### (B) Consistency: デフォルトで meta.\* を無視

```diff
--- a/runner/gates/g4_deepeval.py
+++ b/runner/gates/g4_deepeval.py
@@
-CONS_IGNORE_KEYS_RAW = os.environ.get("AIDD_CONSISTENCY_IGNORE_KEYS", "").strip()
+CONS_IGNORE_KEYS_RAW = os.environ.get(
+  "AIDD_CONSISTENCY_IGNORE_KEYS",
+  "meta.,content_hash,timestamp,model,author,source_type,source,prompt_id,schema_version,derived_from,ssot_note,traceability."
+).strip()
```

#### (C) Coverage: 見出し抽出を弱め、表（|区切り）を論点抽出に含める

```diff
--- a/runner/gates/g4_deepeval.py
+++ b/runner/gates/g4_deepeval.py
@@
 def extract_reference_items(...):
@@
-        is_heading = bool(re.match(r"^#{1,6}\\s+", raw))
+        # 見出しは構造ラベルであり、内容欠落検出にはノイズになりやすいのでデフォルト除外
+        is_heading = False
+
+        # 表の行（| ... |）も論点として拾う（Gate一覧など）
+        is_table_row = raw.startswith("|") and raw.endswith("|") and not set(raw) <= set("|- :")
@@
-        if not (is_heading or is_bullet):
+        if not (is_bullet or is_table_row):
             continue
```

---

## 6. 次アクション

### ① YAML修正の順番（どれから直すか）

1. **`PLN-PLN-DES-006.yaml`**: MDに無い `applicable_cases/examples/future_extension` を削除（創作混入の除去）
2. **`PLN-PLN-RUN-001.yaml`**: MD 13.1 の列挙範囲に合わせて過剰仕様を削除
3. **付録A（planning_id.yaml）**: 台帳内容を分割YAMLとして追加（MDスニペットをSSOTとしてそのまま反映）

### ② 再実行の条件（どのRunを回すか）

- Run-1（pln_transform）を再実行
  - 条件A: YAML修正のみ反映したい場合 → 現行 `g4_deepeval.py` のまま再実行（ただし reason が空のままなので原因特定力は低い）
  - 条件B: **誤減点の切り分け**をしたい場合 → `g4_deepeval.py` のパッチ（5章）適用後に再実行（推奨）

### ③ 合格基準（今回のRun-1での到達目標）

- Faithfulness:
  - **reason が JSON に出力されること**（トリアージ可能化）
  - `PLN-PLN-DES-006.yaml` / `PLN-PLN-RUN-001.yaml` の創作除去後、少なくとも該当2ファイルのスコアが **0.70以上** を目標
- Coverage:
  - 見出し由来ノイズを除いた上で **0.70以上**（現状 0.675）
- Consistency:
  - `meta.*` 無視の上で contradictions が「設計値の不一致」中心になること（件数の目標は **0に近づける**）
