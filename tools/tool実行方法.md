tool実行例

### Deep Eval処理用スクリプト動作方法

```shell
python tools/generate_deep_eval_reports_v2.py --reports-dir reports/PRM-REQ-EVAL-002/v2
```

### Deep Evalタイムアウト対策

```shell
python deepeval/evaluate_req_vs_planning_v1.py --no-async --timeout-seconds 600
```

### stampingHumanMeta.py

```shell
python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingHumanMeta\stampingHumanMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\runner\gates\g3_schema.py" --artifact-id "RES-TST-RUN-001" --author "@juria.koga" --source-type human --source "manual" --timestamp "2026-03-01T13:02:00+09:00" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"
```

### stampingMeta

```shell
python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingMeta\stampingMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\packs\prompts\PRM-PLN-YAML-002.md" --prompt-id "PRM-PLN-YAML-002" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"
```

### JSON Scheme

python packs/pln_pack/runner/gates/g3_schema.py \
 packs/pln_pack/schemas/pln_canonical_v1.schema.json \
 artifacts/planning/yaml \
 output

### g3_scheme.py

python .\runner\gates\g3_schema.py .\packs\pln_pack\schemas\pln_canonical_v1.schema.json .\artifacts\planning\yaml .\output

### g4_deepeval.py

.\runner\gates\scripts\run_g4_pln_transform.ps1
