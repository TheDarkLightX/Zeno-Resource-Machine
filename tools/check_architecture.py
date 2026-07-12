"""Enforce the current inward-only Rust workspace dependency graph."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ALLOWED_INTERNAL_DEPENDENCIES = {
    "zrm-types": set(),
    "zrm-crypto": {"zrm-types"},
    "zrm-codec": {"zrm-types"},
    "zrm-kernel": {"zrm-codec", "zrm-policy", "zrm-types"},
    "zrm-policy": {"zrm-crypto", "zrm-types"},
}
ALLOWED_EXTERNAL_DEPENDENCIES = {
    "zrm-types": set(),
    "zrm-crypto": {"sha2"},
    "zrm-codec": {"sha2"},
    "zrm-kernel": set(),
    "zrm-policy": set(),
}

QUARANTINED_AUTHORITY_METHODS = {
    "admission_reservation_quote_request",
    "candidate_admission_reservation_request",
    "candidate_cost_quote_request",
    "check_untrusted_admission_candidate_shape",
    "check_untrusted_verifier_candidate_shape",
    "compute_quote",
    "compute_untrusted_candidate_quote",
    "cost_quote_request",
    "validate_admission_verifier_candidate",
    "validate_verifier_candidate_compatibility",
}
QUARANTINED_AUTHORITY_TYPES = {
    "CandidateVerifierCostQuoteRequestV1",
    "CandidateVerifierCostQuoteV1",
    "VerifierCompatibilityErrorV1",
    "VerifierCostQuoteRequestV1",
    "VerifierCostQuoteV1",
}
AUTHORITY_SOURCE_PATHS = (
    "crates/zrm-policy/src/cost.rs",
    "crates/zrm-policy/src/error.rs",
    "crates/zrm-policy/src/lib.rs",
    "crates/zrm-policy/src/verifier.rs",
)


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


def public_authority_api_failures(sources: dict[str, str]) -> list[str]:
    """Reject authority-shaped candidate operations from the default public API."""

    failures: list[str] = []
    public_function = re.compile(r"\bpub\s+(?:const\s+)?fn\s+([A-Za-z0-9_]+)\s*\(")
    public_type = re.compile(r"\bpub\s+(?:struct|enum)\s+([A-Za-z0-9_]+)\b")
    public_use = re.compile(r"\bpub\s+use\s+.*?;", re.DOTALL)
    for path, source in sources.items():
        for name in public_function.findall(source):
            if name in QUARANTINED_AUTHORITY_METHODS:
                failures.append(f"{path} publicly exposes quarantined method {name}")
        for name in public_type.findall(source):
            if name in QUARANTINED_AUTHORITY_TYPES:
                failures.append(f"{path} publicly exposes quarantined type {name}")
        for statement in public_use.findall(source):
            for name in QUARANTINED_AUTHORITY_TYPES:
                if re.search(rf"\b{re.escape(name)}\b", statement):
                    failures.append(f"{path} publicly re-exports quarantined type {name}")
    return failures


def authority_api_failures(root: Path) -> list[str]:
    """Read policy sources and enforce the fail-closed public API quarantine."""

    sources = {path: (root / path).read_text(encoding="utf-8") for path in AUTHORITY_SOURCE_PATHS}
    return public_authority_api_failures(sources)


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
    failures.extend(authority_api_failures(ROOT))

    if failures:
        print("architecture check failed: " + "; ".join(failures), file=sys.stderr)
        return 1
    print(
        "architecture check passed: dependency allowlists match and "
        "unauthenticated authority-shaped APIs are quarantined"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
