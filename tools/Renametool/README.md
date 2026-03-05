# 一括置換スクリプト使用方法

## 概要

ディレクトリ内のファイルを一括で置換するPythonスクリプトです。

以下の置換を実行します：
- `Score Aggregation Manager` → `Score Aggregation Manager`
- `（SAM）` → `（SAM）`
- `CheckFlow` → `CheckFlow`

## 使い方

### 1. 確認モード（推奨・最初はこちら）

実際には変更せず、どのファイルが変更されるかを確認します。

```bash
python bulk_rename.py /path/to/your/directory
```

### 2. 実行モード

実際にファイルを変更します。**バックアップが自動作成されます。**

```bash
python bulk_rename.py /path/to/your/directory --execute
```

### 3. 置換ルールを確認

どんな置換が行われるかを確認します。

```bash
python bulk_rename.py --show-rules
```

## 実行例

```bash
# 現在のディレクトリを確認モードで処理
python bulk_rename.py .

# 特定のディレクトリを実行モードで処理
python bulk_rename.py /home/user/project --execute
```

## 処理対象ファイル

以下の拡張子のファイルが対象です：
- `.md`, `.txt` (ドキュメント)
- `.yaml`, `.yml`, `.json` (設定ファイル)
- `.py`, `.js`, `.ts`, `.jsx`, `.tsx` (プログラム)
- `.html`, `.css`, `.scss` (Web)
- `.xml`, `.csv`, `.tsv` (データ)
- `.sh` (シェルスクリプト)

## 除外されるディレクトリ

以下のディレクトリは処理されません：
- `.git`, `.svn` (バージョン管理)
- `node_modules`, `__pycache__` (依存関係)
- `.venv`, `venv` (仮想環境)
- `dist`, `build` (ビルド成果物)

## 安全機能

1. **バックアップ自動作成**: 変更したファイルは `.backup_YYYYMMDD_HHMMSS` として保存されます
2. **ドライランモード**: デフォルトは確認のみで、実際には変更しません
3. **実行前確認**: `--execute` 時は確認プロンプトが表示されます

## 注意事項

- 必ず最初は確認モードで実行してください
- 大事なプロジェクトはGitなどでバージョン管理してから実行してください
- バックアップファイル（`.backup_*`）は後で削除してください

## トラブルシューティング

### エラー: PermissionError

ファイルのアクセス権限がない場合のエラーです。

```bash
chmod +x bulk_rename.py
```

### 文字化けする

UTF-8以外のエンコーディングのファイルは処理されません。必要に応じてスクリプトを修正してください。

## 置換ルール詳細

| 元の文字列 | 置換後 | 備考 |
|-----------|--------|------|
| Score Aggregation Manager | Score Aggregation Manager | 大文字 |
| score aggregation manager | score aggregation manager | 小文字 |
| Score Aggregation Managers | Score Aggregation Managers | 複数形 |
| （SAM） | （SAM） | 全角括弧 |
| (SAM) | (SAM) | 半角括弧 |
| SAM | SAM | 単語境界を考慮 |
| CheckFlow | CheckFlow | 様々な表記に対応 |
| CheckFlow | CheckFlow | ハイフン付き |
| CheckFlow | CheckFlow | スペースなし |

## カスタマイズ

置換ルールを変更したい場合は、スクリプト内の `REPLACEMENTS` リストを編集してください。

```python
REPLACEMENTS = [
    ("元の文字列", "新しい文字列"),
    # ... 追加のルール
]
```