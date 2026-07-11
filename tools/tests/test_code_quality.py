"""Unit tests for deterministic multi-axis Rust code-quality reporting."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.check_code_quality import (
    REQUIRED_DESIGN_PATTERNS,
    QualityError,
    _source_role,
    _write_report,
    _decode_json_strict,
    build_report,
    validate_design_decisions,
)
from tools.rust_quality import analyze_rust_quality


def valid_design_registry() -> dict[str, object]:
    """Return complete records for every required architectural choice."""

    return {
        "schema": "zrm/design-pattern-decisions/v1",
        "decisions": [
            {
                "id": decision_id,
                "pattern": pattern,
                "applies_to": "Authority-sensitive core construction and review.",
                "problem": "The core needs one explicit and reviewable responsibility boundary.",
                "selected_because": "The pattern makes invalid authority states harder to represent.",
                "alternatives_considered": [
                    "A single mutable service object.",
                    "No additional pattern; keep explicit functions and types.",
                ],
                "tradeoffs": ["More explicit types and modules must be maintained."],
                "normative_refs": ["AGENTS.md"],
                "enforcement_refs": ["tools/check_architecture.py"],
                "review_triggers": ["The pattern no longer preserves its stated invariant."],
                "review_scope": "technical",
                "review_status": "ai-reviewed",
                "review_ref": "AGENTS.md",
            }
            for decision_id, pattern in REQUIRED_DESIGN_PATTERNS.items()
        ],
    }


def rule_ids(source: str) -> set[str]:
    """Return finding rule IDs for one fixture source."""

    return {
        finding.rule_id
        for finding in analyze_rust_quality("crates/example/src/lib.rs", source)
    }


class RustQualityAnalysisTests(unittest.TestCase):
    """Exercise bounded lexical smell and antipattern recognition."""

    def test_comments_and_literals_cannot_fabricate_findings(self) -> None:
        """Rust-looking examples outside code remain inert input data."""

        source = r'''
// fn process(verified: bool) { SystemTime::now(); }
/* #[allow(clippy::all)] use std::collections::*; */
const EXAMPLE: &str = "struct ResourceManager { policy_id: String }";
fn validate(mode: AdmissionModeV1) {}
'''

        self.assertEqual(rule_ids(source), set())

    def test_boolean_parameter_rejects_but_semantic_enum_passes(self) -> None:
        """Authority choices use a named enum instead of boolean blindness."""

        self.assertIn("ZRM-Q001", rule_ids("fn verify(required: bool) {}\n"))
        self.assertNotIn(
            "ZRM-Q001", rule_ids("fn verify(mode: ProofModeV1) {}\n")
        )

    def test_const_generic_braces_cannot_hide_function_or_struct_hazards(self) -> None:
        """Valid const expressions before bodies cannot terminate lexical discovery."""

        source = """
fn verify<const N: usize = { choose() }>(required: bool) {}
pub struct VerifiedFact<const N: usize = { 1 }> {
    pub verified: bool,
}
"""
        self.assertTrue({"ZRM-Q001", "ZRM-Q002", "ZRM-Q011"}.issubset(rule_ids(source)))

    def test_authority_fields_reject_boolean_string_bytes_and_public_state(self) -> None:
        """Validated state cannot expose primitive or stringly authority fields."""

        source = """
pub struct VerifiedAdmissionFact {
    pub verified: bool,
    pub policy_id: String,
    pub resource_id: [u8; 32],
}
"""

        self.assertTrue(
            {"ZRM-Q002", "ZRM-Q005", "ZRM-Q006", "ZRM-Q011"}.issubset(
                rule_ids(source)
            )
        )

    def test_suppression_nondeterminism_float_wildcard_and_fallback_reject(self) -> None:
        """Core convenience mechanisms cannot hide review-relevant behavior."""

        source = """
#![allow(clippy::all)]
use std::collections::*;
fn calculate() {
    let ratio: f64 = 1.0;
    let map = HashMap::new();
    let value = map.get(&1).unwrap_or_default();
}
"""

        self.assertTrue(
            {"ZRM-Q004", "ZRM-Q007", "ZRM-Q008", "ZRM-Q009", "ZRM-Q012"}.issubset(
                rule_ids(source)
            )
        )

    def test_vague_name_manager_object_and_default_reject(self) -> None:
        """Generic orchestration names and implicit authority construction are visible."""

        source = """
