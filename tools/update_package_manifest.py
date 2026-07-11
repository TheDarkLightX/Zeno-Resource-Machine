"""Regenerate specification-package payload sizes and SHA-256 digests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "PACKAGE_MANIFEST.json"


def main() -> int:
    """Update only derived file metadata while preserving manifest policy fields."""

    data: dict[str, Any] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files = data["files"]
    for entry in files:
        payload = (ROOT / entry["path"]).read_bytes()
        entry["bytes"] = len(payload)
        entry["sha256"] = hashlib.sha256(payload).hexdigest()
    data["file_count"] = len(files)
    data["total_file_count_including_manifest"] = len(files) + 1
    MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"updated package manifest for {len(files)} payload files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
