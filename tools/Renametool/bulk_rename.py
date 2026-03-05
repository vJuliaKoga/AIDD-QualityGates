#!/usr/bin/env python3
"""
ディレクトリ内のファイルを一括置換するスクリプト

Usage:
    python bulk_rename.py /path/to/directory --dry-run  # 確認モード
    python bulk_rename.py /path/to/directory             # 実行モード
"""

import os
import sys
import argparse
from pathlib import Path
import re
import shutil
from datetime import datetime


# 置換ルール定義
REPLACEMENTS = [
    # 正確な一致を優先（長い方から）
    ("Score Aggregation Manager", "Score Aggregation Manager"),
    ("score aggregation manager", "score aggregation manager"),
    ("Score Aggregation Managers", "Score Aggregation Managers"),  # 複数形
    ("score aggregation managers", "score aggregation managers"),
    ("SAM-UI", "SAM-UI"),
    
    # 括弧付き略称
    ("（SAM）", "（SAM）"),
    ("(SAM)", "(SAM)"),
    ("「SAM」", "「SAM」"),
    
    # 略称単体（単語境界を考慮）
    (r'\bQG\b', 'SAM'),
    (r'\bqg\b', 'sam'),
    
    # CheckFlow
    ("CheckFlow", "CheckFlow"),
    ("checkflow", "checkflow"),
    ("CheckFlow", "CheckFlow"),
    ("checkflow", "checkflow"),
    ("CheckFlow", "CheckFlow"),
]

# 処理対象の拡張子
TARGET_EXTENSIONS = {
    '.md', '.txt', '.yaml', '.yml', '.json', 
    '.py', '.js', '.ts', '.jsx', '.tsx',
    '.html', '.css', '.scss', '.sh',
    '.xml', '.csv', '.tsv'
}

# 除外するディレクトリ
EXCLUDE_DIRS = {
    '.git', '.svn', 'node_modules', '__pycache__', 
    '.venv', 'venv', 'dist', 'build'
}


def is_text_file(file_path):
    """ファイルがテキストファイルかどうかを判定"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # 最初の1KBを読んでみる
        return True
    except (UnicodeDecodeError, PermissionError):
        return False


def replace_in_text(text, replacements):
    """テキスト内の文字列を置換"""
    modified = False
    result = text
    
    for old, new in replacements:
        if r'\b' in old:  # 正規表現パターン
            if re.search(old, result):
                result = re.sub(old, new, result)
                modified = True
        else:  # 通常の文字列置換
            if old in result:
                result = result.replace(old, new)
                modified = True
    
    return result, modified


def process_file(file_path, replacements, dry_run=True):
    """ファイルを処理"""
    try:
        # ファイルを読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 置換実行
        new_content, modified = replace_in_text(original_content, replacements)
        
        if modified:
            if dry_run:
                print(f"  [DRY-RUN] 変更あり: {file_path}")
                return True, False
            else:
                # バックアップを作成
                backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_path)
                
                # ファイルを書き込み
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"  [UPDATED] {file_path}")
                print(f"    バックアップ: {backup_path}")
                return True, True
        else:
            return False, False
            
    except Exception as e:
        print(f"  [ERROR] {file_path}: {e}")
        return False, False


def scan_directory(directory, replacements, dry_run=True):
    """ディレクトリを再帰的にスキャンして処理"""
    directory = Path(directory)
    
    if not directory.exists():
        print(f"エラー: ディレクトリが存在しません: {directory}")
        return
    
    print(f"\n{'='*60}")
    print(f"対象ディレクトリ: {directory}")
    print(f"モード: {'ドライラン（確認のみ）' if dry_run else '実行モード（実際に変更）'}")
    print(f"{'='*60}\n")
    
    files_checked = 0
    files_modified = 0
    files_would_modify = 0
    
    # ディレクトリを再帰的に走査
    for file_path in directory.rglob('*'):
        # ディレクトリをスキップ
        if file_path.is_dir():
            continue
        
        # 除外ディレクトリ内のファイルをスキップ
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue
        
        # 拡張子チェック
        if file_path.suffix not in TARGET_EXTENSIONS:
            continue
        
        # テキストファイルかチェック
        if not is_text_file(file_path):
            continue
        
        files_checked += 1
        
        # ファイルを処理
        has_changes, was_modified = process_file(file_path, replacements, dry_run)
        
        if has_changes:
            if dry_run:
                files_would_modify += 1
            else:
                files_modified += 1
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print(f"処理結果:")
    print(f"  チェックしたファイル数: {files_checked}")
    if dry_run:
        print(f"  変更が必要なファイル数: {files_would_modify}")
        print(f"\n実際に変更するには --execute オプションを付けて再実行してください")
    else:
        print(f"  変更したファイル数: {files_modified}")
        print(f"\n※バックアップファイルが作成されています（.backup_* ファイル）")
    print(f"{'='*60}\n")


def show_replacements():
    """置換ルールを表示"""
    print("\n置換ルール:")
    print("-" * 60)
    for old, new in REPLACEMENTS:
        if r'\b' in old:
            print(f"  {old} (正規表現) → {new}")
        else:
            print(f"  {old} → {new}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='ディレクトリ内のファイルを一括置換',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 確認モード（実際には変更しない）
  python bulk_rename.py /path/to/directory
  
  # 実行モード（実際に変更する）
  python bulk_rename.py /path/to/directory --execute
  
  # 置換ルールを表示
  python bulk_rename.py --show-rules
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        help='処理対象のディレクトリパス'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='実際に変更を実行する（デフォルトはドライランモード）'
    )
    
    parser.add_argument(
        '--show-rules',
        action='store_true',
        help='置換ルールを表示して終了'
    )
    
    args = parser.parse_args()
    
    # 置換ルール表示
    if args.show_rules:
        show_replacements()
        return
    
    # ディレクトリが指定されていない場合
    if not args.directory:
        parser.print_help()
        return
    
    # 置換ルールを表示
    show_replacements()
    
    # 確認
    if args.execute:
        print("\n⚠️  実行モードで処理を開始します。ファイルが実際に変更されます。")
        response = input("続行しますか？ (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("キャンセルしました。")
            return
    
    # 処理実行
    scan_directory(args.directory, REPLACEMENTS, dry_run=not args.execute)


if __name__ == '__main__':
    main()