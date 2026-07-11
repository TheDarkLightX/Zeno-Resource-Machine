"""Enforce the current inward-only Rust workspace dependency graph."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ALLOWED_INTERNAL_DEPENDENCIES = {
    "zrm-types": set(),
    "zrm-crypto": {"zrm-types"},
    "zrm-codec": {"zrm-crypto", "zrm-types"},
    "zrm-policy": {"zrm-crypto", "zrm-types"},
}
ALLOWED_EXTERNAL_DEPENDENCIES = {
    "zrm-types": set(),
    "zrm-crypto": {"sha2"},
    "zrm-codec": set(),
    "zrm-policy": set(),
}


def dependency_failures(package: dict[str, object]) -> list[str]:
    """Return undeclared or missing dependency edges for one workspace crate."""

    package_name = package["name"]
    if not isinstance(package_name, str):
        return ["workspace package has a non-string name"]
    dependencies = package["dependencies"]
    if not isinstance(dependencies, list):
        return [f"{package_name} dependencies are not a list"]
    declared = {
        dependency["name"]
        for dependency in dependencies
        if isinstance(dependency, dict) and isinstance(dependency.get("name"), str)
    }
    allowed = ALLOWED_INTERNAL_DEPENDENCIES[package_name] | ALLOWED_EXTERNAL_DEPENDENCIES[package_name]
    if declared == allowed:
        return []
    failures: list[str] = []
    unexpected = declared - allowed
    missing = allowed - declared
    if unexpected:
        failures.append(f"{package_name} has undeclared dependency edges {sorted(unexpected)}")
    if missing:
        failures.append(f"{package_name} is missing declared dependency edges {sorted(missing)}")
    return failures


def main() -> int:
    """Read locked Cargo metadata and reject undeclared inward edges."""

    command = ["cargo", "metadata", "--format-version", "1", "--locked", "--no-deps"]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"architecture check failed: {result.stderr.strip()}", file=sys.stderr)
        return 1

    metadata = json.loads(result.stdout)
    workspace_ids = set(metadata["workspace_members"])
    packages = {package["id"]: package for package in metadata["packages"] if package["id"] in workspace_ids}
    names = {package["name"] for package in packages.values()}
    expected = set(ALLOWED_INTERNAL_DEPENDENCIES)
    if names != expected:
        print(f"architecture check failed: workspace crates {sorted(names)} != declared {sorted(expected)}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for package in packages.values():
        failures.extend(dependency_failures(package))

    if failures:
        print("architecture check failed: " + "; ".join(failures), file=sys.stderr)
        return 1
    print("architecture check passed: exact internal and external dependency allowlists match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
