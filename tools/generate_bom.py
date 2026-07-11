"""Generate deterministic ZRM-native Cargo SBOM and cryptography CBOM reports."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

if __package__:
    from .bom_cbom import build_cbom
    from .bom_common import (
        MAX_INPUT_BYTES,
        ROOT,
        BomError,
        WorkspaceSnapshot,
        canonical_json,
        decode_json_strict,
        normalize_path,
    )
    from .bom_sbom import apply_build_surface_policy, build_sbom
else:
    from bom_cbom import build_cbom
    from bom_common import (
        MAX_INPUT_BYTES,
        ROOT,
        BomError,
        WorkspaceSnapshot,
        canonical_json,
        decode_json_strict,
        normalize_path,
    )
    from bom_sbom import apply_build_surface_policy, build_sbom


# Stable compatibility aliases used by focused tests and downstream tooling.
_decode_json_strict = decode_json_strict


def _read_bounded(path: Path, description: str) -> bytes:
    """Read a regular non-symlink file under the fixed tooling ceiling."""

    if path.is_symlink() or not path.is_file():
        raise BomError(f"{description} is absent or a symlink")
    payload = path.read_bytes()
    if len(payload) > MAX_INPUT_BYTES:
        raise BomError(f"{description} exceeds the one-megabyte input ceiling")
    return payload


def _capture_workspace(scope: str, manifest_path: str, lockfile_path: str) -> WorkspaceSnapshot:
    """Run fixed offline locked Cargo metadata for one workspace."""

    normalized_manifest = normalize_path(manifest_path)
    normalized_lockfile = normalize_path(lockfile_path)
    command = [
        "cargo",
        "metadata",
        "--format-version",
        "1",
        "--locked",
        "--offline",
        "--all-features",
        "--manifest-path",
        normalized_manifest,
    ]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise BomError(f"{scope} Cargo metadata failed: {stderr}")
    if len(result.stdout) > MAX_INPUT_BYTES:
        raise BomError(f"{scope} Cargo metadata exceeds the one-megabyte input ceiling")
    try:
        metadata = decode_json_strict(result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BomError(f"cannot decode {scope} Cargo metadata") from error
    if not isinstance(metadata, dict):
        raise BomError(f"{scope} Cargo metadata root must be an object")
    return WorkspaceSnapshot(
        scope=scope,
        manifest_path=normalized_manifest,
        lockfile_path=normalized_lockfile,
        metadata=metadata,
        lockfile_bytes=_read_bounded(ROOT / normalized_lockfile, f"{scope} Cargo lockfile"),
    )


def _read_policy(path_text: str, description: str) -> object:
    """Read strict bounded repository policy JSON."""

    normalized = normalize_path(path_text)
    try:
        return decode_json_strict(_read_bounded(ROOT / normalized, description).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BomError(f"cannot decode {description}") from error


def _write_report(path_text: str, payload: str) -> None:
    """Write deterministic JSON only beneath the repository target directory."""

    normalized = normalize_path(path_text)
    relative_path = PurePosixPath(normalized)
    if (
        len(relative_path.parts) < 2
        or relative_path.parts[0] != "target"
        or relative_path.suffix != ".json"
    ):
        raise BomError("BOM reports may be written only as JSON beneath target/")
    path = ROOT / normalized
    target_root = ROOT / "target"
    for parent in path.parents:
        if parent == ROOT:
            break
        if parent.exists() and parent.is_symlink():
            raise BomError(f"BOM report parent is a symlink: {parent.relative_to(ROOT)}")
    if path.exists() and path.is_symlink():
        raise BomError(f"BOM report path is a symlink: {normalized}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.resolve().is_relative_to(target_root.resolve()):
        raise BomError("BOM report path resolves outside target/")
    path.write_text(payload, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Capture both Cargo workspaces and write validated SBOM/CBOM reports."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="supply-chain/cryptography.json")
    parser.add_argument("--build-surface", default="supply-chain/build_surface.json")
    parser.add_argument("--sbom", default="target/zrm-sbom.json")
    parser.add_argument("--cbom", default="target/zrm-cbom.json")
    arguments = parser.parse_args(argv)
    try:
        sbom = apply_build_surface_policy(
            build_sbom(
                [
                    _capture_workspace("root", "Cargo.toml", "Cargo.lock"),
                    _capture_workspace("fuzz", "fuzz/Cargo.toml", "fuzz/Cargo.lock"),
                ]
            ),
            _read_policy(arguments.build_surface, "build-surface policy"),
        )
        cbom = build_cbom(
            _read_policy(arguments.registry, "cryptography registry"), sbom
        )
        _write_report(arguments.sbom, canonical_json(sbom))
        _write_report(arguments.cbom, canonical_json(cbom))
    except (BomError, OSError, subprocess.SubprocessError) as error:
        print(f"BOM generation failed: {error}", file=sys.stderr)
        return 1
    print(
        "BOM generation passed: "
        f"{sbom['summary']['component_count']} source component(s), "
        f"{sbom['summary']['dependency_edge_count']} edge(s), "
        f"{cbom['summary']['component_count']} cryptography component(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