#[derive(Default)]
pub struct PolicyManager {}
fn process() {}
"""

        self.assertTrue(
            {"ZRM-Q003", "ZRM-Q010", "ZRM-Q013"}.issubset(rule_ids(source))
        )

    def test_finding_identity_changes_after_same_shape_source_edit(self) -> None:
        """A finding binds source content as well as rule and location."""

        first = analyze_rust_quality(
            "crates/example/src/lib.rs", "fn verify(required: bool) {}\n"
        )[0]
        second = analyze_rust_quality(
            "crates/example/src/lib.rs", "fn verify(optional: bool) {}\n"
        )[0]

        self.assertNotEqual(first.finding_id, second.finding_id)

    def test_wire_candidate_raw_ids_are_inert_while_clock_and_bypass_reject(self) -> None:
        """The lexical lane preserves the wire/authority boundary and determinism rules."""

        wire = "pub struct ResourceWireV1 { pub machine_id: [u8; 32] }\n"
        self.assertNotIn("ZRM-Q006", rule_ids(wire))
        hazards = '#[cfg(feature = "skip-proof-verification")]\nfn now() { SystemTime::now(); }\n'
        self.assertTrue({"ZRM-Q014", "ZRM-Q015"}.issubset(rule_ids(hazards)))

    def test_unguarded_test_success_skip_rejects_but_asserted_fixture_passes(self) -> None:
        """A constructor regression cannot silently turn a behavior test green."""

        unguarded = """
