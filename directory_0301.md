AIDD-QualityGates/
├── .deepeval/
│   ├── .deepeval_telemetry.txt
│   ├── .deepeval-cache.json
│   ├── .latest_test_run.json
│   └── .temp_test_run_data.json
├── .pytest_cache/
│   ├── v/
│   │   └── cache/
│   │       ├── lastfailed
│   │       ├── nodeids
│   │       └── stepwise
│   ├── .gitignore
│   ├── CACHEDIR.TAG
│   └── README.md
├── artifacts/
│   └── planning/
│       ├── archive/
│       │   ├── PLN-PLN-FLW-001_v1/
│       │   │   ├── PLN-PLN-FLW-001.md
│       │   │   ├── PLN-PLN-FLW-001.yaml
│       │   │   ├── PLN-PLN-SCOPE-001.yaml
│       │   │   └── PLN-PLN-TBL-001.yaml
│       │   ├── PLN-PLN-FLW-001_v2/
│       │   │   ├── gate_report_after_goal_fix.json
│       │   │   ├── PLN-PLN-AIQUA-001.yaml
│       │   │   ├── PLN-PLN-CONS-001.yaml
│       │   │   ├── PLN-PLN-DES-001.yaml
│       │   │   ├── PLN-PLN-EVAL-001.yaml
│       │   │   ├── PLN-PLN-FLW-001.yaml
│       │   │   ├── PLN-PLN-GOAL-001.yaml
│       │   │   ├── PLN-PLN-INT-001.yaml
│       │   │   ├── PLN-PLN-PROB-001.yaml
│       │   │   ├── PLN-PLN-RUN-001.yaml
│       │   │   ├── PLN-PLN-SCOPE-001.yaml
│       │   │   ├── PLN-PLN-TBL-001.yaml
│       │   │   ├── traceability_check_report.json
│       │   │   └── traceability_check_report_after_goal_fix.json
│       │   ├── defect_report_pln_yaml_gaps_20260301.md
│       │   ├── log.md
│       │   └── planning_v1.md
│       ├── yaml/
│       │   ├── v1/
│       │   │   ├── PLN-PLN-AIQUA-001.yaml
│       │   │   ├── PLN-PLN-CONS-001.yaml
│       │   │   ├── PLN-PLN-DES-001.yaml
│       │   │   ├── PLN-PLN-EVAL-001.yaml
│       │   │   ├── PLN-PLN-FLW-001.yaml
│       │   │   ├── PLN-PLN-GOAL-001.yaml
│       │   │   ├── PLN-PLN-INT-001.yaml
│       │   │   ├── PLN-PLN-PROB-001.yaml
│       │   │   ├── PLN-PLN-RUN-001.yaml
│       │   │   ├── PLN-PLN-SCOPE-001.yaml
│       │   │   └── PLN-PLN-TBL-001.yaml
│       │   ├── v2/
│       │   │   ├── PLN-PLN-AIQUA-002.yaml
│       │   │   ├── PLN-PLN-CONS-002.yaml
│       │   │   ├── PLN-PLN-DES-002.yaml
│       │   │   ├── PLN-PLN-EVAL-002.yaml
│       │   │   ├── PLN-PLN-FLW-002.yaml
│       │   │   ├── PLN-PLN-GOAL-002.yaml
│       │   │   ├── PLN-PLN-INT-002.yaml
│       │   │   ├── PLN-PLN-PROB-002.yaml
│       │   │   ├── PLN-PLN-RUN-002.yaml
│       │   │   ├── PLN-PLN-SCOPE-002.yaml
│       │   │   └── PLN-PLN-TBL-002.yaml
│       │   └── pln_canonical_template_v1.yaml
│       └── PLN-PLN-FLW-002.md
├── docs/
│   ├── BACKEND_ARCHITECTURE.md
│   ├── CLAUDE.md
│   ├── FRONTEND_GUIDELINES.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── lessons.md
│   ├── PRD.md
│   ├── progress.txt
│   ├── SCREEN_FLOW.md
│   └── TECH_STACK.md
├── id/
│   ├── id_issued_log.yaml
│   ├── id_rules_registry.yaml
│   └── issue_id.py
├── output/
│   ├── archive/
│   │   ├── planning/
│   │   │   ├── eval_md_vs_yaml_v1.json
│   │   │   └── report_eval_md_vs_yaml_v1.md
│   │   └── evaluate_planning_md_vs_yaml_v1.py
│   ├── G1/
│   │   └── artifacts_planning_yaml_v2/
│   │       └── 0301_1900.json
│   ├── G3/
│   │   ├── artifacts_planning_yaml/
│   │   │   └── 0301_1243.json
│   │   ├── artifacts_planning_yaml_v2/
│   │   │   ├── 0301_1857.json
│   │   │   └── 0301_1944.json
│   │   └── artifacts_planning_yaml_v2_PLN-PLN-AIQUA-002.yaml/
│   │       └── 0301_1905.json
│   └── G4/
│       ├── pln_transform/
│       │   ├── artifacts_planning_yaml/
│       │   │   └── 0301_1539.json
│       │   └── artifacts_planning_yaml_v2/
│       └── reports/
│           ├── pln_coverage/
│           │   └── RES-PLN-COV-001.md (E)
│           └── pln_transform/
│               └── RES-PLN-TRANS-001.md
├── packs/
│   ├── checklists/
│   │   ├── CHK-PLN-AIDD-001.yaml
│   │   └── CHK-PLN-CONSIST-001.yaml
│   ├── docs/
│   │   ├── README.md (E)
│   │   └── tutorial.md (E)
│   ├── pln_pack/
│   │   ├── archive/
│   │   │   └── schemas/
│   │   │       ├── goal.schema.json
│   │   │       ├── inspection_design.schema.json
│   │   │       └── scope.schema.json
│   │   ├── config/
│   │   │   └── ambiguity_excludes.yaml
│   │   ├── schemas/
│   │   │   └── pln_canonical_v1.schema.json
│   │   ├── pln.pack.yaml
│   │   └── schema_registry.yaml
│   ├── prompts/
│   │   ├── PRM-PLN-COV-01.md
│   │   ├── PRM-PLN-FIX-001.md
│   │   ├── PRM-PLN-G3-FIX-001.md
│   │   ├── PRM-PLN-META-001.md
│   │   ├── PRM-PLN-TRANS-001.md
│   │   ├── PRM-PLN-YAML-001.md
│   │   ├── PRM-PLN-YAML-002.md
│   │   ├── PRM-PLN-YAML-003.md
│   │   ├── PRM-PLN-YAML-004.md
│   │   └── PRM-REQ-YAML-001.md
│   ├── req_pack/
│   │   ├── schemas/
│   │   │   └── requirements.schema.json
│   │   └── req.pack.yaml (E)
│   ├── rules/
│   │   └── ambiguous_terms_ja.txt (E)
│   ├── schemas/
│   │   └── plan.schema.yaml
│   ├── workflows/
│   │   └── workflow.pln.yaml (E)
│   └── pack.yaml
├── runner/
│   ├── __pycache__/
│   │   └── aidd-gate.cpython-312.pyc
│   ├── allure/
│   │   ├── __pycache__/
│   │   │   └── allure_helpers.cpython-312.pyc
│   │   └── allure_helpers.py (E)
│   ├── gates/
│   │   ├── __pycache__/
│   │   │   ├── g1_ambiguity.cpython-312.pyc
│   │   │   ├── g2_checklist_completion.cpython-312.pyc
│   │   │   ├── g3_schema.cpython-312.pyc
│   │   │   ├── g4_deepeval.cpython-312.pyc
│   │   │   └── g5_trace.cpython-312.pyc
│   │   ├── scripts/
│   │   │   ├── run_g4_pln_coverage.ps1
│   │   │   └── run_g4_pln_transform.ps1
│   │   ├── g1_ambiguity.py
│   │   ├── g2_checklist_completion.py (E)
│   │   ├── g3_schema.py
│   │   ├── g4_deepeval.py
│   │   ├── g5_trace.py (E)
│   │   └── pf_promptfoo.sh (E)
│   ├── aidd-gate.py
│   └── Dockerfile
├── tests/
│   ├── __pycache__/
│   │   └── test_pln_pack.cpython-312-pytest-8.3.4.pyc
│   └── test_pln_pack.py
├── tools/
│   ├── hashtag/
│   │   └── hashtag_generator.py
│   ├── stampingHumanMeta/
│   │   ├── human.meta.template.yaml
│   │   ├── README.txt
│   │   └── stampingHumanMeta.py
│   ├── stampingMeta/
│   │   └── stampingMeta.py
│   └── tool実行方法.md
├── .gitattributes
├── directory_03010017.yaml
└── requirements.txt
