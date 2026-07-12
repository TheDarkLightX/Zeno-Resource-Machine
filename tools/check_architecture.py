"""Enforce the current inward-only Rust workspace dependency graph."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
POLICY_PUBLIC_API_ALLOWLIST = ROOT / "tools/policy_public_api_allowlist.json"
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
    "crates/zrm-policy/src/cost/fuzz_assertions.rs",
    "crates/zrm-policy/src/error.rs",
    "crates/zrm-policy/src/lib.rs",
    "crates/zrm-policy/src/verifier.rs",
)

PUBLIC_FUNCTION_ALLOWLIST = {
    "cost.rs": {
        "artifact_byte_units",
        "artifact_len",
        "backend_family_id",
        "base_units",
        "canonical_statement_len",
        "label",
        "max_charge_units",
        "new",
        "reserved_output_byte_units",
        "rows_root",
        "schema_version",
        "statement_byte_units",
        "units",
    },
    "fuzz_assertions.rs": {"fuzz_assert_untrusted_candidate_cost_invariants"},
    "error.rs": set(),
    "lib.rs": set(),
    "verifier.rs": {
        "as_candidate",
        "backend_family_id",
        "domain_id",
        "is_valid_at",
        "machine_id",
        "max_artifact_bytes",
        "max_public_input_bytes",
        "max_public_output_bytes",
        "max_verifier_cost_units",
        "proof_mode",
        "verifier_cost_model_id",
        "verifier_policy_id",
    },
}

PUBLIC_FUNCTION_SIGNATURE_ALLOWLIST = {
    "cost.rs": {
        "CandidateVerifierCostQuoteRequestV1::pub const fn artifact_len(&self) -> u64",
        "CandidateVerifierCostQuoteRequestV1::pub const fn canonical_statement_len(&self) -> u64",
        "CandidateVerifierCostQuoteV1::pub const fn units(self) -> u64",
        "VerifierCostErrorV1::pub const fn label(self) -> &'static str",
        "VerifierCostModelV1::pub const fn max_charge_units(&self) -> u64",
        "VerifierCostModelV1::pub const fn rows_root(&self) -> VerifierCostRowsRoot",
        "VerifierCostModelV1::pub const fn schema_version(&self) -> u16",
        "VerifierCostRowV1::pub const fn artifact_byte_units(&self) -> u64",
        "VerifierCostRowV1::pub const fn backend_family_id(&self) -> BackendFamilyId",
        "VerifierCostRowV1::pub const fn base_units(&self) -> u64",
        "VerifierCostRowV1::pub const fn new(candidate: VerifierCostRowCandidateV1) -> Self",
        "VerifierCostRowV1::pub const fn reserved_output_byte_units(&self) -> u64",
        "VerifierCostRowV1::pub const fn statement_byte_units(&self) -> u64",
    },
    "fuzz_assertions.rs": {
        "<module>::pub fn fuzz_assert_untrusted_candidate_cost_invariants(data: &[u8])"
    },
    "error.rs": set(),
    "lib.rs": set(),
    "verifier.rs": {
        "VerifierPolicyV1::pub const fn as_candidate(&self) -> VerifierPolicyCandidateV1",
        "VerifierPolicyV1::pub const fn backend_family_id(&self) -> BackendFamilyId",
        "VerifierPolicyV1::pub const fn domain_id(&self) -> DomainId",
        "VerifierPolicyV1::pub const fn is_valid_at(&self, epoch: u64) -> bool",
        "VerifierPolicyV1::pub const fn machine_id(&self) -> MachineId",
        "VerifierPolicyV1::pub const fn max_artifact_bytes(&self) -> u64",
        "VerifierPolicyV1::pub const fn max_public_input_bytes(&self) -> u64",
        "VerifierPolicyV1::pub const fn max_public_output_bytes(&self) -> u64",
        "VerifierPolicyV1::pub const fn max_verifier_cost_units(&self) -> u64",
        "VerifierPolicyV1::pub const fn proof_mode(&self) -> ProofModeV1",
        "VerifierPolicyV1::pub const fn verifier_cost_model_id(&self) -> VerifierCostModelId",
        "VerifierPolicyV1::pub const fn verifier_policy_id(&self) -> VerifierPolicyId",
    },
}

PUBLIC_VALUE_ALLOWLIST = {
    "cost.rs": {"<module>::pub const VERIFIER_COST_MODEL_SCHEMA_V1: u16 = 1;"},
    "fuzz_assertions.rs": set(),
    "error.rs": set(),
    "lib.rs": {"<module>::pub const POLICY_SCHEMA_VERSION_V1: u16 = 1;"},
    "verifier.rs": set(),
}

PUBLIC_TYPE_ALLOWLIST = {
    "cost.rs": {
        "VerifierCostErrorV1",
        "VerifierCostModelCandidateV1",
        "VerifierCostModelV1",
        "VerifierCostRowCandidateV1",
        "VerifierCostRowV1",
    },
    "fuzz_assertions.rs": set(),
    "error.rs": {
        "LimitFieldV1",
        "PolicyObjectV1",
        "PolicyValidationErrorV1",
        "ResourceDimensionErrorV1",
    },
    "lib.rs": set(),
    "verifier.rs": {"ProofModeV1", "VerifierPolicyCandidateV1", "VerifierPolicyV1"},
}

PUBLIC_REEXPORT_ALLOWLIST = {
    "cost.rs": {"fuzz_assert_untrusted_candidate_cost_invariants"},
    "fuzz_assertions.rs": set(),
    "error.rs": set(),
    "lib.rs": {
        "AccountingModeV1",
        "AdmissionModeV1",
        "AdmissionPolicyV1",
        "DataAvailabilityRequirementV1",
        "LimitFieldV1",
        "MachinePolicyCandidateV1",
        "MachinePolicyV1",
        "PolicyLimitsCandidateV1",
        "PolicyLimitsV1",
        "PolicyObjectV1",
        "PolicyValidationErrorV1",
        "ProofModeV1",
        "ResourceDimensionErrorV1",
        "ResourceKindPolicyCandidateV1",
        "ResourceKindPolicyV1",
        "ValidationContextCandidateV1",
        "ValidationContextV1",
        "ValidityWindowV1",
        "VerifierCostErrorV1",
        "VerifierCostModelCandidateV1",
        "VerifierCostModelV1",
        "VerifierCostRowCandidateV1",
        "VerifierCostRowV1",
        "VerifierPolicyCandidateV1",
        "VerifierPolicyV1",
        "fuzz_assert_untrusted_candidate_cost_invariants",
    },
    "verifier.rs": set(),
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


def public_authority_api_failures(sources: dict[str, str]) -> list[str]:
    """Enforce the exact reviewed public surface of authority-adjacent modules."""

    failures: list[str] = []
    public_function = re.compile(
        r'^\s*pub\s+(?:(?:const|async|unsafe)\s+|extern(?:\s+"[^"]+")?\s+)*fn\s+([A-Za-z0-9_]+)\s*\(',
        re.MULTILINE,
    )
    public_type = re.compile(
        r"^\s*pub\s+(?:struct|enum|union|type|trait)\s+([A-Za-z0-9_]+)\b",
        re.MULTILINE,
    )
    for path, source in sources.items():
        role = Path(path).name
        if role not in PUBLIC_FUNCTION_ALLOWLIST:
            failures.append(f"{path} has no reviewed authority API allowlist")
            continue
        functions = Counter(public_function.findall(source))
        function_signatures = public_function_signatures(source)
        types = Counter(public_type.findall(source))
        values = public_value_signatures(source)
        reexports = public_reexport_names(source)
        failures.extend(
            exact_surface_failures(
                path,
                "public functions",
                functions,
                Counter(PUBLIC_FUNCTION_ALLOWLIST[role]),
            )
        )
        failures.extend(
            exact_surface_failures(
                path,
                "public function signatures",
                function_signatures,
                Counter(PUBLIC_FUNCTION_SIGNATURE_ALLOWLIST[role]),
            )
        )
        failures.extend(
            exact_surface_failures(
                path, "public types", types, Counter(PUBLIC_TYPE_ALLOWLIST[role])
            )
        )
        failures.extend(
            exact_surface_failures(
                path,
                "public const/static values",
                values,
                Counter(PUBLIC_VALUE_ALLOWLIST[role]),
            )
        )
        failures.extend(
            exact_surface_failures(
                path,
                "public re-exports",
                reexports,
                Counter(PUBLIC_REEXPORT_ALLOWLIST[role]),
            )
        )
        for name in set(functions) & QUARANTINED_AUTHORITY_METHODS:
            failures.append(f"{path} publicly exposes quarantined method {name}")
        for name in set(types) & QUARANTINED_AUTHORITY_TYPES:
            failures.append(f"{path} publicly exposes quarantined type {name}")
        for name in set(reexports) & QUARANTINED_AUTHORITY_TYPES:
            failures.append(f"{path} publicly re-exports quarantined type {name}")

    failures.extend(fuzz_assertion_surface_failures(sources))
    return failures


def exact_surface_failures(
    path: str,
    kind: str,
    actual: Counter[str],
    expected: Counter[str],
) -> list[str]:
    """Return additions and removals from one reviewed API allowlist."""

    failures: list[str] = []
    unexpected = list((actual - expected).elements())
    missing = list((expected - actual).elements())
    if unexpected:
        failures.append(f"{path} has unreviewed {kind} {sorted(unexpected)}")
    if missing:
        failures.append(f"{path} is missing reviewed {kind} {sorted(missing)}")
    return failures


def public_reexport_names(source: str) -> Counter[str]:
    """Extract identifiers exported by line-anchored Rust `pub use` statements."""

    statements = re.findall(r"^\s*pub\s+use\s+([^;]+);", source, re.MULTILINE | re.DOTALL)
    names: Counter[str] = Counter()
    for statement in statements:
        if "{" in statement:
            body = statement.split("{", 1)[1].rsplit("}", 1)[0]
            for part in body.split(","):
                if part.strip():
                    names[part.strip().split(" as ")[-1]] += 1
        else:
            name = statement.strip().split(" as ")[-1].rsplit("::", 1)[-1]
            names[name] += 1
    return names


def public_function_signatures(source: str) -> Counter[str]:
    """Return owner-qualified, whitespace-normalized public function signatures."""

    pattern = re.compile(
        r'^\s*pub\s+(?:(?:const|async|unsafe)\s+|extern(?:\s+"[^"]+")?\s+)*fn\s+[A-Za-z0-9_]+\s*\(',
        re.MULTILINE,
    )
    owners = impl_owners_by_line(source)
    signatures: Counter[str] = Counter()
    for match in pattern.finditer(source):
        end = source.find("{", match.start())
        if end < 0:
            end = source.find(";", match.start())
        if end < 0:
            signatures["<unterminated-public-function>"] += 1
            continue
        signature = " ".join(source[match.start() : end].split())
        line_number = source.count("\n", 0, match.start()) + 1
        owner = owners.get(line_number, "<module>")
        signatures[f"{owner}::{signature}"] += 1
    return signatures


def public_value_signatures(source: str) -> Counter[str]:
    """Return owner-qualified public const/static declarations, including pointers."""

    pattern = re.compile(
        r"^\s*pub\s+(?:const|static(?:\s+mut)?)\s+[A-Za-z0-9_]+\s*:[^;]+;",
        re.MULTILINE,
    )
    owners = impl_owners_by_line(source)
    values: Counter[str] = Counter()
    for match in pattern.finditer(source):
        signature = " ".join(match.group(0).split())
        line_number = source.count("\n", 0, match.start()) + 1
        owner = owners.get(line_number, "<module>")
        values[f"{owner}::{signature}"] += 1
    return values


def impl_owners_by_line(source: str) -> dict[int, str]:
    """Map lines inside simple Rust impl blocks to their owning type."""

    owners: dict[int, str] = {}
    active: list[tuple[int, str]] = []
    depth = 0
    impl_pattern = re.compile(
        r"^\s*impl(?:<[^>]+>)?\s+(?:[^\s]+\s+for\s+)?([A-Za-z0-9_]+)(?:<[^>]+>)?\s*\{"
    )
    for line_number, line in enumerate(source.splitlines(), start=1):
        code = line.split("//", 1)[0]
        match = impl_pattern.match(code)
        if match is not None:
            active.append((depth + code.count("{") - code.count("}"), match.group(1)))
        if active:
            owners[line_number] = active[-1][1]
        depth += code.count("{") - code.count("}")
        while active and depth < active[-1][0]:
            active.pop()
    return owners


def fuzz_assertion_surface_failures(sources: dict[str, str]) -> list[str]:
    """Require the sole fuzz export to be cfg-gated, raw-input-only, and unit-returning."""

    failures: list[str] = []
    name = "fuzz_assert_untrusted_candidate_cost_invariants"
    assertion_source = next(
        (source for path, source in sources.items() if Path(path).name == "fuzz_assertions.rs"),
        None,
    )
    if assertion_source is not None and not re.search(
        rf"^pub\s+fn\s+{name}\s*\(\s*data:\s*&\[u8\]\s*\)\s*\{{",
        assertion_source,
        re.MULTILINE,
    ):
        failures.append(
            "fuzz_assertions.rs must expose exactly a &[u8] assertion sink with implicit unit return"
        )
    for role in ("cost.rs", "lib.rs"):
        source = next(
            (value for path, value in sources.items() if Path(path).name == role),
            None,
        )
        if source is not None and not re.search(
            rf"#\[cfg\(fuzzing\)\]\s*(?:#\[doc\(hidden\)\]\s*)?pub\s+use\s+[^;]*\b{name}\b[^;]*;",
            source,
            re.MULTILINE,
        ):
            failures.append(f"{role} must re-export the assertion sink only under cfg(fuzzing)")
    return failures


def authority_api_failures(root: Path) -> list[str]:
    """Read policy sources and enforce the fail-closed public API quarantine."""

    sources = {path: (root / path).read_text(encoding="utf-8") for path in AUTHORITY_SOURCE_PATHS}
    return public_authority_api_failures(sources)


def compiler_public_api_failures(root: Path) -> list[str]:
    """Compare pinned compiler-derived public API JSON in default and fuzz profiles."""

    try:
        allowlist = json.loads(POLICY_PUBLIC_API_ALLOWLIST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"unable to read compiler public API allowlist: {error}"]
    if allowlist.get("schema") != "zrm/compiler-public-api-allowlist/v1":
        return ["compiler public API allowlist has an unexpected schema"]
    package = allowlist.get("package")
    toolchain = allowlist.get("toolchain")
    format_version = allowlist.get("rustdoc_format_version")
    profiles = allowlist.get("profiles")
    if not isinstance(package, str) or not isinstance(toolchain, str):
        return ["compiler public API package and toolchain must be strings"]
    if not isinstance(format_version, int) or not isinstance(profiles, dict):
        return ["compiler public API format version or profiles are invalid"]
    if set(profiles) != {"default", "fuzzing"}:
        return ["compiler public API profiles must be exactly default and fuzzing"]

    failures: list[str] = []
    crate_filename = package.replace("-", "_") + ".json"
    for profile_name in ("default", "fuzzing"):
        profile = profiles[profile_name]
        if not isinstance(profile, dict):
            failures.append(f"compiler public API profile {profile_name} is not an object")
            continue
        flags = profile.get("rustdoc_flags")
        expected_digest = profile.get("sha256")
        if not isinstance(flags, list) or not all(isinstance(flag, str) for flag in flags):
            failures.append(f"compiler public API profile {profile_name} has invalid flags")
            continue
        if not isinstance(expected_digest, str) or re.fullmatch(r"[0-9a-f]{64}", expected_digest) is None:
            failures.append(f"compiler public API profile {profile_name} has invalid SHA-256")
            continue

        target_dir = root / "target" / "policy-public-api" / profile_name
        environment = os.environ.copy()
        environment["CARGO_TARGET_DIR"] = str(target_dir)
        environment["RUSTC_BOOTSTRAP"] = "1"
        environment["RUSTDOCFLAGS"] = " ".join(flags)
        environment.pop("RUSTFLAGS", None)
        command = [
            "cargo",
            f"+{toolchain}",
            "rustdoc",
            "-p",
            package,
            "--lib",
            "--locked",
            "--",
            "-Z",
            "unstable-options",
            "--output-format",
            "json",
            "--document-hidden-items",
        ]
        result = subprocess.run(
            command,
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(
                f"compiler public API profile {profile_name} failed: {result.stderr.strip()}"
            )
            continue
        output_path = target_dir / "doc" / crate_filename
        try:
            raw = output_path.read_bytes()
            rustdoc = json.loads(raw)
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"compiler public API profile {profile_name} is unreadable: {error}")
            continue
        if rustdoc.get("format_version") != format_version:
            failures.append(
                f"compiler public API profile {profile_name} format changed from {format_version}"
            )
        if rustdoc.get("includes_private") is not False:
            failures.append(f"compiler public API profile {profile_name} unexpectedly includes private items")
        actual_digest = hashlib.sha256(raw).hexdigest()
        if actual_digest != expected_digest:
            failures.append(
                f"compiler public API profile {profile_name} digest {actual_digest} "
                f"does not match reviewed {expected_digest}"
            )
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
    failures.extend(authority_api_failures(ROOT))
    failures.extend(compiler_public_api_failures(ROOT))

    if failures:
        print("architecture check failed: " + "; ".join(failures), file=sys.stderr)
        return 1
    print(
        "architecture check passed: dependency allowlists match and "
        "source plus compiler public API allowlists quarantine unauthenticated authority-shaped APIs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
