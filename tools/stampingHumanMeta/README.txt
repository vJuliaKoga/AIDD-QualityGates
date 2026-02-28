MDファイルにmeta情報を添付する例
```shell
python AIDD\tools\stampingHumanMeta\stampingHumanMeta.py `
  --file AIDD\planning\planning_v2.2.md `
  --artifact-id PLN-PLN-GOAL-001 `
  --author @juria.koga `
  --source-type human `
  --supersedes planning_v2.1.md `
  --hash-script AIDD\hashtag\hashtag_generator.py
```

yamlにmeta情報を添付する例
```shell
python AIDD\tools\stampingHumanMeta\stampingHumanMeta.py `
  --file AIDD\RULES\TPL-OPS-RULES-001.yaml `
  --artifact-id TPL-OPS-RULES-001 `
  --author @juria.koga `
  --source-type human `
  --hash-script AIDD\hashtag\hashtag_generator.py
```