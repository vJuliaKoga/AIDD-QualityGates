import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import yaml


def now_str():
    # 既存の手動メタと合わせてこの表示形式にする（+09:00でもOK）
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def run_sha256(script_path: Path, target_file: Path) -> str:
    res = subprocess.run(
        [sys.executable, str(script_path), str(target_file)],
        capture_output=True, text=True
    )
    if res.returncode != 0:
        raise SystemExit(
            "Hash script failed.\n"
            f"cmd: {sys.executable} {script_path} {target_file}\n"
            f"stdout:\n{res.stdout}\n"
            f"stderr:\n{res.stderr}\n"
        )
    out = res.stdout.strip().splitlines()
    if not out:
        raise SystemExit("Hash script produced no output.")
    return out[-1].strip()


def assert_meta_present(f: Path, expected_artifact_id: str, expected_source: str):
    data = yaml.safe_load(f.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("YAML root must be an object")

    meta = data.get("meta")
    if not isinstance(meta, dict):
        raise SystemExit("meta is missing after stamping.")

    required = ["artifact_id", "file", "author", "source_type", "source", "timestamp", "model", "content_hash"]
    missing = [k for k in required if k not in meta]
    if missing:
        raise SystemExit(f"meta missing keys after stamping: {missing}")

    if meta["artifact_id"] != expected_artifact_id:
        raise SystemExit(f"meta.artifact_id mismatch: {meta['artifact_id']} != {expected_artifact_id}")
    if meta["source"] != expected_source:
        raise SystemExit(f"meta.source mismatch: {meta['source']} != {expected_source}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="artifacts/planning/PLN-PLN-GOAL-001.yaml etc.")
    ap.add_argument("--prompt-id", required=True, help="PRM-PLN-YAML-001 etc. (will be stored in meta.source)")
    ap.add_argument("--hash-script", default="hashtag/hashtag_generator.py")
    args = ap.parse_args()

    f = Path(args.file).resolve()
    if not f.exists():
        raise SystemExit(f"--file not found: {f}")

    prompt_id = args.prompt_id.strip()
    hash_script = Path(args.hash_script).resolve()
    if not hash_script.exists():
        raise SystemExit(f"--hash-script not found: {hash_script}")

    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit("YAML root must be a mapping/object")

    artifact_id = f.stem  # ファイル名 = artifact_id 運用
    model = "gpt-5.2"

    meta = data.get("meta")
    if not isinstance(meta, dict):
        meta = {}

    meta.update({
        "artifact_id": artifact_id,
        "file": f.name,
        "author": model,          # author=model
        "source_type": "ai",
        "source": prompt_id,      # source=prompt_id
        "timestamp": now_str(),
        "model": model,
        "content_hash": "PENDING"
    })
    data["meta"] = meta

    # 1回保存（meta込み最終形でハッシュを取るため）
    f.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # ハッシュ確定
    h = run_sha256(hash_script, f)
    data["meta"]["content_hash"] = h

    # 最終保存
    f.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # 再読込して確認
    assert_meta_present(f, expected_artifact_id=artifact_id, expected_source=prompt_id)

    print(f"Stamped AI meta into: {f}")


if __name__ == "__main__":
    main()
