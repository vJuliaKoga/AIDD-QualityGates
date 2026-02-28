import hashlib
import sys
from pathlib import Path


def sha256_of_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) < 2:
        print("Usage: python hashtag_generator.py <path-to-yaml>")
        raise SystemExit(2)

    file_path = Path(sys.argv[1]).expanduser().resolve()
    print(sha256_of_file(file_path))


if __name__ == "__main__":
    main()