fn behavior() -> Result<(), TestError> {
    let policy = construct();
    let Ok(policy) = policy else { return Ok(()); };
    assert!(policy.valid());
    Ok(())
}
"""
        guarded = unguarded.replace(
            "let Ok(policy)", "assert!(policy.is_ok());\n    let Ok(policy)"
        )
        unguarded_ids = {
            finding.rule_id
            for finding in analyze_rust_quality(
                "crates/example/tests/behavior.rs", unguarded
            )
        }
        guarded_ids = {
            finding.rule_id
            for finding in analyze_rust_quality(
                "crates/example/tests/behavior.rs", guarded
            )
        }
        self.assertIn("ZRM-Q016", unguarded_ids)
        self.assertNotIn("ZRM-Q016", guarded_ids)


class DesignDecisionTests(unittest.TestCase):
    """Exercise complete, live architectural-pattern decision records."""

    def test_complete_required_decisions_are_accepted(self) -> None:
        """Every required pattern has explicit rationale and enforcement."""

        decisions = validate_design_decisions(valid_design_registry())
        self.assertEqual(len(decisions), len(REQUIRED_DESIGN_PATTERNS))

    def test_missing_or_duplicate_required_decision_rejects(self) -> None:
        """A required pattern cannot disappear or become ambiguous."""

        registry = valid_design_registry()
        decisions = registry["decisions"]
        self.assertIsInstance(decisions, list)
        if isinstance(decisions, list):
            missing = {**registry, "decisions": decisions[1:]}
            duplicate = {**registry, "decisions": [*decisions, decisions[0]]}
            with self.assertRaises(QualityError):
                validate_design_decisions(missing)
            with self.assertRaises(QualityError):
                validate_design_decisions(duplicate)

    def test_empty_reasoning_or_stale_enforcement_reference_rejects(self) -> None:
        """A pattern label alone is not a design decision or evidence."""

        registry = valid_design_registry()
        decisions = registry["decisions"]
        self.assertIsInstance(decisions, list)
        if not isinstance(decisions, list):
            self.fail("fixture decisions must be a list")
        empty_alternative = {
            **decisions[0],
            "alternatives_considered": [],
        }
        stale_reference = {
            **decisions[0],
            "enforcement_refs": ["tools/missing_quality_gate.py"],
        }
        for invalid in (empty_alternative, stale_reference):
            replaced = {**registry, "decisions": [invalid, *decisions[1:]]}
            with self.subTest(invalid=invalid), self.assertRaises(QualityError):
                validate_design_decisions(replaced)

    def test_parent_path_in_decision_reference_rejects(self) -> None:
        """Decision evidence cannot escape the reviewed repository."""

        registry = valid_design_registry()
        decisions = registry["decisions"]
        self.assertIsInstance(decisions, list)
        if isinstance(decisions, list):
            escaped = {**decisions[0], "normative_refs": ["../AGENTS.md"]}
            with self.assertRaises(QualityError):
                validate_design_decisions(
                    {**registry, "decisions": [escaped, *decisions[1:]]}
                )

    def test_pattern_choice_must_consider_no_additional_pattern(self) -> None:
        """Pattern records cannot turn pattern use into an automatic objective."""

        registry = valid_design_registry()
        decisions = registry["decisions"]
        self.assertIsInstance(decisions, list)
        if isinstance(decisions, list):
            invalid = {
                **decisions[0],
                "alternatives_considered": ["Use a larger framework."],
            }
            with self.assertRaises(QualityError):
                validate_design_decisions(
                    {**registry, "decisions": [invalid, *decisions[1:]]}
                )

    def test_technical_decision_requires_ai_review_evidence(self) -> None:
        """Technical choices consume AI review rather than human attention."""

        registry = valid_design_registry()
        decisions = registry["decisions"]
        self.assertIsInstance(decisions, list)
        if isinstance(decisions, list):
            invalid = {
                **decisions[0],
                "review_status": "human-review-required",
                "review_ref": None,
            }
            with self.assertRaises(QualityError):
                validate_design_decisions(
                    {**registry, "decisions": [invalid, *decisions[1:]]}
                )

class CodeQualityReportTests(unittest.TestCase):
    """Exercise deterministic multi-axis report and excellence semantics."""

    def test_clean_report_is_deterministic_excellent_candidate(self) -> None:
        """Mapping insertion order cannot alter the source or report identity."""

        sources = {
            "crates/zeta/src/lib.rs": "fn validate() {}\n",
            "crates/alpha/src/lib.rs": "fn construct() {}\n",
        }
        reversed_sources = dict(reversed(list(sources.items())))
        complexity_registry = {
            "schema": "zrm/complexity-exceptions/v1",
            "exceptions": [],
        }

        first = build_report(sources, complexity_registry, valid_design_registry())
        second = build_report(
            reversed_sources, complexity_registry, valid_design_registry()
        )

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "pass")
        self.assertEqual(first["structural_quality_tier"], "excellent-candidate")
        self.assertTrue(first["meets_excellent_structural_baseline"])
        self.assertEqual(first["technical_ai_review_status"], "complete")
        self.assertNotIn("/" + "home" + "/", first["canonical_json"])

    def test_smell_or_empty_source_set_cannot_be_excellent(self) -> None:
        """An active finding blocks excellence and absent coverage fails closed."""

        complexity_registry = {
            "schema": "zrm/complexity-exceptions/v1",
            "exceptions": [],
        }
        report = build_report(
            {"crates/example/src/lib.rs": "fn process(flag: bool) {}\n"},
            complexity_registry,
            valid_design_registry(),
        )
        self.assertEqual(report["status"], "review-needed")
        self.assertEqual(report["structural_quality_tier"], "review-required")

        with self.assertRaises(QualityError):
            build_report({}, complexity_registry, valid_design_registry())

    def test_report_writer_cannot_overwrite_reviewed_source(self) -> None:
        """Diagnostic output is confined to JSON files beneath target."""

        with patch("pathlib.Path.write_text") as write_text:
            with self.assertRaises(QualityError):
                _write_report("tools/should-not-write.json", "{}\n")
        write_text.assert_not_called()

    def test_duplicate_quality_policy_keys_reject(self) -> None:
        """Ambiguous machine policy input fails closed at every object depth."""

        for source in (
            '{"schema":"wrong","schema":"right"}',
            '{"outer":{"id":"first","id":"second"}}',
        ):
            with self.subTest(source=source), self.assertRaises(QualityError):
                _decode_json_strict(source)

    def test_source_roles_are_explicit_and_test_size_does_not_change_core_budget(self) -> None:
        """All roles are smell-scanned while production complexity remains separate."""

        self.assertEqual(
            _source_role("crates/example/src/lib.rs"),
            "production_with_embedded_assurance",
        )
        self.assertEqual(
            _source_role("crates/example/tests/integration.rs"), "integration_test"
        )
        self.assertEqual(_source_role("fuzz/fuzz_targets/decode.rs"), "fuzz")

        large_test = "\n".join("fn exact_case() {}" for _ in range(701))
        report = build_report(
            {
                "crates/example/src/lib.rs": "fn validate() {}\n",
                "crates/example/tests/integration.rs": large_test,
            },
            {"schema": "zrm/complexity-exceptions/v1", "exceptions": []},
            valid_design_registry(),
        )
        self.assertEqual(report["summary"]["audited_file_count"], 2)
        self.assertEqual(report["summary"]["complexity_file_count"], 1)


if __name__ == "__main__":
    unittest.main()
