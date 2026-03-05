#!/usr/bin/env python3
"""
バックアップファイル（.backup_*）を削除するスクリプト

Usage:
    python cleanup_backups.py /path/to/directory --dry-run  # 確認モード
    python cleanup_backups.py /path/to/directory --execute  # 実行モード
"""

import os
import argparse
from pathlib import Path
from datetime import datetime


# バックアップファイルのパターン
BACKUP_PATTERN = ".backup_"

# 除外するディレクトリ
EXCLUDE_DIRS = {
    '.git', '.svn', 'node_modules', '__pycache__', 
    '.venv', 'venv', 'dist', 'build'
}


def is_backup_file(file_path):
    """ファイルがバックアップファイルかどうかを判定"""
    return BACKUP_PATTERN in file_path.name


def get_file_size_human(size_bytes):
    """ファイルサイズを人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def scan_backup_files(directory):
    """バックアップファイルをスキャン"""
    directory = Path(directory)
    
    if not directory.exists():
        print(f"エラー: ディレクトリが存在しません: {directory}")
        return []
    
    backup_files = []
    
    # ディレクトリを再帰的に走査
    for file_path in directory.rglob('*'):
        # ディレクトリをスキップ
        if file_path.is_dir():
            continue
        
        # 除外ディレクトリ内のファイルをスキップ
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue
        
        # バックアップファイルかチェック
        if is_backup_file(file_path):
            try:
                size = file_path.stat().st_size
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                backup_files.append({
                    'path': file_path,
                    'size': size,
                    'mtime': mtime
                })
            except Exception as e:
                print(f"  [警告] ファイル情報取得エラー: {file_path}: {e}")
    
    return backup_files


def delete_backup_files(backup_files, dry_run=True):
    """バックアップファイルを削除"""
    deleted_count = 0
    deleted_size = 0
    
    for backup_info in backup_files:
        file_path = backup_info['path']
        file_size = backup_info['size']
        
        try:
            if dry_run:
                print(f"  [DRY-RUN] 削除予定: {file_path}")
                print(f"    サイズ: {get_file_size_human(file_size)}, 更新日時: {backup_info['mtime'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                file_path.unlink()
                print(f"  [DELETED] {file_path}")
                print(f"    サイズ: {get_file_size_human(file_size)}")
                deleted_count += 1
                deleted_size += file_size
        except Exception as e:
            print(f"  [ERROR] 削除失敗: {file_path}: {e}")
    
    return deleted_count, deleted_size


def main():
    parser = argparse.ArgumentParser(
        description='バックアップファイル（.backup_*）を削除',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 確認モード（実際には削除しない）
  python cleanup_backups.py /path/to/directory
  
  # 実行モード（実際に削除する）
  python cleanup_backups.py /path/to/directory --execute
        """
    )
    
    parser.add_argument(
        'directory',
        help='処理対象のディレクトリパス'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='実際に削除を実行する（デフォルトはドライランモード）'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"対象ディレクトリ: {args.directory}")
    print(f"モード: {'ドライラン（確認のみ）' if not args.execute else '実行モード（実際に削除）'}")
    print(f"{'='*60}\n")
    
    # バックアップファイルをスキャン
    print("バックアップファイルをスキャン中...")
    backup_files = scan_backup_files(args.directory)
    
    if not backup_files:
        print("\nバックアップファイルが見つかりませんでした。")
        return
    
    # ファイル一覧を表示
    print(f"\n見つかったバックアップファイル: {len(backup_files)}件")
    print("-" * 60)
    
    total_size = sum(f['size'] for f in backup_files)
    print(f"合計サイズ: {get_file_size_human(total_size)}\n")
    
    # 確認
    if args.execute:
        print("⚠️  以下のファイルを削除します:\n")
        for backup_info in backup_files[:10]:  # 最初の10件を表示
            print(f"  - {backup_info['path']}")
        
        if len(backup_files) > 10:
            print(f"  ... 他 {len(backup_files) - 10} 件")
        
        print(f"\n合計: {len(backup_files)}件のファイルを削除します。")
        response = input("\n本当に削除しますか？ (yes/no): ")
        
        if response.lower() not in ['yes', 'y']:
            print("キャンセルしました。")
            return
        
        print()
    
    # 削除実行
    deleted_count, deleted_size = delete_backup_files(backup_files, dry_run=not args.execute)
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print(f"処理結果:")
    if args.execute:
        print(f"  削除したファイル数: {deleted_count}")
        print(f"  解放されたディスク容量: {get_file_size_human(deleted_size)}")
    else:
        print(f"  削除対象ファイル数: {len(backup_files)}")
        print(f"  解放予定ディスク容量: {get_file_size_human(total_size)}")
        print(f"\n実際に削除するには --execute オプションを付けて再実行してください")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
