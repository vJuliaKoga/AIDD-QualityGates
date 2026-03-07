---
meta:
  artifact_id: RES-PLN-TRANS-001
  file: RES-PLN-TRANS-001.md
  author: gpt-5.2
  source_type: ai
  source: Cline
  prompt_id: PRM-PLN-TRANS-001
  timestamp: "2026-03-05T09:12:00+09:00"
  model: gpt-5.2
  content_hash: 5a88a0d0b5c9fed011001a4532e8ada3e1bf68145dbec6da1f54a2622bf87760
---

# 1. 実行サマリ

- run名: **pln_transform**
- 参照モード: **MD**（DeepEval出力では `ref_mode: AUTO` だが、参照ファイルはMDのみ）
- 評価対象: **artifacts\planning\yaml\PLN-PLN-FLW-003**
- テストケース数 / 合格率 / メトリクス平均（JSON転記）
  - total **18** / passed **1** / failed **17**（overall: **fail**）
  - Faithfulness（ファイル単位）: **0/16 pass**, avg_score **0.1125**（warning: true）
  - Coverage（GLOBAL）: **0/1 pass**, avg_score **0.675**（status warn、covered_items=54/80）
  - Consistency（GLOBAL）: **1/1 pass**, avg_score **0.7812**（contradictions=24）

- 出力JSONファイルへの相対パス: **0303_1730.json**

---

# 2. 全体所見（結論を3〜6行）

1. **企画MD→YAML変換の“忠実な写経”を超えて、YAML側に仕様の補完・推測（=参照にない断定/閾値/運用ルール追加）が混入**しており、Faithfulnessが壊滅的に低い。
2. 一方で **Consistencyは「パス」だが、検出されたcontradictions=24の大半は“分割YAMLとして当然異なるべきフィールド”を機械的に衝突扱いしており、観測値がノイズ化**している。
3. Coverage 0.675（54/80）は「抜け」だけでなく、**見出し/箇条書き抽出とJaccard類似の設計により“存在するのに未カバー扱い”が混じる**。

---

# 3. 重大問題（High Priority）

## HP-1: Gate仕様（G1/G2/G3/G4/G5/PF）に“参照にない閾値・条件”が追加されている

- 対象yaml_file: **PLN-PLN-DES-002.yaml**
- どのセクション: `inspection_design.gates[*].warning_condition / pass_condition / outputs.fields` など
- 何が欠けている／矛盾している／誤っているか:
  - 例）G1に **warning_condition「5〜10件」/ pass_condition「5件未満」** が明記されているが、企画MD側で明示されている“致命条件”は「10件超」まで（少なくとも、5〜10や5未満の運用条件は本文で明記されていない）。
  - 例）各ゲート出力の `fields` が詳細化されている（G1: detected_terms など）が、MDで明記されているのは「ゲート別JSON＋サマリ（exitcode含む）」等の粒度で、ゲート別のフィールド詳細は本文からは確定できない。

- 根拠:
  - MD該当箇所（要約）: **Gate一覧と“即時失格条件（例: G1=10件超、G4=0.6未満）”は明記**されている一方、G1のwarning帯やpass帯の具体閾値までは本文に確定情報がない。
  - DeepEval判定理由: Faithfulnessが **PLN-PLN-DES-002.yaml で fail（score=0.1163）**。ただし `reason` が空で、どの主張が参照外か追跡不能。

- 修正案（YAML側の追記/修正案）
  - **参照MDに存在しない“閾値・条件・フィールド定義”を削除**し、MDに書いてある粒度へ戻す（例: G1は「10件超がFatal」まで）。
  - どうしても補足を残すなら、`exceptions` の方針に合わせて **「AIによる提案」枠を別キーで明示**（本文扱いにしない）し、Faithfulness対象外にする設計へ寄せる（現状は混在）。

---

## HP-2: リスクレベル運用に“参照にないデフォルト規則”が混入

- 対象yaml_file: **PLN-PLN-DES-006.yaml**
- どのセクション: `score_policy.risk_level_declaration.default`
- 何が欠けている／矛盾している／誤っているか:
  - YAMLには **「宣言なしの場合は HIGH を適用（安全側フォールバック）」** が書かれているが、企画MD側の「可変リスクレベル別・合格閾値」では LOW/HIGH の閾値提示が中心で、**“未宣言時のデフォルト”は本文に確定情報として記載されていない**。

