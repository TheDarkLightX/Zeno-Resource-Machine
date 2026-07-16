"""Validate the machine-readable ZRM CBC conformance matrix."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "CONFORMANCE_MATRIX.json"
PACKAGE_MANIFEST_PATH = ROOT / "PACKAGE_MANIFEST.json"
VALID_STATUSES = {
    "specified",
    "implemented_partial",
    "implemented",
    "verified_scoped",
    "blocked",
    "not_applicable",
}
VALID_LAYERS = {
    "unrepresentable",
    "guarded_transition",
    "detected_at_commit",
    "detected_by_evidence",
    "bounded_blast_radius",
}
REFERENCE_FIELDS = (
    "implementation_refs",
    "test_refs",
    "formal_refs",
    "evidence_refs",
    "normative_refs",
)
REQUIRED_TEXT_FIELDS = (
    "id",
    "title",
    "severity",
    "status",
    "defense_layer",
    "disaster_state",
    "construction_rule",
    "next_action",
    "non_claim",
    "target_level",
)


class ConformanceError(ValueError):
    """Raised when the conformance matrix violates its declared contract."""


def github_anchor(heading: str) -> str:
    """Return the base GitHub-style anchor used by this repository's headings."""

    normalized = re.sub(r"[\t\n ]+", "-", heading.strip().lower())
    return "".join(char for char in normalized if char.isalnum() or char in "-_")


def markdown_anchors(path: Path) -> set[str]:
    """Collect unique GitHub-style anchors from one Markdown file."""

    anchors: set[str] = set()
    counts: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if match is None:
            continue
        base = github_anchor(match.group(1))
        duplicate_index = counts[base]
        counts[base] += 1
        anchors.add(base if duplicate_index == 0 else f"{base}-{duplicate_index}")
    return anchors


def require(condition: bool, message: str) -> None:
    """Raise a typed validation error when ``condition`` is false."""

    if not condition:
        raise ConformanceError(message)


def require_string_list(value: Any, field: str, obligation_id: str) -> list[str]:
    """Validate and return one obligation string-list field."""

    require(isinstance(value, list), f"{obligation_id}.{field} must be a list")
    require(
        all(isinstance(item, str) and item for item in value),
        f"{obligation_id}.{field} must contain nonempty strings",
    )
    return value


def validate_reference(reference: str, obligation_id: str, anchors: dict[Path, set[str]]) -> None:
    """Validate a file or Markdown-anchor reference."""

    file_text, separator, anchor = reference.partition("#")
    relative_path = Path(file_text)
    require(not relative_path.is_absolute(), f"{obligation_id} reference must be repository-relative")
    require(".." not in relative_path.parts, f"{obligation_id} reference escapes repository root")
    referenced_path = (ROOT / relative_path).resolve()
    require(referenced_path.is_relative_to(ROOT.resolve()), f"{obligation_id} reference escapes repository root")
    require(referenced_path.is_file(), f"{obligation_id} references missing file {file_text}")
    if separator:
        require(file_text.endswith(".md"), f"{obligation_id} anchor target is not Markdown: {reference}")
        known = anchors.setdefault(referenced_path, markdown_anchors(referenced_path))
        require(anchor in known, f"{obligation_id} references missing anchor {reference}")


def validate_status(obligation: dict[str, Any]) -> None:
    """Enforce the matrix's machine-readable promotion rules."""

    obligation_id = obligation["id"]
    status = obligation["status"]
    implementation_refs = obligation["implementation_refs"]
    test_refs = obligation["test_refs"]
    formal_refs = obligation["formal_refs"]
    evidence_refs = obligation["evidence_refs"]
    dependencies = obligation["blocking_dependencies"]

    if status == "specified":
        require(
            not implementation_refs and not test_refs and not formal_refs and not evidence_refs,
            f"{obligation_id} specified status cannot carry implementation evidence",
        )
    elif status == "implemented_partial":
        require(implementation_refs and test_refs, f"{obligation_id} partial status needs implementation and tests")
    elif status == "implemented":
        require(implementation_refs and test_refs, f"{obligation_id} implemented status needs implementation and tests")
        require(not dependencies, f"{obligation_id} implemented status cannot have blocking dependencies")
    elif status == "verified_scoped":
        require(implementation_refs and test_refs, f"{obligation_id} verified status needs implementation and tests")
        require(formal_refs or evidence_refs, f"{obligation_id} verified status needs formal or replay evidence")
        require(not dependencies, f"{obligation_id} verified status cannot have blocking dependencies")
    elif status == "blocked":
        require(dependencies, f"{obligation_id} blocked status needs a blocking dependency")
    elif status == "not_applicable":
        require(evidence_refs, f"{obligation_id} not-applicable status needs an approved rationale")


def validate_dependency_graph(obligations: list[dict[str, Any]]) -> None:
    """Require known dependencies and an acyclic CBC graph."""

    identifiers = {obligation["id"] for obligation in obligations}
    graph: dict[str, list[str]] = {}
    for obligation in obligations:
        obligation_id = obligation["id"]
        dependencies = obligation["blocking_dependencies"]
        require(obligation_id not in dependencies, f"{obligation_id} cannot depend on itself")
        unknown = set(dependencies) - identifiers
        require(not unknown, f"{obligation_id} has unknown dependencies: {sorted(unknown)}")
        graph[obligation_id] = dependencies

    visited: set[str] = set()
    active: set[str] = set()

    def visit(identifier: str) -> None:
        require(identifier not in active, f"CBC dependency cycle reaches {identifier}")
        if identifier in visited:
            return
        active.add(identifier)
        for dependency in graph[identifier]:
            visit(dependency)
        active.remove(identifier)
        visited.add(identifier)

    for identifier in graph:
        visit(identifier)


