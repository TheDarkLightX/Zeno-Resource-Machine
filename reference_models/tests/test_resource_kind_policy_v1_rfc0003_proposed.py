"""Independent tests for the proposed RFC-0003 quantity semantics."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from reference_models.resource_kind_policy_v1 import (
    U128_MAX,
    U64_MAX,
    AccountingMode,
    DecisionKind as BaselineDecisionKind,
    PolicyCandidateV1,
    ResourceQuantityCandidateV1,
    decide_policy_construction as decide_baseline_policy,
    decide_resource_quantity as decide_baseline_resource,
)
from reference_models.resource_kind_policy_v1_rfc0003_proposed import (
    ProposedDecisionKind,
    ProposedReason,
    decide_rfc0003_policy_construction,
    decide_rfc0003_resource_quantity,
)


UNIT_U = "unit-u"
UNIT_V = "unit-v"
REFERENCE_MODELS = Path(__file__).resolve().parents[1]
COUNTEREXAMPLES = (
    REFERENCE_MODELS
    / "resource_kind_policy_v1_rfc0003_proposed_counterexamples.json"
)
BASELINE_SHA256 = {
    "RESOURCE_KIND_POLICY_V1_ORACLE.md": (
        "98e3f1950b586a48faf0a4684d1d779f18b74f911671e784af6626c2eb84d2a3"
    ),
    "resource_kind_policy_v1.py": (
        "430e4260eead5d1fa88925be75f87d283b5b47eb2b8b2436765c2280dcc4c2c6"
    ),
    "resource_kind_policy_v1_counterexamples.json": (
        "d5fe2b126748cccce346518310a9329b8709d678fa4bf454e5176af978fda334"
    ),
    "tests/test_resource_kind_policy_v1.py": (
        "37ba70e4a1051f0a688827f507bacdf893e68c979d7d10dac0b546faf8a69a3e"
    ),
}


def policy(
    mode: AccountingMode,
    quantity_max: int,
    *,
    schema_version: int = 1,
    validity_start_epoch: int = 0,
    validity_end_epoch: int = U64_MAX,
) -> PolicyCandidateV1:
    """Build an inert policy input shared by both independent decisions."""

    return PolicyCandidateV1(
        schema_version=schema_version,
        accounting_mode=mode,
        unit_id=UNIT_U,
        quantity_max=quantity_max,
        validity_start_epoch=validity_start_epoch,
        validity_end_epoch=validity_end_epoch,
    )


def resource(
    quantity_atoms: int,
    *,
    unit_id: str = UNIT_U,
) -> ResourceQuantityCandidateV1:
    """Build an inert resource quantity input."""

    return ResourceQuantityCandidateV1(unit_id=unit_id, quantity_atoms=quantity_atoms)


class FrozenBaselineTests(unittest.TestCase):
    """The proposal cannot silently rewrite its comparison oracle."""

    def test_frozen_baseline_artifact_hashes_are_unchanged(self) -> None:
        for relative_path, expected in BASELINE_SHA256.items():
            with self.subTest(path=relative_path):
                payload = (REFERENCE_MODELS / relative_path).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), expected)


class ProposedPolicyConstructionTests(unittest.TestCase):
    """RFC-0003 policy construction follows the supplied amendment."""

    def test_lifecycle_maximum_exactly_one_constructs(self) -> None:
        decision = decide_rfc0003_policy_construction(
            policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1)
        )
        self.assertEqual(decision.kind, ProposedDecisionKind.ACCEPT)
        self.assertEqual(decision.reason, ProposedReason.POLICY_SHAPE_ACCEPTED)

    def test_lifecycle_maxima_other_than_one_reject(self) -> None:
        for quantity_max in (0, 2, U128_MAX):
            with self.subTest(quantity_max=quantity_max):
                decision = decide_rfc0003_policy_construction(
                    policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, quantity_max)
                )
                self.assertEqual(decision.kind, ProposedDecisionKind.REJECT)
                self.assertEqual(
                    decision.reason,
                    ProposedReason.LIFECYCLE_POLICY_MAXIMUM_MUST_EQUAL_ONE,
                )

    def test_non_lifecycle_zero_maximum_constructs_empty_candidate(self) -> None:
        for mode in AccountingMode:
            if mode is AccountingMode.LIFECYCLE_NON_FUNGIBLE:
                continue
            with self.subTest(mode=mode):
                decision = decide_rfc0003_policy_construction(policy(mode, 0))
                self.assertEqual(decision.kind, ProposedDecisionKind.ACCEPT)
                self.assertIn(
                    "an admitted resource may not exist", decision.non_claims
                )

    def test_non_lifecycle_u128_maximum_constructs(self) -> None:
        for mode in AccountingMode:
            if mode is AccountingMode.LIFECYCLE_NON_FUNGIBLE:
                continue
            with self.subTest(mode=mode):
                decision = decide_rfc0003_policy_construction(
                    policy(mode, U128_MAX)
                )
                self.assertEqual(decision.kind, ProposedDecisionKind.ACCEPT)

    def test_constructor_precedence_schema_then_validity_then_lifecycle(self) -> None:
        schema_first = decide_rfc0003_policy_construction(
            policy(
                AccountingMode.LIFECYCLE_NON_FUNGIBLE,
                2,
                schema_version=2,
                validity_start_epoch=2,
                validity_end_epoch=1,
            )
        )
        validity_second = decide_rfc0003_policy_construction(
            policy(
                AccountingMode.LIFECYCLE_NON_FUNGIBLE,
                2,
                validity_start_epoch=2,
                validity_end_epoch=1,
            )
        )
        lifecycle_third = decide_rfc0003_policy_construction(
            policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, 2)
        )
        self.assertEqual(schema_first.reason, ProposedReason.UNSUPPORTED_SCHEMA)
        self.assertEqual(
            validity_second.reason, ProposedReason.INVALID_VALIDITY_WINDOW
        )
        self.assertEqual(
            lifecycle_third.reason,
            ProposedReason.LIFECYCLE_POLICY_MAXIMUM_MUST_EQUAL_ONE,
        )

    def test_width_checks_remain_fail_closed(self) -> None:
        invalid_validity = decide_rfc0003_policy_construction(
            policy(
                AccountingMode.CONSERVED_FUNGIBLE,
                1,
                validity_end_epoch=U64_MAX + 1,
            )
        )
        invalid_maximum = decide_rfc0003_policy_construction(
            policy(AccountingMode.CONSERVED_FUNGIBLE, U128_MAX + 1)
        )
        self.assertEqual(
            invalid_validity.reason, ProposedReason.VALIDITY_EPOCH_OUT_OF_RANGE
        )
        self.assertEqual(
            invalid_maximum.reason, ProposedReason.QUANTITY_MAX_OUT_OF_RANGE
        )


class ProposedResourceDecisionTests(unittest.TestCase):
    """RFC-0003 resource decisions expose the supplied relative precedence."""

    def test_every_mode_accepts_positive_quantity_one_at_maximum_one(self) -> None:
        for mode in AccountingMode:
            with self.subTest(mode=mode):
                decision = decide_rfc0003_resource_quantity(
                    policy(mode, 1), resource(1)
                )
                self.assertEqual(decision.kind, ProposedDecisionKind.ACCEPT)

    def test_unit_mismatch_precedes_lifecycle_and_zero(self) -> None:
        decision = decide_rfc0003_resource_quantity(
            policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1),
            resource(0, unit_id=UNIT_V),
        )
        self.assertEqual(decision.reason, ProposedReason.UNIT_MISMATCH)

    def test_lifecycle_exact_one_precedes_general_zero(self) -> None:
        decision = decide_rfc0003_resource_quantity(
            policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1), resource(0)
        )
        self.assertEqual(
            decision.reason, ProposedReason.LIFECYCLE_QUANTITY_MUST_EQUAL_ONE
        )

    def test_lifecycle_exact_one_precedes_general_maximum(self) -> None:
        decision = decide_rfc0003_resource_quantity(
            policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1), resource(2)
        )
        self.assertEqual(
            decision.reason, ProposedReason.LIFECYCLE_QUANTITY_MUST_EQUAL_ONE
        )

    def test_general_zero_precedes_maximum_for_empty_policy(self) -> None:
        decision = decide_rfc0003_resource_quantity(
            policy(AccountingMode.CONSERVED_FUNGIBLE, 0), resource(0)
        )
        self.assertEqual(
            decision.reason,
            ProposedReason.ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION,
        )

    def test_positive_quantity_rejects_above_empty_policy_maximum(self) -> None:
        decision = decide_rfc0003_resource_quantity(
            policy(AccountingMode.CONSERVED_FUNGIBLE, 0), resource(1)
        )
        self.assertEqual(decision.reason, ProposedReason.QUANTITY_EXCEEDS_MAXIMUM)

    def test_zero_rejects_for_every_mode(self) -> None:
        for mode in AccountingMode:
            with self.subTest(mode=mode):
                decision = decide_rfc0003_resource_quantity(
                    policy(mode, 1), resource(0)
                )
                self.assertEqual(decision.kind, ProposedDecisionKind.REJECT)

    def test_evidence_only_has_no_zero_marker_permission(self) -> None:
        zero = decide_rfc0003_resource_quantity(
            policy(AccountingMode.EVIDENCE_ONLY, 1), resource(0)
        )
        one = decide_rfc0003_resource_quantity(
            policy(AccountingMode.EVIDENCE_ONLY, 1), resource(1)
        )
        self.assertEqual(
            zero.reason,
            ProposedReason.ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION,
        )
        self.assertEqual(one.kind, ProposedDecisionKind.ACCEPT)
        self.assertEqual(
            one.reason,
            ProposedReason.EVIDENCE_ONLY_QUANTITY_STRUCTURALLY_ACCEPTED,
        )
        self.assertIn("evidence meaning remains unestablished", one.non_claims)

    def test_u128_maximum_is_preserved_for_non_lifecycle_mode(self) -> None:
        decision = decide_rfc0003_resource_quantity(
            policy(AccountingMode.TRANSFORMABLE, U128_MAX), resource(U128_MAX)
        )
        self.assertEqual(decision.kind, ProposedDecisionKind.ACCEPT)

    def test_quantity_above_u128_rejects_without_wrapping(self) -> None:
        decision = decide_rfc0003_resource_quantity(
            policy(AccountingMode.CONSERVED_FUNGIBLE, U128_MAX),
            resource(U128_MAX + 1),
        )
        self.assertEqual(decision.reason, ProposedReason.QUANTITY_OUT_OF_RANGE)


class FrozenBaselineDifferentialTests(unittest.TestCase):
    """The proposal changes exactly the maintainer-supplied state-space slice."""

    def test_policy_acceptance_delta_is_exact(self) -> None:
        removed: set[tuple[AccountingMode, int]] = set()
        added: set[tuple[AccountingMode, int]] = set()
        for mode in AccountingMode:
            for quantity_max in range(5):
                candidate = policy(mode, quantity_max)
                baseline_accepts = (
                    decide_baseline_policy(candidate).kind
                    is BaselineDecisionKind.ACCEPT
                )
                proposed_accepts = (
                    decide_rfc0003_policy_construction(candidate).kind
                    is ProposedDecisionKind.ACCEPT
                )
                if baseline_accepts and not proposed_accepts:
                    removed.add((mode, quantity_max))
                if proposed_accepts and not baseline_accepts:
                    added.add((mode, quantity_max))
        self.assertEqual(
            removed,
            {
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 0),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 2),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 3),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 4),
            },
        )
        self.assertEqual(added, set())

    def test_resource_acceptance_delta_is_exact(self) -> None:
        removed: set[tuple[AccountingMode, int, int]] = set()
        added: set[tuple[AccountingMode, int, int]] = set()
        for mode in AccountingMode:
            for quantity_max in range(5):
                for quantity_atoms in range(6):
                    candidate_policy = policy(mode, quantity_max)
                    candidate_resource = resource(quantity_atoms)
                    baseline_accepts = (
                        decide_baseline_resource(
                            candidate_policy, candidate_resource
                        ).kind
                        is BaselineDecisionKind.ACCEPT
                    )
                    proposed_accepts = (
                        decide_rfc0003_resource_quantity(
                            candidate_policy, candidate_resource
                        ).kind
                        is ProposedDecisionKind.ACCEPT
                    )
                    if baseline_accepts and not proposed_accepts:
                        removed.add((mode, quantity_max, quantity_atoms))
                    if proposed_accepts and not baseline_accepts:
                        added.add((mode, quantity_max, quantity_atoms))
        self.assertEqual(
            removed,
            {
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 2, 1),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 3, 1),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 4, 1),
            },
        )
        self.assertEqual(added, set())

    def test_reason_only_delta_for_common_valid_policies_is_exact(self) -> None:
        changed: set[tuple[AccountingMode, int, int]] = set()
        for mode in AccountingMode:
            for quantity_max in range(5):
                candidate_policy = policy(mode, quantity_max)
                baseline_policy = decide_baseline_policy(candidate_policy)
                proposed_policy = decide_rfc0003_policy_construction(
                    candidate_policy
                )
                if (
                    baseline_policy.kind is not BaselineDecisionKind.ACCEPT
                    or proposed_policy.kind is not ProposedDecisionKind.ACCEPT
                ):
                    continue
                for quantity_atoms in range(6):
                    baseline = decide_baseline_resource(
                        candidate_policy, resource(quantity_atoms)
                    )
                    proposed = decide_rfc0003_resource_quantity(
                        candidate_policy, resource(quantity_atoms)
                    )
                    if (
                        baseline.kind.value == proposed.kind.value
                        and baseline.reason.value != proposed.reason.value
                    ):
                        changed.add((mode, quantity_max, quantity_atoms))
        self.assertEqual(
            changed,
            {
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1, 0),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1, 2),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1, 3),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1, 4),
                (AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1, 5),
            },
        )

    def test_unit_mismatch_and_non_lifecycle_relations_are_unchanged(self) -> None:
        for mode in AccountingMode:
            maximum = 1 if mode is AccountingMode.LIFECYCLE_NON_FUNGIBLE else 3
            for quantity_atoms in range(4):
                with self.subTest(mode=mode, quantity_atoms=quantity_atoms):
                    candidate_policy = policy(mode, maximum)
                    candidate_resource = resource(quantity_atoms, unit_id=UNIT_V)
                    baseline = decide_baseline_resource(
                        candidate_policy, candidate_resource
                    )
                    proposed = decide_rfc0003_resource_quantity(
                        candidate_policy, candidate_resource
                    )
                    self.assertEqual(baseline.kind.value, proposed.kind.value)
                    self.assertEqual(baseline.reason.value, proposed.reason.value)


class ProposedCounterexampleRecordTests(unittest.TestCase):
    """RFC-0003 findings remain complete and executable."""

    def test_findings_have_required_review_fields(self) -> None:
        document = json.loads(COUNTEREXAMPLES.read_text(encoding="utf-8"))
        self.assertIn("non-normative unless RFC-0003 is accepted", document["normative_status"])
        required = {
            "boundary",
            "attacker_capabilities",
            "preconditions",
            "invariant",
            "minimal_counterexample",
            "expected_result",
            "formal_or_property_obligation",
            "residual_risk",
        }
        for finding in document["findings"]:
            with self.subTest(finding=finding["id"]):
                self.assertTrue(required.issubset(finding))

    def test_every_counterexample_matches_proposed_oracle(self) -> None:
        document = json.loads(COUNTEREXAMPLES.read_text(encoding="utf-8"))
        for finding in document["findings"]:
            example = finding["minimal_counterexample"]
            expected = finding["expected_result"]
            policy_input = example["policy"]
            candidate_policy = PolicyCandidateV1(
                schema_version=policy_input["schema_version"],
                accounting_mode=AccountingMode(policy_input["accounting_mode"]),
                unit_id=policy_input["unit_id"],
                quantity_max=policy_input["quantity_max"],
                validity_start_epoch=policy_input["validity_start_epoch"],
                validity_end_epoch=policy_input["validity_end_epoch"],
            )
            if example["operation"] == "decide_rfc0003_policy_construction":
                actual = decide_rfc0003_policy_construction(candidate_policy)
            else:
                resource_input = example["resource"]
                actual = decide_rfc0003_resource_quantity(
                    candidate_policy,
                    ResourceQuantityCandidateV1(
                        unit_id=resource_input["unit_id"],
                        quantity_atoms=resource_input["quantity_atoms"],
                    ),
                )
            with self.subTest(finding=finding["id"]):
                self.assertEqual(actual.kind, ProposedDecisionKind(expected["decision"]))
                self.assertEqual(actual.reason, ProposedReason(expected["reason"]))

    def test_every_recorded_baseline_result_matches_frozen_oracle(self) -> None:
        document = json.loads(COUNTEREXAMPLES.read_text(encoding="utf-8"))
        for finding in document["findings"]:
            example = finding["minimal_counterexample"]
            expected = finding["baseline_result"]
            policy_input = example["policy"]
            candidate_policy = PolicyCandidateV1(
                schema_version=policy_input["schema_version"],
                accounting_mode=AccountingMode(policy_input["accounting_mode"]),
                unit_id=policy_input["unit_id"],
                quantity_max=policy_input["quantity_max"],
                validity_start_epoch=policy_input["validity_start_epoch"],
                validity_end_epoch=policy_input["validity_end_epoch"],
            )
            if example["operation"] == "decide_rfc0003_policy_construction":
                actual = decide_baseline_policy(candidate_policy)
            else:
                resource_input = example["resource"]
                actual = decide_baseline_resource(
                    candidate_policy,
                    ResourceQuantityCandidateV1(
                        unit_id=resource_input["unit_id"],
                        quantity_atoms=resource_input["quantity_atoms"],
                    ),
                )
            with self.subTest(finding=finding["id"]):
                self.assertEqual(actual.kind.value, expected["decision"])
                self.assertEqual(actual.reason.value, expected["reason"])


if __name__ == "__main__":
    unittest.main()
