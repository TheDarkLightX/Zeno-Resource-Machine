"""Fail closed when the specification-package manifest is stale."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "PACKAGE_MANIFEST.json"


class ManifestError(ValueError):
    """Raised when the package manifest does not match its payload files."""


def require(condition: bool, message: str) -> None:
    """Raise a typed manifest error for a failed invariant."""

    if not condition:
        raise ManifestError(message)


def validate_manifest(data: dict[str, Any]) -> None:
    """Validate schema, ordering, counts, sizes, and SHA-256 digests."""

    require(
        data.get("schema") == "zrm/specification-package-manifest/v1",
        "unexpected manifest schema",
    )
    files = data.get("files")
    require(isinstance(files, list), "files must be a list")
    require(data.get("file_count") == len(files), "file_count is stale")
    require(
        data.get("total_file_count_including_manifest") == len(files) + 1,
        "total file count is stale",
    )

    paths = [entry.get("path") for entry in files if isinstance(entry, dict)]
    require(len(paths) == len(files), "every file entry must be an object")
    require(all(isinstance(path, str) and path for path in paths), "invalid payload path")
    require(paths == sorted(paths, key=lambda path: path.encode("utf-8")), "payload paths are not bytewise sorted")
    require(len(paths) == len(set(paths)), "duplicate payload path")

    for entry, relative_path in zip(files, paths, strict=True):
        path = ROOT / relative_path
        require(path.is_file(), f"missing payload file: {relative_path}")
        payload = path.read_bytes()
        require(entry.get("bytes") == len(payload), f"stale byte count: {relative_path}")
        digest = hashlib.sha256(payload).hexdigest()
        require(entry.get("sha256") == digest, f"stale SHA-256: {relative_path}")


def main() -> int:
    """Load and validate the repository package manifest."""

    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        require(isinstance(data, dict), "manifest root must be an object")
        validate_manifest(data)
    except (ManifestError, json.JSONDecodeError, OSError) as error:
        print(f"package manifest check failed: {error}", file=sys.stderr)
        return 1
    print("package manifest check passed: all payload sizes and SHA-256 digests match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
