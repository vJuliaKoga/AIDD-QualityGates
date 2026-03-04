---
meta:
  artifact_id: RES-PLN-TRANS-003
  file: RES-PLN-TRANS-003.md
  author: gpt-5.2
  source_type: ai
  source: Cline
  prompt_id: PRM-PLN-TRANS-001
  timestamp: "2026-03-02T18:45:00+09:00"
  model: gpt-5.2
  content_hash: 88b3c108a16a21e6460d7fe8a257f57e0d4a550573a2667645f13c9013e4f3dc
---

# RES-PLN-TRANS-003（G4 / Run-1: pln_transform）評価レポート

> 対象: **企画MD ↔ 企画YAML 分割**の変換品質（欠落なく／矛盾なく／誤った言い換えなく）

本レポートの根拠は、**Run-1（最新）のDeepEval出力JSON** `output\G4\pln_transform\artifacts_planning_yaml_v3\0302_1139.json` と、同JSONが指す参照MD/評価対象YAML/チェックリスト/スクリプト（PRM-PLN-TRANS-001で指定）に限定します。

---

## 1. 実行サマリ

- run名: **pln_transform**
- 参照モード: **MD**
- 評価対象: `artifacts\planning\yaml\v3`（`inputs.yaml_dir`）
- テストケース数 / 合格率 / メトリクス平均（DeepEval出力JSONから転記）
  - total_test_cases: **21**（`summary.total`）
  - passed / failed: **19 / 2**（`summary.passed` / `summary.failed`）
  - pass_rate: **0.9048**（= 19/21）
  - metric_averages:
    - Faithfulness: **avg=0.8802**（`summary.faithfulness.avg_score`、total=11 / failed=1）
    - Checklist（CHK-PLN-CONSIST-001）: **avg=0.9000**（`summary.checklist.avg_score`、total=10 / failed=1）
- 出力JSONファイル: `output\G4\pln_transform\artifacts_planning_yaml_v3\0302_1139.json`

---

## 2. 全体所見（結論を3〜6行）

1. Run-1のFailは **(a) Faithfulnessのタイムアウト（CONS YAML）** と **(b) Checklistのプレースホルダ検知の誤検知** の2点に集約され、現状は「変換品質そのもの」より「評価側の成立性」に強く依存しています（`results[].status=error/fail`）。
2. `PLN-PLN-CONS-002.yaml` は、参照MD（PLN-PLN-FLW-002.md）に明示のない外部参照（例: `shadow.md`）を含み得る構造になっており、**誤変換（根拠のない追加）を見逃すリスク**があります（MD側に該当記述が存在しない）。
3. `PLN-PLN-TBL-002.yaml` はFaithfulnessが高スコアでPASSしていますが、MDに存在しない詳細（故障モード・機械チェック群など）を含む可能性があるため、**スクリプト側のFaithfulness入力設計（長大YAML/全文MD投入）**の見直しが必要です。

変換品質の最重要課題（上位3つ）:

- (1) **CONSのFaithfulnessがタイムアウトし、MD↔YAML忠実性が未検証のままFail**（評価実行失敗）
- (2) **ChecklistのPLN-CONS-060が誤検知し、内容として正しい記述（「TODO等を残さない」方針文）までFail扱い**
- (3) **MDに根拠のない参照・制約・検査詳細がYAMLに混入する（または混入しても検知されない）構造**

---

## 3. 重大問題（High Priority）

### HP-1: PLN-CONS-060（TODO/TBD/PENDING残存検知）が「プレースホルダ残存」ではなく「用語の言及」まで誤検知してFail

- 対象yaml_file:
  - `artifacts\planning\yaml\v3\PLN-PLN-CONS-002.yaml`
  - `artifacts\planning\yaml\v3\PLN-PLN-TBL-002.yaml`
- どのセクション:
  - CONS: `constraints.quality_constraints.CON-QA-001.description`（ほか）
  - TBL: `inspection_design.mappings[].machine_checks[].method/pass_criteria`（ほか）
- 何が欠けている／矛盾している／誤っているか:
  - チェックリスト要件（`CHK-PLN-CONSIST-001.yaml` の `PLN-CONS-060`）は「**meta以外に TODO/TBD/PENDING が残っていない**」ですが、現状スクリプトは **文字列中の出現**も違反として扱っています（プレースホルダ値の残存とは別物）。
  - 結果として、YAMLが「TODO等を残さない」という**方針文として言及しているだけ**でもFailになります。
