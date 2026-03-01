---
meta:
  artifact_id: PRM-PLN-YAML-005
  file: PRM-PLN-YAML-005.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-01T11:45:00+09:00"
  content_hash: bb09f4127199221d914e79afb992b05cada08ee01afdc7db660c2414143bad6f
---

<DIRECTORY> 配下の各ファイルに対して、以下を実行してください。

0. 入力値
   - PROMPT_ID = PRM-PLN-YAML-005
   - DIRECTORY：artifacts/planning/yaml

1. 各YAMLの meta を「schema_version だけ残して他は削除」する
   - meta が無い場合は何もしない
   - meta.schema_version がある場合だけ保持する
   - 下記キー（artifact_id/file/author/source_type/source/timestamp/model/content_hash など）は全て削除する

2. tools/stampingMeta/stampingMeta.py を各ファイルに対して実行し、meta を付与し直す
   - コマンド例:
     python tools/stampingMeta/stampingMeta.py --file <対象ファイルパス> --prompt-id <PROMPT_ID> --hash-script tools/hashtag/hashtag_generator.py

3. 実行後、各ファイルに meta.content_hash が PENDING ではなく sha256 の16進文字列で入っていることを確認する
