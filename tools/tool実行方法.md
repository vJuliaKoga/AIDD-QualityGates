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
python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingHumanMeta\stampingHumanMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\packs\checklists\CHK-PLN-CONSIST-001.template.yaml" --artifact-id "CHK-PLN-CONSIST-001" --author "@juria.koga" --source-type human --source "manual" --timestamp "2026-03-01T00:14:00+09:00" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"
```

### stampingMeta

```shell
python "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\stampingMeta\stampingMeta.py" --file "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\packs\prompts\PRM-PLN-YAML-002.md" --prompt-id "PRM-PLN-YAML-002" --hash-script "C:\Users\juria.koga\Documents\Github\AIDD-QualityGates\tools\hashtag\hashtag_generator.py"
```

### JSON Scheme

python -c "import yaml, json, sys; from jsonschema import Draft202012Validator; s=json.load(open(r'packs\pln_pack\schemas\inspection_design.schema.json',encoding='utf-8')); d=yaml.safe_load(open(r'artifacts\planning\PLN-PLN-TBL-001.yaml',encoding='utf-8')); errs=sorted(Draft202012Validator(s).iter_errors(d), key=lambda e:e.path); print('OK' if not errs else '\n'.join([f'ERROR: {list(e.path)}: {e.message}' for e in errs])); sys.exit(0 if not errs else 2)"