- 根拠:
  - Checklist（ルール定義）: `packs\checklists\CHK-PLN-CONSIST-001.yaml` の `rules[rule_id=PLN-CONS-060].title`
  - DeepEval判定理由（Run-1 JSON）:
    - `results[test_name="Checklist :: PLN-CONS-060"].status = "fail"`
    - `results[...].reason = "TODO/TBD/PENDING残存: PLN-PLN-CONS-002.yaml: {'TBD'} / PLN-PLN-TBL-002.yaml: {'TBD', 'PENDING', 'TODO'}"`
  - YAML実体（用語としての言及）:
    - `PLN-PLN-CONS-002.yaml` の `CON-QA-001.description` に **"TODO/TBD/PENDING"** が含まれる
    - `PLN-PLN-TBL-002.yaml` の `MC-PLN-NON-002.method/pass_criteria` に **"TODO" "TBD" "PENDING"** が含まれる
- 修正案（YAML側の追記/修正案）:
  - （暫定ワークアラウンド）`PLN-PLN-CONS-002.yaml` / `PLN-PLN-TBL-002.yaml` 内の説明文から、英字トークン **TODO/TBD/PENDING** の生文字列を除去し、例:
    - 「未確定プレースホルダ（例: TODO等）」→ **「未確定プレースホルダ語」** のように置換（※現スクリプトはIGNORECASEのため、英字を残すと再度誤検知）
  - （本質対応は後述「5」）スクリプト側で「値がTODO/TBD/PENDINGそのもの」の検知に限定する。

---

### HP-2: Faithfulness :: PLN-PLN-CONS-002.yaml が TimeoutError で評価不能（Run-1のFail要因）

- 対象yaml_file: `artifacts\planning\yaml\v3\PLN-PLN-CONS-002.yaml`
- どのセクション: `constraints`（ファイル全体がFaithfulness対象）
- 何が欠けている／矛盾している／誤っているか:
  - Run-1の主目的である「MD→YAMLの忠実性（誤った追加・言い換えの検知）」が、このファイルについて **未検証**の状態です。
  - Failは「変換品質の検出」ではなく「評価実行の失敗（タイムアウト）」で決まっています。
- 根拠:
  - DeepEval判定理由（Run-1 JSON）:
    - `results[test_name="Faithfulness :: PLN-PLN-CONS-002.yaml"].status = "error"`
    - `results[...].reason = "RetryError[<Future ... raised TimeoutError>]"`
    - `results[...].duration_ms = 977608`（約16分）
  - 参照元MD（制約が書かれている箇所）:
    - 「16. 配布形態（Phase 1はサーバー不要）」
    - 「11. トレーサビリティ設計（Core/Adapter）」
    - 「13. ID発行・管理（single-user前提）」
    - 「9. スコア運用ポリシー（0.70未満はWarning／スコアは唯一根拠にしない）」
- 修正案（YAML側の追記/修正案）:
  - `PLN-PLN-CONS-002.yaml` の制約を **参照MDに存在する制約へ限定**し、MDに根拠がない制約（外部参照や設定ファイル前提の詳細）を削除・別成果物へ分離する（結果としてYAMLが短くなり、Faithfulnessも完走しやすくなる）。
  - `derived_from` を、実際に記載根拠として使っているMD章（例: `#11-トレーサビリティ設計` / `#13-id発行・管理` / `#9-スコア運用ポリシー`）まで拡張し、参照の追跡可能性を上げる。

---

### HP-3: MDに根拠のない外部参照（例: shadow.md）をYAMLが含んでおり、「誤った追加（ハルシネーション）」の疑い（DeepEvalでも根拠が残らない）

- 対象yaml_file: `artifacts\planning\yaml\v3\PLN-PLN-CONS-002.yaml`
- どのセクション:
  - `constraints.ai_specific_constraints[*].derived_from`（例: `shadow.md#...`）
- 何が欠けている／矛盾している／誤っているか:
  - 参照MD（`artifacts\planning\PLN-PLN-FLW-002.md`）に存在しない参照（`shadow.md`）を根拠として制約が記載されており、Run-1の目的（MD→YAML変換の忠実性）から見て **誤変換（根拠のない追加）** の疑いが強い。
  - さらに、Faithfulnessは当該YAMLでタイムアウトしているため（HP-2）、自動評価としても検知できていません。