- 根拠:
  - MD該当箇所（要約）: **LOW Risk 70点以上 / HIGH Risk 90点以上** の提示。デフォルト適用規則の明記は確認できない。
  - DeepEval判定理由: Faithfulnessが **PLN-PLN-DES-006.yaml で fail（score=0.0）**、reason空。

- 修正案
  - `risk_level_declaration.default` を **削除**（または「未確定/TBD」扱いに落とす）。
  - MD本文にデフォルト方針を入れたい場合は、先にMDへ追記してからYAMLへ反映（本Runは「MD→YAML忠実変換」なので逆流はNG）。

---

## HP-3: 企画YAML化方針（PLNパックQA観点）に“チェック方法/合格基準/例”が過剰に具体化されている

- 対象yaml_file: **PLN-PLN-YAML-001.yaml**
- どのセクション: `inspection_design.pln_pack_mandatory_qa[*].check_method / pass_criterion / fail_example / pass_example`
- 何が欠けている／矛盾している／誤っているか:
  - MD（8.1）で“必須にするQA観点（3つ）”は挙げられているが、YAML側は **チェック方法（G1+G4等）・合格基準（数値/閾値/条件）・fail/pass例** を断定しており、本文の確定情報を超えている。

- 根拠:
  - MD該当箇所（要約）: PLNパックに **検証可能性/スコープ/リスク運用** を標準装備する旨と、PLN-ID付与→derivedfrom接続方針の説明。個々の“チェック方法の割当”や“合格基準の数値化”は本文の確定情報としては不足。
  - DeepEval判定理由: Faithfulnessが **PLN-PLN-YAML-001.yaml で fail（score=0.0）**、reason空。

- 修正案
  - `pln_pack_mandatory_qa` は **MDの列挙に留める**（観点名と説明まで）。チェック方法や合格基準が本文に無いなら入れない。
  - 例や基準を残す場合は、同ファイルの `exceptions` に従い **“AIによる提案”として別枠キーへ分離**して、本文由来と混ぜない。

---

# 4. 中程度問題（Medium Priority）

## MP-1: Coverage（54/80）の“未カバー”に、存在するのに拾えていない項目が混在

- 対象yaml_file: **GLOBAL（ディレクトリ全体）**
- どのセクション: Coverage詳細 `details.coverage.items[*]`
- 何が欠けている／矛盾している／誤っているか:
  - Coverage抽出は「見出し/箇条書き」を論点として80件抽出しているが、例として **「1.1 現状の構造的問題」「1.2 社内で解くべき3課題」など“見出しそのもの”が未カバー扱い**になっている。分割YAMLは“見出し文字列の一致”を目的としていないため、ここでの減点は「欠落」ではなく「照合設計」の影響が大きい。

- 根拠:
  - JSON reason: `covered_items=54/80 (sim_th=0.25)`、未カバー項目に見出しが含まれている。

- 修正案
  - 見出しを論点に入れない運用（`AIDD_COVERAGE_SKIP_HEADINGS=1`）へ。
  - もしくは、見出しは `primary_section` など“メタの整合”で判定し、Coverage対象から除外。

---

## MP-2: Consistencyのcontradictions=24が“分割YAMLとして自然な差分”を大量に拾っている

- 対象yaml_file: **GLOBAL**
- どのセクション: Consistency詳細 `details.consistency.contradictions[*]`
- 何が欠けている／矛盾している／誤っているか:
  - `rationale / ssot_note / primary_section / traceability.source_document` 等が「path_value_conflict」として列挙されているが、これらは **ファイルごとに異なるのが正**（=矛盾ではない）。

- 根拠:
  - contradictions例に `path: rationale` や `path: ssot_note` が含まれる。

- 修正案
  - `AIDD_CONSISTENCY_IGNORE_KEYS` に `rationale, ssot_note, primary_section, traceability.source_document, referenced_internal_ids` 等を追加し、**“比較して意味のあるキー”だけに絞る**。

---

## MP-3: Faithfulnessのreasonが空で、どこが参照外か追跡不能（評価レポートとして不適）

- 対象yaml_file: **全Faithfulnessケース（16件）**
- どのセクション: `results[*].reason`
- 何が欠けている／矛盾している／誤っているか:
  - failでもreasonが空のため、**「どのyaml_fileのどのセクションが原因か？」にDeepEval結果から答えられない**。

