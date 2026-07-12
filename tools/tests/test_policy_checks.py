"""Unit tests for repository conformance and workflow policy helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.check_architecture import dependency_failures, public_authority_api_failures
from tools.check_conformance import (
    ConformanceError,
    github_anchor,
    require,
    validate_promotion_boundary,
    validate_reference,
)
from tools.check_coverage import CoverageError, coverage_totals, enforce_thresholds
from tools.check_repository_hygiene import action_pin_failures


class ConformanceHelperTests(unittest.TestCase):
    """Exercise deterministic anchor and failure behavior."""

    def test_github_anchor_removes_punctuation(self) -> None:
        """Markdown anchors retain semantic words and separators."""

        self.assertEqual(github_anchor("13.6 ResourceWireV1 canonical bytes"), "136-resourcewirev1-canonical-bytes")

    def test_require_raises_typed_error(self) -> None:
        """Failed matrix predicates use the conformance error type."""

        with self.assertRaises(ConformanceError):
            require(False, "expected failure")

    def test_reference_cannot_escape_repository(self) -> None:
        """Parent traversal cannot satisfy a matrix evidence reference."""

        with self.assertRaises(ConformanceError):
            validate_reference("../ZRM/LICENSE", "ZRM-CBC-TEST", {})

    @staticmethod
    def promoted_data() -> dict[str, object]:
        """Return the minimal valid promoted-claim shape for focused tests."""

        return {
            "status": "scoped_wp0_wp1_implementation",
            "promotion_boundary": {
                "public_implementation_claim_allowed": True,
                "production_ready": False,
                "current_level": "ZRM-L0",
                "claim_scope": ["reviewed_wp1_scope"],
                "promotion_evidence": ["evidence/wp1-class-c-review-2026-07-11.json"],
            },
        }

    def test_promoted_claim_rejects_wrong_matrix_status(self) -> None:
        """A promoted level cannot retain candidate or arbitrary top-level status."""

        data = self.promoted_data()
        data["status"] = "candidate"
        with self.assertRaises(ConformanceError):
            validate_promotion_boundary(data, [{"status": "implemented"}])

    def test_promoted_claim_requires_evidence(self) -> None:
        """A promoted level must bind an existing durable review/evidence record."""

        data = self.promoted_data()
        boundary = data["promotion_boundary"]
        self.assertIsInstance(boundary, dict)
        if isinstance(boundary, dict):
            boundary["promotion_evidence"] = []
        with self.assertRaises(ConformanceError):
            validate_promotion_boundary(data, [{"status": "implemented"}])

    def test_promoted_claim_requires_public_claim_flag(self) -> None:
        """A promoted level with a disabled scoped-claim flag is inconsistent."""

        data = self.promoted_data()
        boundary = data["promotion_boundary"]
        self.assertIsInstance(boundary, dict)
        if isinstance(boundary, dict):
            boundary["public_implementation_claim_allowed"] = False
        with self.assertRaises(ConformanceError):
            validate_promotion_boundary(data, [{"status": "implemented"}])


class WorkflowPinTests(unittest.TestCase):
    """Exercise exact GitHub Action pin enforcement."""

    def test_full_commit_pin_is_accepted(self) -> None:
        """A forty-hex action ref passes."""

        workflow = "uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n"
        self.assertEqual(action_pin_failures(workflow, Path("ci.yml")), [])

    def test_tag_ref_is_rejected(self) -> None:
        """A mutable version tag fails."""

        workflow = "uses: actions/checkout@v4\n"
        self.assertEqual(len(action_pin_failures(workflow, Path("ci.yml"))), 1)


class CoveragePolicyTests(unittest.TestCase):
    """Exercise fail-closed line and branch threshold handling."""

    @staticmethod
    def report() -> dict[str, object]:
        """Return a minimal LLVM JSON coverage report."""

        return {
            "data": [
                {
                    "totals": {
                        "lines": {"count": 100, "covered": 98},
                        "branches": {"count": 10, "covered": 9},
                    },
                    "files": [
                        {
                            "filename": "/repo/crates/zrm-policy/src/lib.rs",
                            "summary": {
                                "lines": {"count": 20, "covered": 20},
                                "branches": {"count": 4, "covered": 4},
                            },
                        }
                    ],
                }
            ]
        }

    def test_workspace_thresholds_accept_inclusive_percentages(self) -> None:
        """Workspace totals at or above both thresholds pass."""

        totals = coverage_totals(self.report(), None)
        self.assertEqual(enforce_thresholds(totals, 98.0, 90.0), (98.0, 90.0))

    def test_scope_prefix_aggregates_only_selected_files(self) -> None:
        """A critical-crate scope uses only matching file summaries."""

        totals = coverage_totals(self.report(), "crates/zrm-policy")
        self.assertEqual(enforce_thresholds(totals, 100.0, 100.0), (100.0, 100.0))

    def test_branch_threshold_fails_closed(self) -> None:
        """A branch result below policy raises a typed error."""

        totals = coverage_totals(self.report(), None)
        with self.assertRaises(CoverageError):
            enforce_thresholds(totals, 90.0, 90.1)

    def test_zero_branch_sites_fail_closed(self) -> None:
        """A report that omitted branch instrumentation cannot pass as full."""

        totals = coverage_totals(self.report(), None)
        totals["branches"] = {"count": 0, "covered": 0}
        with self.assertRaises(CoverageError):
            enforce_thresholds(totals, 90.0, 85.0)

    def test_impossible_covered_count_fails_closed(self) -> None:
        """Covered sites cannot be negative or exceed total sites."""

        for count, covered in [(-1, 0), (10, -1), (10, 11)]:
            with self.subTest(count=count, covered=covered):
                totals = coverage_totals(self.report(), None)
                totals["branches"] = {"count": count, "covered": covered}
                with self.assertRaises(CoverageError):
                    enforce_thresholds(totals, 90.0, 85.0)


class ArchitecturePolicyTests(unittest.TestCase):
    """Exercise exact external dependency allowlisting."""

    def test_unexpected_external_dependency_is_rejected(self) -> None:
        """A network client cannot silently enter a core crate."""

        package = {
            "name": "zrm-types",
            "dependencies": [{"name": "reqwest"}],
        }
        self.assertEqual(len(dependency_failures(package)), 1)

    def test_exact_crypto_dependencies_are_accepted(self) -> None:
        """The reviewed crypto dependency set passes exactly."""

        package = {
            "name": "zrm-crypto",
            "dependencies": [{"name": "sha2"}, {"name": "zrm-types"}],
        }
        self.assertEqual(dependency_failures(package), [])

    def test_crate_private_candidate_helpers_are_accepted(self) -> None:
        """Internal arithmetic and shape helpers remain available for assurance."""

        sources = allowed_authority_sources()
        sources["cost.rs"] += "\npub(crate) fn compute_untrusted_candidate_quote() {}"
        sources["error.rs"] += "\npub(crate) enum VerifierCompatibilityErrorV1 {}"
        sources["lib.rs"] += "\npub(crate) use cost::CandidateVerifierCostQuoteV1;"
        sources["verifier.rs"] += "\npub(crate) fn check_untrusted_admission_candidate_shape() {}"
        self.assertEqual(public_authority_api_failures(sources), [])

    def test_public_candidate_authority_methods_are_rejected(self) -> None:
        """Default public APIs cannot quote or return admission-like success."""

        sources = allowed_authority_sources()
        sources["cost.rs"] += "\npub fn compute_quote() {}"
        sources["verifier.rs"] += "\npub fn validate_admission_verifier_candidate() {}"
        failures = public_authority_api_failures(sources)
        self.assertTrue(any("compute_quote" in failure for failure in failures))
        self.assertTrue(
            any("validate_admission_verifier_candidate" in failure for failure in failures)
        )

    def test_public_quote_types_and_reexports_are_rejected(self) -> None:
        """Opaque candidate quote values cannot escape through the crate root."""

        sources = allowed_authority_sources()
        sources["cost.rs"] += "\npub struct VerifierCostQuoteV1;"
        sources["lib.rs"] += "\npub use cost::VerifierCostQuoteRequestV1;"
        failures = public_authority_api_failures(sources)
        self.assertTrue(any("VerifierCostQuoteV1" in failure for failure in failures))
        self.assertTrue(any("VerifierCostQuoteRequestV1" in failure for failure in failures))

    def test_renamed_public_quote_operation_is_rejected_by_exact_allowlist(self) -> None:
        """Renaming a quote escape cannot bypass the architecture gate."""

        sources = allowed_authority_sources()
        sources["cost.rs"] += "\npub fn calculate_candidate_cost() -> u64 { 0 }"
        failures = public_authority_api_failures(sources)
        self.assertTrue(any("calculate_candidate_cost" in failure for failure in failures))

    def test_allowlisted_name_on_wrong_owner_is_rejected(self) -> None:
        """A method cannot reuse another type's allowlisted getter name."""

        sources = allowed_authority_sources()
        sources["cost.rs"] += """
impl VerifierCostRowV1 {
    pub fn max_charge_units(&self) -> u64 { 0 }
}
"""
        failures = public_authority_api_failures(sources)
        self.assertTrue(any("max_charge_units" in failure for failure in failures))
        self.assertTrue(any("function signatures" in failure for failure in failures))

    def test_async_and_extern_public_functions_are_rejected(self) -> None:
        """Rust function qualifiers cannot bypass the reviewed signature inventory."""

        for declaration in (
            "pub async fn calculate_candidate_cost() {}",
            'pub extern "C" fn calculate_candidate_cost() {}',
        ):
            with self.subTest(declaration=declaration):
                sources = allowed_authority_sources()
                sources["cost.rs"] += f"\n{declaration}"
                failures = public_authority_api_failures(sources)
                self.assertTrue(any("calculate_candidate_cost" in failure for failure in failures))

    def test_public_function_pointer_constant_is_rejected(self) -> None:
        """A callable associated constant is part of the exact value inventory."""

        sources = allowed_authority_sources()
        sources["cost.rs"] += "\npub const QUOTE: fn() -> u64 = || 0;"
        failures = public_authority_api_failures(sources)
        self.assertTrue(any("const/static" in failure for failure in failures))

    def test_fuzz_assertion_cannot_return_a_cost_value(self) -> None:
        """The fuzz-only public bridge remains a raw-input assertion sink."""

        sources = allowed_authority_sources()
        sources["fuzz_assertions.rs"] = (
            "pub fn fuzz_assert_untrusted_candidate_cost_invariants(data: &[u8]) -> u64 { "
            "data.len() as u64 }"
        )
        failures = public_authority_api_failures(sources)
        self.assertTrue(any("implicit unit return" in failure for failure in failures))

    def test_fuzz_assertion_reexports_require_fuzz_configuration(self) -> None:
        """The assertion sink is absent from the default public API."""

        sources = allowed_authority_sources()
        sources["lib.rs"] = sources["lib.rs"].replace("#[cfg(fuzzing)]\n", "", 1)
        failures = public_authority_api_failures(sources)
        self.assertTrue(any("only under cfg(fuzzing)" in failure for failure in failures))


def allowed_authority_sources() -> dict[str, str]:
    """Return the live reviewed sources for focused counterexample mutation."""

    from tools.check_architecture import AUTHORITY_SOURCE_PATHS, ROOT

    return {
        Path(path).name: (ROOT / path).read_text(encoding="utf-8")
        for path in AUTHORITY_SOURCE_PATHS
    }


if __name__ == "__main__":
    unittest.main()