- 根拠:
  - YAML側:
    - `PLN-PLN-CONS-002.yaml` に `derived_from: shadow.md#...` が存在（例: `CON-AI-001/002/003/004`）
  - MD側:
    - `PLN-PLN-FLW-002.md` には `shadow.md` の言及が存在しない（全文内に該当文字列がない）
  - DeepEval側:
    - `results[Faithfulness :: PLN-PLN-CONS-002.yaml].status="error"` のため、Faithfulness判断理由が出せない（タイムアウト）
- 修正案（YAML側の追記/修正案）:
  - `constraints.ai_specific_constraints` を、参照MDに書かれている範囲（例: **「外部モデル送信可否は事前確認」**といったMD内の表現）に合わせて縮退し、MDに出ない前提（設定ファイル名、月次コスト上限、G3通過前提など）の記述を削除する。
  - どうしても必要な場合は、当該根拠を **参照MDへ追記してから** YAMLへ反映（本Run-1の「MD↔YAML整合」目的に合わせる）。

---

## 4. 中程度問題（Medium Priority）

### MP-1: `PLN-PLN-CONS-002.yaml` の運用制約に、MD上の表現だけでは確定できない「ゲート別のFail/Warning運用」が含まれる可能性

- 対象yaml_file: `artifacts\planning\yaml\v3\PLN-PLN-CONS-002.yaml`
- どのセクション: `constraints.operational_constraints.CON-OPS-003`（Gateごとの挙動記述）
- 何が欠けている／矛盾している／誤っているか:
  - MD側は「スコアは合否の唯一根拠にしない」「0.70未満はWarning」までを明記していますが（9章）、YAML側は「G4はWarningのみ」「G1はcritical_wordsでFail」など、**ゲート別のブロック条件**を詳細化しています。
  - これがMDに明記された方針（合否の最終判断は人）と整合しているかは、Run-1の範囲では断定できず、**言い換え/拡大解釈**になっているリスクがあります。
- 根拠:
  - MD（該当箇所）:
    - 「9. スコア運用ポリシー（スコアは合否の唯一根拠にしない／0.70未満はWarning）」
    - 「5. 基本思想（品質ゲートを満たさないものは次工程に進めない）」
  - DeepEval側:
    - 当該ファイルはFaithfulnessが `status=error` のため、整合性の自動判定が得られていない（HP-2と同根）
- 修正案（YAML側の追記/修正案）:
  - ゲート別挙動の断定を避け、MDで確実に言える範囲（例: 0.70未満はWarning、最終判断はCoach）に表現を戻す。

---

### MP-2: `derived_from` が実際の根拠章と対応していない（参照追跡が困難）

- 対象yaml_file: `artifacts\planning\yaml\v3\PLN-PLN-CONS-002.yaml`
- どのセクション: `meta/derived_from` と `constraints.*.derived_from_section/derived_from`
- 問題:
  - YAMLの `derived_from` は `#16-配布形態` のみですが、制約は11章・13章・9章を根拠とする項目を含んでいます（各項目に `derived_from_section` があり、分散している）。
  - 参照MD↔YAML整合の追跡がしづらく、レビュー・修正サイクルが遅くなります。
- 根拠:
  - YAML側: `derived_from: - ...#16-配布形態` のみ
  - MD側: 制約に相当する章が複数（11/13/9/5など）
- 修正案（YAML側の追記/修正案）:
  - `derived_from` に、当該YAMLで参照している章アンカーを追加（例: `...#11-トレーサビリティ設計`, `...#13-id発行・管理`, `...#9-スコア運用ポリシー`）。

---

## 5. スクリプト改善提案（runner/gates/g4_deepeval.py）

### 5.1 今回の結果が正しく集計できているか／不要観点で減点していないか／timeout要因

- 集計自体（pass/fail件数）はJSON上正しいものの、**Failのうち1件（Faithfulness）は評価実行失敗**であり、変換品質と直結していません（HP-2）。
- 不要観点での減点: `PLN-CONS-060` はプレースホルダ残存の意図に対して**語の言及までFail**にしており、不要減点です（HP-1）。
- timeout要因: `PLN-PLN-CONS-002.yaml` が長大であること、かつ `actual_output=yaml_content`（全文）をFaithfulnessに渡していることが、タイムアウト要因になっている可能性が高いです（`duration_ms=977608`）。

### 5.2 具体的な修正ポイント（関数名/変数名レベル）と最小パッチ案（疑似差分OK）

#### (A) PLN-CONS-060: 文字列ヒットではなく「値がTODO/TBD/PENDINGそのもの」の検出に変更（誤検知防止）