- 根拠:
  - JSONのFaithfulness結果で `reason": ""` が継続している。

- 修正案
  - スクリプト側で `include_reason=True` を許可し、最低限の根拠（抽出されたtruthsや不一致箇所）を出す。

---

# 5. スクリプト改善提案（g4_deepeval.py）

## 5.1 今回の結果が正しく集計できているか

- Faithfulnessが全滅に近い一方、YAMLの多くはMDの内容を含んでいるため、**「参照にない“補完/推測”が混ざっている」こと自体は妥当な検出**になり得る。
- ただし、**reasonが空**なので「誤って減点していないか」の検証ができず、ゲートとして運用不可能に近い。

## 5.2 不要観点で減点していないか（Consistency / Coverage）

- Consistencyは、分割YAMLとして当然異なる `rationale` 等を矛盾扱いしており、**“矛盾数”がノイズ**。スコア自体はpassでも、Allure表示や解釈を誤らせる。
- Coverageは見出しを論点に採用しており、**「見出し文字列がYAMLに無い＝欠落」扱い**になりやすい。目的（MD→YAML写経の欠落検知）からズレる。

## 5.3 timeout要因（今回観測あり）

- `PLN-PLN-DES-004.yaml` は `retried: true` かつ `first_error: TimeoutError` が記録されている。
- 参照チャンク選択やctx長の調整は入っているが、**一部ファイルで依然タイムアウトが出ている**。

## 5.4 具体的な修正ポイント（最小パッチ案）

### (A) Faithfulnessの `reason` を出す（最優先）

- 修正ポイント: `build_faith_metric()` の `include_reason` を True に（もしくは envで切替）

疑似差分：

```diff
 def build_faith_metric(truths_limit: int):
     base_kwargs = {
         "threshold": WARN_THRESHOLD,
         "model": EVAL_MODEL,
-        "include_reason": False,   # タイムアウト優先で理由は切る
+        "include_reason": True,    # 追跡可能性を優先（必要ならenvで切替）
         "async_mode": False,
     }
```

### (B) Consistencyの比較対象キーを絞る（ノイズ削減）

- 修正ポイント: `CONS_IGNORE_KEYS_RAW` のデフォルトを拡張（rationale等を無視）

疑似差分：

```diff
 CONS_IGNORE_KEYS_RAW = os.environ.get(
     "AIDD_CONSISTENCY_IGNORE_KEYS",
-    "meta.,timestamp,updated_at,created_at,hash,checksum"
+    "meta.,timestamp,updated_at,created_at,hash,checksum,"
+    "rationale,ssot_note,primary_section,traceability.source_document,referenced_internal_ids"
 ).strip()
```

### (C) Coverageで見出しをデフォルト除外（欠落検知の精度を上げる）

- 修正ポイント: `COV_SKIP_HEADINGS` の既定値を1へ（またはENVで運用固定）

疑似差分：

```diff
-COV_SKIP_HEADINGS = os.environ.get("AIDD_COVERAGE_SKIP_HEADINGS", "0").lower() in ("1", "true", "yes")
+COV_SKIP_HEADINGS = os.environ.get("AIDD_COVERAGE_SKIP_HEADINGS", "1").lower() in ("1", "true", "yes")
```

---

# 6. 次アクション

## ① YAML修正の順番（どれから直すか）

1. **PLN-PLN-DES-002.yaml**：参照にない閾値・条件・出力フィールド詳細の追加を除去（HP-1）
2. **PLN-PLN-DES-006.yaml**：未宣言デフォルト等、本文にない運用規則の削除（HP-2）
3. **PLN-PLN-YAML-001.yaml**：3観点の列挙に戻し、チェック方法/基準/例の断定を落とす（HP-3）

## ② 再実行の条件（どのRunを回すか）

- **Run-1（pln_transform）を再実行**（MD参照のまま）。
- 併せて、g4_deepeval.pyを最小パッチで修正し、**Faithfulness reasonが出る状態**で同じRun-1を回す（「誤減点」検証の前提）。

## ③ 合格基準（今回のRun-1での到達目標）

- Faithfulness: **16件中 12件以上 pass**（まず“参照外の断定混入”を止める）
- Coverage: **0.70以上（=warning解除）** を目標（見出し除外などの設定改善後に評価）
- Consistency: スコアよりも、**contradictionsが“意味のあるキーだけ”に縮退していること**（ノイズ除去後に再確認）
