#!/usr/bin/env python3
"""Build a deterministic, clean source archive for hackathon review."""
from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist"}
SECRET_NAMES = {".env", ".npmrc", "auth.json", "credentials.json", "secrets.json"}
SECRET_SUFFIXES = {".pem", ".key"}


def is_secret_name(name: str) -> bool:
    lowered = name.lower()
    return lowered in SECRET_NAMES or lowered.startswith(".env.")


def build_archive(root: Path, output: Path) -> int:
    root = root.resolve()
    output = output.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"source root is not a directory: {root}")
    output.parent.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_dir() and path.name in EXCLUDED_DIRS:
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.resolve() == output:
            continue
        if path.is_symlink():
            raise ValueError(f"refusing to archive symlink: {path.relative_to(root)}")
        if not path.is_file():
            continue
        if is_secret_name(path.name) or path.suffix.lower() in SECRET_SUFFIXES:
            raise ValueError(f"refusing to archive secret-shaped file: {path.relative_to(root)}")
        if path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        files.append(path)

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            member = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.flag_bits |= 0x800
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        count = build_archive(args.root, args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(f"Built source review archive: {args.output.resolve()} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