- 対象: `check_rule()` → `if rule_id == "PLN-CONS-060": ...`
- 現状: `_non_meta_yaml_str()` でYAML全体を文字列化 → `_TODO_PATTERN.findall()` で単語出現を検知
- 問題: 方針文（"TODO/TBD/PENDINGを残さない"）も違反扱い

最小パッチ案（概念）:

```diff
@@
 _TODO_PATTERN       = re.compile(r'\b(TODO|TBD|PENDING)\b', re.IGNORECASE)

+def _find_placeholder_values(obj):
+    """meta以外に、値が TODO/TBD/PENDING そのもののスカラーが存在するか検知"""
+    if isinstance(obj, str):
+        return {obj.upper()} if obj.upper() in ("TODO", "TBD", "PENDING") else set()
+    if isinstance(obj, list):
+        s = set()
+        for v in obj:
+            s |= _find_placeholder_values(v)
+        return s
+    if isinstance(obj, dict):
+        s = set()
+        for k, v in obj.items():
+            if k == "meta":
+                continue
+            s |= _find_placeholder_values(v)
+        return s
+    return set()
@@
         if rule_id == "PLN-CONS-060":
             violations = []
             for fp, info in yaml_files.items():
-                non_meta = _non_meta_yaml_str(info["data"])
-                found = set(_TODO_PATTERN.findall(non_meta))
+                found = _find_placeholder_values(info["data"])
                 if found:
                     violations.append(f"{Path(fp).name}: {found}")
```

#### (B) Faithfulnessタイムアウト対策: 長大YAMLをそのままLLM入力にしない（要約/チャンク/上限）

- 対象: `eval_faithfulness()` の `yaml_content` をそのまま `actual_output` に渡している箇所
- 最小パッチ案（概念）:

```diff
@@
         yaml_content = info["content"]
+        # タイムアウト回避: まずは上限をかける（Run-1の成立性優先）
+        MAX_CHARS = int(os.getenv("AIDD_G4_MAX_YAML_CHARS", "20000"))
+        if len(yaml_content) > MAX_CHARS:
+            yaml_content = yaml_content[:MAX_CHARS] + "\n\n# [TRUNCATED]"
@@
             test_case = LLMTestCase(
                 ...
                 actual_output=yaml_content,
                 retrieval_context=[md_content],
             )
```

（補足）Run-1の目的が「欠落/矛盾/誤変換の特定」である以上、将来的には `derived_from` の章だけMDを抜粋して `retrieval_context` を小さくする方が望ましいですが、上記は最小修正としての提案です。

---

## 6. 次アクション

### ① YAML修正の順番（どれから直すか）

1. `PLN-PLN-CONS-002.yaml`：MDに根拠のない外部参照（例: `shadow.md`）を除去/縮退し、Faithfulnessの成立性（タイムアウト回避）も改善する（HP-2/HP-3）。
2. `PLN-PLN-TBL-002.yaml` / `PLN-PLN-CONS-002.yaml`：`PLN-CONS-060` に引っかかる文字列（TODO/TBD/PENDING）を一時的に回避する（HP-1）※ただし本質はスクリプト修正。
3. `PLN-PLN-CONS-002.yaml`：`derived_from` を実根拠章へ拡張し、MD↔YAML追跡性を上げる（MP-2）。

### ② 再実行の条件（どのRunを回すか）

- Run-1（pln_transform）を再実行（同条件: MD=`PLN-PLN-FLW-002.md`, YAML=`artifacts/planning/yaml/v3`, Checklist=`CHK-PLN-CONSIST-001.yaml`）
- 成立条件（今回のFail再発防止）:
  - `results[Faithfulness :: PLN-PLN-CONS-002.yaml].status != "error"`（TimeoutErrorを0件に）
  - `results[Checklist :: PLN-CONS-060].passed == true`（誤検知が解消されていること）

### ③ 合格基準（今回のRun-1での到達目標）

- 最低到達目標（評価が成立し、変換品質を語れる状態）:
  - 21/21 PASS（少なくとも `status=error` が0件）
  - `PLN-CONS-060` が「プレースホルダ値の残存」のみをFailにできている（方針文の言及ではFailにならない）
- 変換品質の到達目標（MD↔YAML）:
  - 参照MDに存在しない根拠（外部ファイル参照や未記載の詳細）がYAMLに混入していないこと（例: `shadow.md` のようなMD外参照が0件）
