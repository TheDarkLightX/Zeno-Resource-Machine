"""Enforce multi-axis code quality and explicit design-pattern decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:
    from .check_complexity import (
        MAX_SOURCE_FILE_BYTES,
        build_report as build_complexity_report,
    )
    from .rust_complexity import ComplexityError, _validate_relative_path
    from .rust_quality import (
        QUALITY_RULES,
        QualityError,
        QualityFinding,
        analyze_rust_quality,
    )
else:
    from check_complexity import (
        MAX_SOURCE_FILE_BYTES,
        build_report as build_complexity_report,
    )
    from rust_complexity import ComplexityError, _validate_relative_path
    from rust_quality import QUALITY_RULES, QualityError, QualityFinding, analyze_rust_quality


ROOT = Path(__file__).resolve().parent.parent
REPORT_SCHEMA = "zrm/code-quality-report/v1"
DESIGN_REGISTRY_SCHEMA = "zrm/design-pattern-decisions/v1"
DEFAULT_COMPLEXITY_EXCEPTIONS = "tools/complexity_exceptions.json"
DEFAULT_DESIGN_DECISIONS = "tools/design_pattern_decisions.json"
CURRENT_COMPLEXITY_WARNING_CEILING = 0
DECISION_ID = re.compile(r"ZRM-DESIGN-[0-9]{3}")
REQUIRED_DESIGN_PATTERNS = {
    "ZRM-DESIGN-001": "staged-typestate-authority-pipeline",
    "ZRM-DESIGN-002": "ports-and-adapters",
    "ZRM-DESIGN-003": "validated-value-objects",
    "ZRM-DESIGN-004": "manual-canonical-codec",
    "ZRM-DESIGN-005": "narrow-capability-ports",
}


def _require_nonempty_string(value: object, field: str) -> str:
    """Return a nonempty string or reject decision metadata."""

    if not isinstance(value, str) or not value.strip():
        raise QualityError(f"design decision field {field} must be a nonempty string")
    return value


def _require_string_list(value: object, field: str) -> tuple[str, ...]:
    """Return a nonempty tuple of nonempty strings."""

    if not isinstance(value, list) or not value:
        raise QualityError(f"design decision field {field} must be a nonempty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise QualityError(f"design decision field {field} contains an empty value")
    return tuple(value)


def _validate_live_references(
    references: Sequence[str], field: str, repository_root: Path
) -> tuple[str, ...]:
    """Validate repository-relative, non-symlink decision evidence paths."""

    normalized: list[str] = []
    for reference in references:
        try:
            path_text = _validate_relative_path(reference)
        except ComplexityError as error:
            raise QualityError(str(error)) from error
        path = repository_root / path_text
        if not path.is_file():
            raise QualityError(f"design decision {field} references missing file: {path_text}")
        if path.is_symlink():
            raise QualityError(f"design decision {field} references a symlink: {path_text}")
        normalized.append(path_text)
    return tuple(normalized)


def validate_design_decisions(
    registry: object, repository_root: Path = ROOT
) -> tuple[dict[str, object], ...]:
    """Validate the complete required design-pattern decision register."""

    if not isinstance(registry, dict) or set(registry) != {"schema", "decisions"}:
        raise QualityError("design registry must contain exactly schema and decisions")
    if registry.get("schema") != DESIGN_REGISTRY_SCHEMA:
        raise QualityError("unexpected design-pattern decision schema")
    decisions = registry.get("decisions")
    if not isinstance(decisions, list):
        raise QualityError("design decisions must be a list")
    required_fields = {
        "id",
        "pattern",
        "applies_to",
        "problem",
        "selected_because",
        "alternatives_considered",
        "tradeoffs",
        "normative_refs",
        "enforcement_refs",
        "review_triggers",
        "review_scope",
        "review_status",
        "review_ref",
    }
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    for decision in decisions:
        if not isinstance(decision, dict) or set(decision) != required_fields:
            raise QualityError("each design decision must contain the exact v1 fields")
        decision_id = _require_nonempty_string(decision.get("id"), "id")
        if DECISION_ID.fullmatch(decision_id) is None:
            raise QualityError(f"invalid design decision ID: {decision_id!r}")
        if decision_id in seen:
            raise QualityError(f"duplicate design decision: {decision_id}")
        seen.add(decision_id)
        pattern = _require_nonempty_string(decision.get("pattern"), "pattern")
        expected_pattern = REQUIRED_DESIGN_PATTERNS.get(decision_id)
        if expected_pattern is None or pattern != expected_pattern:
            raise QualityError(f"unexpected required pattern for {decision_id}: {pattern!r}")
        alternatives = _require_string_list(
            decision.get("alternatives_considered"), "alternatives_considered"
        )
        if not any("no additional pattern" in alternative.lower() for alternative in alternatives):
            raise QualityError(
                f"design decision {decision_id} must consider the no-additional-pattern option"
            )
        review_scope = _require_nonempty_string(
            decision.get("review_scope"), "review_scope"
        )
        review_status = _require_nonempty_string(
            decision.get("review_status"), "review_status"
        )
        review_ref = decision.get("review_ref")
        if review_scope != "technical" or review_status != "ai-reviewed":
            raise QualityError(
                f"design decision {decision_id} requires technical AI review evidence"
            )
        review_ref_text = _require_nonempty_string(review_ref, "review_ref")
        normalized_review_ref = _validate_live_references(
            (review_ref_text,), "review_ref", repository_root
        )[0]
        normalized.append(
            {
                "id": decision_id,
                "pattern": pattern,
                "applies_to": _require_nonempty_string(decision.get("applies_to"), "applies_to"),
                "problem": _require_nonempty_string(decision.get("problem"), "problem"),
                "selected_because": _require_nonempty_string(
                    decision.get("selected_because"), "selected_because"
                ),
                "alternatives_considered": list(alternatives),
                "tradeoffs": list(_require_string_list(decision.get("tradeoffs"), "tradeoffs")),
                "normative_refs": list(
                    _validate_live_references(
                        _require_string_list(decision.get("normative_refs"), "normative_refs"),
                        "normative_refs",
                        repository_root,
                    )
                ),
                "enforcement_refs": list(
                    _validate_live_references(
                        _require_string_list(
                            decision.get("enforcement_refs"), "enforcement_refs"
                        ),
                        "enforcement_refs",
                        repository_root,
                    )
                ),
                "review_triggers": list(
                    _require_string_list(decision.get("review_triggers"), "review_triggers")
                ),
                "review_scope": review_scope,
                "review_status": review_status,
                "review_ref": normalized_review_ref,
            }
        )
    missing = set(REQUIRED_DESIGN_PATTERNS) - seen
    if missing:
        raise QualityError(f"missing required design decisions: {sorted(missing)}")
    unexpected = seen - set(REQUIRED_DESIGN_PATTERNS)
    if unexpected:
        raise QualityError(f"undeclared design decisions require a schema update: {sorted(unexpected)}")
    return tuple(sorted(normalized, key=lambda decision: str(decision["id"])))


def _finding_report(finding: QualityFinding) -> dict[str, object]:
    """Return one deterministic finding report object."""

    rule = QUALITY_RULES[finding.rule_id]
    return {
        "category": finding.category,
        "finding_id": finding.finding_id,
        "item": finding.item,
        "line": finding.line,
        "meaning": rule["meaning"],
        "path": finding.path,
        "preferred_pattern": rule["preferred_pattern"],
        "rule_id": finding.rule_id,
        "rule_name": rule["name"],
        "source_sha256": finding.source_sha256,
    }


def _design_fingerprint(decisions: Sequence[Mapping[str, object]]) -> str:
    """Hash normalized tooling-only design decision records."""

    encoded = json.dumps(decisions, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _source_fingerprint(sources: Mapping[str, str]) -> str:
    """Hash a length-framed snapshot of every audited Rust source role."""

    digest = hashlib.sha256()
    for path, source in sorted(sources.items()):
        path_bytes = path.encode("utf-8")
        source_bytes = source.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(4, "big"))
        digest.update(path_bytes)
        digest.update(len(source_bytes).to_bytes(8, "big"))
        digest.update(source_bytes)
    return digest.hexdigest()


def _source_role(path_text: str) -> str:
    """Classify a repository Rust file into one explicit assurance role."""

    parts = PurePosixPath(path_text).parts
    if parts and parts[0] == "fuzz":
        return "fuzz"
    if "tests" in parts:
        return "integration_test"
    if "benches" in parts:
        return "benchmark"
    if "examples" in parts:
        return "example"
    if len(parts) >= 4 and parts[0] == "crates" and parts[2] == "src":
        return "production_with_embedded_assurance"
    if parts and parts[-1] == "build.rs":
        return "build_script"
    return "other_rust"


def build_report(
    sources: Mapping[str, str],
    complexity_registry: object,
    design_registry: object,
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    """Build one deterministic multi-axis code-quality report."""

    normalized_sources: dict[str, str] = {}
    for path, source in sources.items():
        try:
            normalized = _validate_relative_path(path)
        except ComplexityError as error:
            raise QualityError(str(error)) from error
        if normalized in normalized_sources:
            raise QualityError(f"duplicate source path: {normalized}")
        if not isinstance(source, str):
            raise QualityError("Rust source must be UTF-8 text")
        normalized_sources[normalized] = source
    if not normalized_sources:
        raise QualityError("code-quality report requires at least one Rust source")
    complexity_sources = {
        path: source
        for path, source in normalized_sources.items()
        if _source_role(path) == "production_with_embedded_assurance"
    }
    if not complexity_sources:
        raise QualityError("code-quality report requires at least one production Rust source")
    try:
        complexity_report = build_complexity_report(complexity_sources, complexity_registry)
    except ComplexityError as error:
        raise QualityError(str(error)) from error
    decisions = validate_design_decisions(design_registry, repository_root)
    findings = tuple(
        finding
        for path in sorted(normalized_sources)
        for finding in analyze_rust_quality(path, normalized_sources[path])
    )
    complexity_summary = complexity_report["summary"]
    active_findings = len(findings)
    complexity_passes = complexity_report["status"] == "pass"
    status = "pass" if not active_findings and complexity_passes else "review-needed"
    approved_exceptions = int(complexity_summary["approved_exception_count"])
    warning_count = int(complexity_summary["warning_count"])
    excellent_structural_candidate = (
        status == "pass" and approved_exceptions == 0 and warning_count == 0
    )
    if status != "pass":
        structural_quality_tier = "review-required"
    elif excellent_structural_candidate:
        structural_quality_tier = "excellent-candidate"
    else:
        structural_quality_tier = "maintained-with-advisories"
    technical_ai_review_complete = all(
        decision["review_status"] == "ai-reviewed"
        for decision in decisions
        if decision["review_scope"] == "technical"
    )
    counts = {
        category: sum(finding.category == category for finding in findings)
        for category in ("code_smell", "antipattern", "design_pattern")
    }
    payload: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": status,
        "structural_quality_tier": structural_quality_tier,
        "meets_excellent_structural_baseline": excellent_structural_candidate,
        "technical_ai_review_status": (
            "complete" if technical_ai_review_complete else "required"
        ),
        "source_fingerprint_sha256": _source_fingerprint(normalized_sources),
        "design_decision_fingerprint_sha256": _design_fingerprint(decisions),
        "quality_rule_contract": QUALITY_RULES,
        "dimensions": {
            "complexity": {
                "status": complexity_report["status"],
                "preferred_warning_count": warning_count,
                "review_required_count": complexity_summary["review_required_count"],
                "unapproved_review_count": complexity_summary["unapproved_review_count"],
                "approved_exception_count": approved_exceptions,
            },
            "code_smells": {"finding_count": counts["code_smell"]},
            "antipatterns": {"finding_count": counts["antipattern"]},
            "design_patterns": {
                "finding_count": counts["design_pattern"],
                "required_decision_count": len(REQUIRED_DESIGN_PATTERNS),
                "complete_decision_count": len(decisions),
            },
        },
        "findings": [_finding_report(finding) for finding in findings],
        "design_decisions": list(decisions),
        "summary": {
            "active_quality_finding_count": active_findings,
            "advisory_complexity_count": warning_count,
            "audited_file_count": len(normalized_sources),
            "complexity_file_count": complexity_summary["file_count"],
            "audited_function_count": complexity_summary["function_count"],
            "quality_rule_count": len(QUALITY_RULES),
            "required_design_decision_count": len(REQUIRED_DESIGN_PATTERNS),
            "source_role_counts": {
                role: sum(_source_role(path) == role for path in normalized_sources)
                for role in sorted({_source_role(path) for path in normalized_sources})
            },
        },
        "excellent_structural_baseline_contract": {
            "no_active_quality_findings": active_findings == 0,
            "no_unapproved_complexity_reviews": complexity_summary[
                "unapproved_review_count"
            ]
            == 0,
            "no_approved_exception_debt": approved_exceptions == 0,
            "all_required_design_decisions_complete": len(decisions)
            == len(REQUIRED_DESIGN_PATTERNS),
            "no_preferred_complexity_warning_debt": warning_count == 0,
        },
        "unmeasured_review_requirements": [
            "diff-aware shotgun edits across unrelated crates",
            "semantic duplication between host, guest, and independent implementations",
            "tests that mirror implementation logic instead of stating invariants",
            "comments that excuse an unenforced invariant",
            "universal optimality of a selected design pattern",
            "cyclomatic and cognitive complexity outside compiler diagnostics",
            "Python quality-tool complexity and semantics",
        ],
        "non_claims": [
            "lexical rules are not compiler-AST or macro-expanded analysis",
            "design records establish completeness and live references, not universal pattern optimality",
            "production complexity and all-role lexical-smell coverage are separate report axes",
            "a passing report or excellent-candidate tier is not human review, formal proof, a security audit, or production authority",
        ],
    }
    payload["canonical_json"] = json.dumps(
        payload, ensure_ascii=True, indent=2, sort_keys=True
    ) + "\n"
    return payload


def _read_repository_sources() -> dict[str, str]:
    """Read deterministic Rust production and assurance sources."""

    sources: dict[str, str] = {}
    patterns = (
        "crates/*/src/**/*.rs",
        "crates/*/tests/**/*.rs",
        "crates/*/benches/**/*.rs",
        "crates/*/examples/**/*.rs",
        "crates/*/build.rs",
        "fuzz/**/*.rs",
    )
    paths = sorted({path for pattern in patterns for path in ROOT.glob(pattern)})
    for path in paths:
        if path.is_symlink():
            raise QualityError(f"Rust source symlink requires review: {path.relative_to(ROOT)}")
        source_bytes = path.read_bytes()
        if len(source_bytes) > MAX_SOURCE_FILE_BYTES:
            raise QualityError(
                f"Rust source exceeds one-megabyte review ceiling: {path.relative_to(ROOT)}"
            )
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise QualityError(f"Rust source is not UTF-8: {path.relative_to(ROOT)}") from error
        relative = path.relative_to(ROOT).as_posix()
        if relative in sources:
            raise QualityError(f"duplicate discovered Rust source: {relative}")
        sources[relative] = source
    if not sources:
        raise QualityError("no Rust production or assurance files were discovered")
    return sources


def _read_json(path_text: str) -> object:
    """Read one normalized repository-relative JSON policy artifact."""

    try:
        normalized = _validate_relative_path(path_text)
    except ComplexityError as error:
        raise QualityError(str(error)) from error
    path = ROOT / normalized
    if path.is_symlink():
        raise QualityError(f"quality policy path is a symlink: {normalized}")
    try:
        return _decode_json_strict(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise QualityError(f"cannot read code-quality policy artifact: {normalized}") from error


def _decode_json_strict(source: str) -> object:
    """Decode policy JSON while rejecting duplicate keys at every depth."""

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        decoded: dict[str, object] = {}
        for key, value in pairs:
            if key in decoded:
                raise QualityError(f"duplicate JSON object key in quality policy: {key!r}")
            decoded[key] = value
        return decoded

    return json.loads(source, object_pairs_hook=unique_object)


def _write_report(path_text: str, canonical_json: str) -> None:
    """Write a report only as JSON beneath the repository target directory."""

    try:
        normalized = _validate_relative_path(path_text)
    except ComplexityError as error:
        raise QualityError(str(error)) from error
    relative_path = PurePosixPath(normalized)
    if (
        len(relative_path.parts) < 2
        or relative_path.parts[0] != "target"
        or relative_path.suffix != ".json"
    ):
        raise QualityError("code-quality reports may be written only as JSON beneath target/")
    path = ROOT / normalized
    target_root = ROOT / "target"
    for parent in path.parents:
        if parent == ROOT:
            break
        if parent.exists() and parent.is_symlink():
            raise QualityError(f"code-quality report parent is a symlink: {parent.relative_to(ROOT)}")
    if path.exists() and path.is_symlink():
        raise QualityError(f"code-quality report path is a symlink: {normalized}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.resolve().is_relative_to(target_root.resolve()):
        raise QualityError("code-quality report path resolves outside target/")
    path.write_text(canonical_json, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run all-role analysis and enforce blocker and warning-debt ratchets."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--complexity-exceptions",
        default=DEFAULT_COMPLEXITY_EXCEPTIONS,
        help="repository-relative complexity exception registry",
    )
    parser.add_argument(
        "--design-decisions",
        default=DEFAULT_DESIGN_DECISIONS,
        help="repository-relative design-pattern decision registry",
    )
    parser.add_argument("--report", help="optional canonical JSON output beneath target/")
    arguments = parser.parse_args(argv)
    try:
        report = build_report(
            _read_repository_sources(),
            _read_json(arguments.complexity_exceptions),
            _read_json(arguments.design_decisions),
        )
        if arguments.report:
            _write_report(arguments.report, report["canonical_json"])
    except (ComplexityError, QualityError) as error:
        print(f"code-quality check failed: {error}", file=sys.stderr)
        return 1
    summary = report["summary"]
    warning_count = int(summary["advisory_complexity_count"])
    if report["status"] != "pass" or warning_count > CURRENT_COMPLEXITY_WARNING_CEILING:
        print(
            "code-quality check requires review: "
            f"tier={report['structural_quality_tier']}, "
            f"{summary['active_quality_finding_count']} quality finding(s), "
            f"{warning_count}/{CURRENT_COMPLEXITY_WARNING_CEILING} complexity advisories",
            file=sys.stderr,
        )
        for finding in report["findings"]:
            print(
                "code-quality finding: "
                f"{finding['path']}:{finding['line']} {finding['rule_id']} "
                f"{finding['rule_name']} ({finding['item']})",
                file=sys.stderr,
            )
        return 1
    print(
        "code-quality check passed: "
        f"tier={report['structural_quality_tier']}, "
        f"technical-ai-review={report['technical_ai_review_status']}, "
        f"{summary['quality_rule_count']} rules, "
        f"{summary['required_design_decision_count']} design decisions, "
        f"{warning_count}/{CURRENT_COMPLEXITY_WARNING_CEILING} complexity advisory(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