def validate_promotion_boundary(data: dict[str, Any], obligations: list[dict[str, Any]]) -> None:
    """Require top-level public claims to agree with obligation promotion state."""

    boundary = data.get("promotion_boundary")
    require(isinstance(boundary, dict), "promotion_boundary must be an object")
    public_claim = boundary.get("public_implementation_claim_allowed")
    production_ready = boundary.get("production_ready")
    current_level = boundary.get("current_level")
    require(isinstance(public_claim, bool), "public implementation claim flag must be boolean")
    require(isinstance(production_ready, bool), "production_ready must be boolean")
    require(isinstance(current_level, str), "current_level must be a string")

    statuses = {obligation["status"] for obligation in obligations}
    if current_level == "design-only":
        require(statuses == {"specified"}, "design-only posture cannot carry implementation evidence")
        require(data.get("status") == "design_obligations_only", "design-only matrix status is inconsistent")
        require(not public_claim, "design-only posture cannot allow implementation claims")
    elif current_level == "ZRM-L0-candidate":
        require("implemented_partial" in statuses, "candidate posture needs partial implementation evidence")
        require(
            data.get("status") == "wp0_wp1_candidate_awaiting_human_review",
            "candidate matrix status is inconsistent",
        )
        require(not public_claim, "unreviewed candidate cannot allow public implementation claims")
    else:
        require(re.fullmatch(r"ZRM-L[0-5]", current_level) is not None, "unknown promoted conformance level")
        require(public_claim, "a promoted implementation level must enable scoped implementation claims")
        require(
            data.get("status") == "scoped_wp0_wp1_implementation",
            "promoted matrix status is inconsistent",
        )
        claim_scope = require_string_list(boundary.get("claim_scope"), "claim_scope", "promotion_boundary")
        require(bool(claim_scope), "promoted posture needs a nonempty claim scope")
        promotion_evidence = require_string_list(
            boundary.get("promotion_evidence"),
            "promotion_evidence",
            "promotion_boundary",
        )
        require(bool(promotion_evidence), "promoted posture needs promotion evidence")
        for reference in promotion_evidence:
            validate_reference(reference, "promotion_boundary", {})
        require(
            "implemented" in statuses or "verified_scoped" in statuses,
            "promoted posture needs promoted obligations",
        )

    if production_ready:
        require(public_claim and current_level == "ZRM-L5", "production requires a public ZRM-L5 posture")

    manifest = json.loads(PACKAGE_MANIFEST_PATH.read_text(encoding="utf-8"))
    require(data.get("updated_at") == manifest.get("date"), "matrix updated_at differs from package date")


def validate_matrix(data: dict[str, Any]) -> None:
    """Validate all schema, reference, status, and dependency obligations."""

    require(data.get("schema") == "zrm/cbc-conformance-matrix/v1", "unexpected matrix schema")
    require(data.get("version") == 1, "unexpected matrix version")
    obligations = data.get("obligations")
    require(isinstance(obligations, list), "obligations must be a list")
    expected_ids = [f"ZRM-CBC-{number:03d}" for number in range(1, 56)]
    actual_ids = [obligation.get("id") for obligation in obligations]
    require(actual_ids == expected_ids, "CBC identifiers must be unique and sequential from 001 through 055")

    anchors: dict[Path, set[str]] = {}
    for obligation in obligations:
        obligation_id = obligation["id"]
        for field in REQUIRED_TEXT_FIELDS:
            require(
                isinstance(obligation.get(field), str) and bool(obligation[field]),
                f"{obligation_id}.{field} must be a nonempty string",
            )
        require(obligation["status"] in VALID_STATUSES, f"{obligation_id} has invalid status")
        require(obligation["defense_layer"] in VALID_LAYERS, f"{obligation_id} has invalid defense layer")
        require(re.fullmatch(r"ZRM-L[0-5]", obligation["target_level"]) is not None, f"{obligation_id} has invalid target level")

        required_evidence = require_string_list(obligation.get("required_evidence"), "required_evidence", obligation_id)
        require(bool(required_evidence), f"{obligation_id} requires at least one evidence item")
        work_packages = require_string_list(obligation.get("work_packages"), "work_packages", obligation_id)
        require(
            all(re.fullmatch(r"WP(?:[0-9]|1[0-3])", item) is not None for item in work_packages),
            f"{obligation_id} has invalid work package",
        )
        require_string_list(obligation.get("blocking_dependencies"), "blocking_dependencies", obligation_id)

        for field in REFERENCE_FIELDS:
            references = require_string_list(obligation.get(field), field, obligation_id)
            if field == "normative_refs":
                require(bool(references), f"{obligation_id} needs a normative reference")
            for reference in references:
                validate_reference(reference, obligation_id, anchors)
        validate_status(obligation)

    validate_dependency_graph(obligations)
    validate_promotion_boundary(data, obligations)


def main() -> int:
    """Load and validate the repository's conformance matrix."""

    try:
        data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        require(isinstance(data, dict), "matrix root must be an object")
        validate_matrix(data)
    except (ConformanceError, json.JSONDecodeError, OSError) as error:
        print(f"conformance check failed: {error}", file=sys.stderr)
        return 1
    print("conformance check passed: 55 obligations, live anchors, valid promotion states, acyclic dependencies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
