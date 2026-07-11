"""Shared bounded types and validation for ZRM BOM tooling."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent
MAX_INPUT_BYTES = 1_048_576
SBOM_SCHEMA = "zrm/source-sbom/v1"
CRYPTOGRAPHY_REGISTRY_SCHEMA = "zrm/cryptography-registry/v1"
BUILD_SURFACE_POLICY_SCHEMA = "zrm/build-surface-policy/v1"
CBOM_SCHEMA = "zrm/cbom/v1"


class BomError(ValueError):
    """Raised when dependency or cryptography inventory data is ambiguous."""


@dataclass(frozen=True)
class WorkspaceSnapshot:
    """Locked Cargo metadata and lock bytes for one reviewed workspace scope."""

    scope: str
    manifest_path: str
    lockfile_path: str
    metadata: Mapping[str, object]
    lockfile_bytes: bytes


def canonical_json(value: object) -> str:
    """Return deterministic tooling JSON with one trailing newline."""

    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def normalize_path(path_text: str) -> str:
    """Return one normalized repository-relative POSIX path or reject."""

    if not isinstance(path_text, str) or not path_text or "\\" in path_text:
        raise BomError("BOM paths must be nonempty repository-relative POSIX paths")
    path = PurePosixPath(path_text)
    if path.is_absolute() or ".." in path.parts or str(path) != path_text:
        raise BomError(f"BOM path is not normalized and repository-relative: {path_text!r}")
    return path_text


def require_string(value: object, field: str) -> str:
    """Return a nonempty string field or reject."""

    if not isinstance(value, str) or not value.strip():
        raise BomError(f"{field} must be a nonempty string")
    return value


def require_string_list(value: object, field: str) -> tuple[str, ...]:
    """Return a nonempty tuple of nonempty strings."""

    if not isinstance(value, list) or not value:
        raise BomError(f"{field} must be a nonempty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise BomError(f"{field} contains an empty or non-string value")
    return tuple(value)


def decode_json_strict(source: str) -> object:
    """Decode JSON while rejecting duplicate object keys at every depth."""

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        decoded: dict[str, object] = {}
        for key, value in pairs:
            if key in decoded:
                raise BomError(f"duplicate JSON object key: {key!r}")
            decoded[key] = value
        return decoded

    return json.loads(source, object_pairs_hook=unique_object)


def validate_references(
    references: Sequence[str], field: str, repository_root: Path
) -> list[str]:
    """Return sorted, live repository-relative evidence references."""

    normalized: list[str] = []
    for reference in references:
        path_text = normalize_path(reference)
        path = repository_root / path_text
        if not path.is_file():
            raise BomError(f"{field} references missing file: {path_text}")
        if path.is_symlink():
            raise BomError(f"{field} references a symlink: {path_text}")
        normalized.append(path_text)
    if len(normalized) != len(set(normalized)):
        raise BomError(f"{field} contains duplicate references")
    return sorted(normalized)
