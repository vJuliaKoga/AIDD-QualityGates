# Directory structure

`C:\Users\juria.koga\Documents\Github\AIDD-QualityGates` の現状ディレクトリ構造（`tree /F /A` 実行結果）:

```text
フォルダー パスの一覧
ボリューム シリアル番号は D46D-6BC2 です
C:.
|   .env.local
|   .gitattributes
|   directory.md
|   requirements.txt
|
+---.deepeval
|       .deepeval-cache.json
|       .deepeval_telemetry.txt
|       .latest_test_run.json
|       .temp_test_run_data.json
|
+---.pytest_cache
|   |   .gitignore
|   |   CACHEDIR.TAG
|   |   README.md
|   |
|   \---v
|       \---cache
|               lastfailed
|               nodeids
|               stepwise
|
+---artifacts
|   \---planning
|       |   PLN-PLN-FLW-003.md
|       |   pln_canonical_template_v1.yaml
|       |
|       +---archive
|       |   |   PLN-PLN-FLW-001.md
|       |   |   PLN-PLN-FLW-002.md
|       |   |
|       |   +---et_cetera
|       |   |       defect_report_pln_yaml_gaps_20260301.md
|       |   |       log.md
|       |   |       matome.md
|       |   |       planning_v1.md
|       |   |       toolidea.md
|       |   |
|       |   +---PLN-002
|       |   |       PLN-PLN-CONS-001.yaml
|       |   |       PLN-PLN-EVAL-001.yaml
|       |   |       PLN-PLN-GOAL-001.yaml
|       |   |
|       |   +---PLN-PLN-FLW-001_v1
|       |   |       PLN-PLN-FLW-001.md
|       |   |       PLN-PLN-FLW-001.yaml
|       |   |       PLN-PLN-SCOPE-001.yaml
|       |   |       PLN-PLN-TBL-001.yaml
|       |   |
|       |   +---PLN-PLN-FLW-001_v2
|       |   |       gate_report_after_goal_fix.json
|       |   |       PLN-PLN-AIQUA-001.yaml
|       |   |       PLN-PLN-CONS-001.yaml
|       |   |       PLN-PLN-DES-001.yaml
|       |   |       PLN-PLN-EVAL-001.yaml
|       |   |       PLN-PLN-FLW-001.yaml
|       |   |       PLN-PLN-GOAL-001.yaml
|       |   |       PLN-PLN-INT-001.yaml
|       |   |       PLN-PLN-PROB-001.yaml
|       |   |       PLN-PLN-RUN-001.yaml
|       |   |       PLN-PLN-SCOPE-001.yaml
|       |   |       PLN-PLN-TBL-001.yaml
|       |   |       traceability_check_report.json
|       |   |       traceability_check_report_after_goal_fix.json
|       |   |
|       |   +---PLN-PLN-FLW-002
|       |   |       PLN-PLN-AIQUA-001.yaml
|       |   |       PLN-PLN-CONS-001.yaml
|       |   |       PLN-PLN-DES-001.yaml
|       |   |       PLN-PLN-EVAL-001.yaml
|       |   |       PLN-PLN-FLW-001.yaml
|       |   |       PLN-PLN-GOAL-001.yaml
|       |   |       PLN-PLN-INT-001.yaml
|       |   |       PLN-PLN-PROB-001.yaml
|       |   |       PLN-PLN-RUN-001.yaml
|       |   |       PLN-PLN-SCOPE-001.yaml
|       |   |       PLN-PLN-TBL-001.yaml
|       |   |
|       |   \---PLN-PLN-FLW-002_FIX
|       |           PLN-PLN-AIQUA-002.yaml
|       |           PLN-PLN-CONS-002.yaml
|       |           PLN-PLN-DES-002.yaml
|       |           PLN-PLN-EVAL-002.yaml
|       |           PLN-PLN-FLW-002.yaml
|       |           PLN-PLN-GOAL-002.yaml
|       |           PLN-PLN-INT-002.yaml
|       |           PLN-PLN-PROB-002.yaml
|       |           PLN-PLN-RUN-002.yaml
|       |           PLN-PLN-SCOPE-002.yaml
|       |           PLN-PLN-TBL-002.yaml
|       |
|       \---yaml
|           \---PLN-PLN-FLW-003
|                   PLN-PLN-CONS-001.yaml
|                   PLN-PLN-DES-001.yaml
|                   PLN-PLN-DES-002.yaml
|                   PLN-PLN-DES-003.yaml
|                   PLN-PLN-DES-004.yaml
|                   PLN-PLN-DES-005.yaml
|                   PLN-PLN-DES-006.yaml
|                   PLN-PLN-EVAL-001.yaml
|                   PLN-PLN-FLW-001.yaml
|                   PLN-PLN-FLW-002.yaml
|                   PLN-PLN-INT-001.yaml
|                   PLN-PLN-PROB-001.yaml
|                   PLN-PLN-RUN-001.yaml
|                   PLN-PLN-SCOPE-001.yaml
|                   PLN-PLN-UI-001.yaml
|                   PLN-PLN-YAML-001.yaml
|
+---docs
|       BACKEND_ARCHITECTURE.md
|       CLAUDE.md
|       FRONTEND_GUIDELINES.md
|       IMPLEMENTATION_PLAN.md
|       lessons.md
|       PRD.md
|       progress.txt
|       SCREEN_FLOW.md
|       TECH_STACK.md
|
+---id
|       id_issued_log.yaml
|       id_rules_registry.yaml
|       issue_id.py
|
+---output
|   +---archive
|   |   |   evaluate_planning_md_vs_yaml_v1.py
|   |   |   g4_deepeval_old.py
|   |   |
|   |   \---planning
|   |           eval_md_vs_yaml_v1.json
|   |           report_eval_md_vs_yaml_v1.md
|   |
|   +---G1
|   |   +---artifacts_planning_yaml_v2
|   |   |       0301_1900.json
|   |   |       0301_2059.json
|   |   |
|   |   \---artifacts_planning_yaml_v3
|   |           0301_2100.json
|   |           0301_2116.json
|   |           0301_2126.json
|   |           0301_2128.json
|   |
|   +---G3
|   |   +---artifacts_planning_yaml
|   |   |       0301_1243.json
|   |   |
|   |   \---artifacts_planning_yaml_v2
|   |           0301_1857.json
|   |           0301_1905.json
|   |           0301_1944.json
|   |
|   \---G4
|       +---pln_transform
|       |   +---allure-results
|       |   |       08711d96-0304-4d67-a459-cde8853edb80-result.json
|       |   |       0dd7ed55-4db1-46c8-a935-20f7e9ce984a-result.json
|       |   |       297f5753-43cd-4e40-87e3-20ed103a70d2-result.json
|       |   |       2b99b2db-0cb9-4fe3-ab9b-73c9ba3090b5-result.json
|       |   |       2bc1cbd1-ab8a-4a55-8ecd-0bcfb3ba9161-result.json
|       |   |       557839d1-7f72-4b3f-803a-c5359e3d6325-result.json
|       |   |       6c973797-b8b1-4634-97b6-d5ed2f292aa1-result.json
|       |   |       6d79363b-3f02-4e16-91ba-5837f6b99121-result.json
|       |   |       6ea73eb3-f1f4-46df-bea1-10639f8d8e04-result.json
|       |   |       76c1d733-d2a9-4c59-926c-7cc81ba7801c-result.json
|       |   |       77134909-60ce-4adc-8d34-2d73757052fc-result.json
|       |   |       8da3b64b-bfc3-4f40-ba19-2d8af8c29a17-result.json
|       |   |       9ad70fe2-98b2-4a5b-a06d-f2fadce24f69-result.json
|       |   |       a06542e1-6e18-4341-9e19-a399d3ab6ec1-result.json
|       |   |       b1c7946d-6a4b-4b30-9250-e38fd0a7831a-result.json
|       |   |       bb0e4051-d83a-4951-bc08-339d350076bf-result.json
|       |   |       c1859121-e75e-4676-9c3c-49b2a5cffc08-result.json
|       |   |       ce7b7d60-74c8-4c1a-a3aa-afab3ffb6c48-result.json
|       |   |       d642bbb2-f849-4084-ac6a-c8fb5afcef95-result.json
|       |   |       d663291c-2393-45bf-97e9-0aeeb60c5c58-result.json
|       |   |       f87e8a79-331c-4fe1-95ad-f4c4cf60d7f5-result.json
|       |   |
|       |   +---artifacts_planning_yaml
|       |   |       0301_1539.json
|       |   |
|       |   +---artifacts_planning_yaml_v2
|       |   |       0301_1957.json
|       |   |       0301_2023.json
|       |   |
|       |   \---artifacts_planning_yaml_v3
|       |           0301_2211.json
|       |           0301_2242.json
|       |           0301_2248.json
|       |           0302_0818.json
|       |           0302_0910.json
|       |           0302_1139.json
|       |
|       \---reports
|           +---pln_coverage
|           |       RES-PLN-COV-001.md
|           |
|           \---pln_transform
|                   RES-PLN-TRANS-001.md
|                   RES-PLN-TRANS-002.md
|                   RES-PLN-TRANS-003.md
|
+---packs
|   |   pack.yaml
|   |
|   +---checklists
|   |       CHK-PLN-AIDD-001.yaml
|   |       CHK-PLN-CONSIST-001.yaml
|   |
|   +---docs
|   |       README.md
|   |       tutorial.md
|   |
|   +---pln_pack
|   |   |   pln.pack.yaml
|   |   |   schema_registry.yaml
|   |   |
|   |   +---archive
|   |   |   \---schemas
|   |   |           goal.schema.json
|   |   |           inspection_design.schema.json
|   |   |           scope.schema.json
|   |   |
|   |   +---config
|   |   |       ambiguity_excludes.yaml
|   |   |
|   |   \---schemas
|   |           pln_canonical_v1.schema.json
|   |
|   +---prompts
|   |       PLN-PLN-TBL-001.md
|   |       PRM-PLN-COV-01.md
|   |       PRM-PLN-FLW_001.md
|   |       PRM-PLN-G1-FIX-001.md
|   |       PRM-PLN-G3-FIX-001.md
|   |       PRM-PLN-G4-FIX-001.md
|   |       PRM-PLN-META-001.md
|   |       PRM-PLN-TRANS-001.md
|   |       PRM-PLN-YAML-001.md
|   |       PRM-PLN-YAML-002.md
|   |       PRM-PLN-YAML-003.md
|   |       PRM-PLN-YAML-004.md
|   |
|   +---req_pack
|   |   |   req.pack.yaml
|   |   |
|   |   \---schemas
|   |           requirements.schema.json
|   |
|   +---rules
|   |       ambiguous_terms_ja.txt
|   |
|   +---schemas
|   |       plan.schema.yaml
|   |
|   \---workflows
|           workflow.pln.yaml
|
+---runner
|   |   aidd-gate.py
|   |   Dockerfile
|   |
|   +---allure
|   |   |   allure_helpers.py
|   |   |
|   |   \---__pycache__
|   |           allure_helpers.cpython-312.pyc
|   |
|   +---gates
|   |   |   DeepEval.py
|   |   |   g1_ambiguity.py
|   |   |   g2_checklist_completion.py
|   |   |   g3_schema.py
|   |   |   g4_deepeval.py
|   |   |   g5_trace.py
|   |   |   pf_promptfoo.sh
|   |   |
|   |   +---scripts
|   |   |       run_g4_pln_coverage.ps1
|   |   |       run_g4_pln_transform.ps1
|   |   |
|   |   \---__pycache__
|   |           g1_ambiguity.cpython-312.pyc
|   |           g2_checklist_completion.cpython-312.pyc
|   |           g3_schema.cpython-312.pyc
|   |           g4_deepeval.cpython-312.pyc
|   |           g5_trace.cpython-312.pyc
|   |
|   \---__pycache__
|           aidd-gate.cpython-312.pyc
|
+---tests
|   |   test_pln_pack.py
|   |
|   \---__pycache__
|           test_pln_pack.cpython-312-pytest-8.3.4.pyc
|
\---tools
    |   memo.txt
    |   tool実行方法.md
    |
    +---hashtag
    |       hashtag_generator.py
    |
    +---stampingHumanMeta
    |       human.meta.template.yaml
    |       README.txt
    |       stampingHumanMeta.py
    |
    \---stampingMeta
            stampingMeta.py
```
