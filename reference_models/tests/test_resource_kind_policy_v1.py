"""Independent boundary tests for the ResourceKindPolicyV1 quantity oracle."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from reference_models.resource_kind_policy_v1 import (
    U128_MAX,
    U64_MAX,
    AccountingMode,
    DecisionKind,
    PolicyCandidateV1,
    Reason,
    ResourceQuantityCandidateV1,
    decide_policy_construction,
    decide_resource_quantity,
)


UNIT_U = "unit-u"
UNIT_V = "unit-v"
COUNTEREXAMPLES = (
    Path(__file__).resolve().parents[1]
    / "resource_kind_policy_v1_counterexamples.json"
)


def policy(
    mode: AccountingMode,
    quantity_max: int,
    *,
    schema_version: int = 1,
    validity_start_epoch: int = 0,
    validity_end_epoch: int = U64_MAX,
) -> PolicyCandidateV1:
    """Build inert policy input with only fields relevant to this oracle."""

    return PolicyCandidateV1(
        schema_version=schema_version,
        accounting_mode=mode,
        unit_id=UNIT_U,
        quantity_max=quantity_max,
        validity_start_epoch=validity_start_epoch,
        validity_end_epoch=validity_end_epoch,
    )


def resource(quantity_atoms: int, *, unit_id: str = UNIT_U) -> ResourceQuantityCandidateV1:
    """Build inert resource quantity input."""

    return ResourceQuantityCandidateV1(unit_id=unit_id, quantity_atoms=quantity_atoms)


class PolicyConstructionTests(unittest.TestCase):
    """Policy construction expresses only rules stated by the draft."""

    def test_every_mode_accepts_each_u128_maximum_boundary(self) -> None:
        for mode in AccountingMode:
            for quantity_max in (0, 1, 2, U128_MAX):
                with self.subTest(mode=mode, quantity_max=quantity_max):
                    decision = decide_policy_construction(policy(mode, quantity_max))
                    self.assertEqual(decision.kind, DecisionKind.ACCEPT)
                    self.assertEqual(decision.reason, Reason.POLICY_SHAPE_ACCEPTED)

    def test_lifecycle_maxima_zero_one_and_greater_than_one_construct(self) -> None:
        for quantity_max in (0, 1, 2, U128_MAX):
            with self.subTest(quantity_max=quantity_max):
                decision = decide_policy_construction(
                    policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, quantity_max)
                )
                self.assertEqual(decision.kind, DecisionKind.ACCEPT)

    def test_rejects_unsupported_schema_before_invalid_validity(self) -> None:
        decision = decide_policy_construction(
            policy(
                AccountingMode.CONSERVED_FUNGIBLE,
                1,
                schema_version=2,
                validity_start_epoch=2,
                validity_end_epoch=1,
            )
        )
        self.assertEqual(decision.kind, DecisionKind.REJECT)
        self.assertEqual(decision.reason, Reason.UNSUPPORTED_SCHEMA)

    def test_boolean_is_not_a_supported_schema_integer(self) -> None:
        decision = decide_policy_construction(
            policy(
                AccountingMode.CONSERVED_FUNGIBLE,
                1,
                schema_version=True,
            )
        )
        self.assertEqual(decision.reason, Reason.UNSUPPORTED_SCHEMA)

    def test_rejects_reversed_validity_window(self) -> None:
        decision = decide_policy_construction(
            policy(
                AccountingMode.CONSERVED_FUNGIBLE,
                1,
                validity_start_epoch=2,
                validity_end_epoch=1,
            )
        )
        self.assertEqual(decision.reason, Reason.INVALID_VALIDITY_WINDOW)

    def test_rejects_validity_epoch_outside_u64(self) -> None:
        for start, end in ((-1, 0), (0, U64_MAX + 1)):
            with self.subTest(start=start, end=end):
                decision = decide_policy_construction(
                    policy(
                        AccountingMode.CONSERVED_FUNGIBLE,
                        1,
                        validity_start_epoch=start,
                        validity_end_epoch=end,
                    )
                )
                self.assertEqual(decision.reason, Reason.VALIDITY_EPOCH_OUT_OF_RANGE)

    def test_rejects_quantity_max_outside_u128(self) -> None:
        for quantity_max in (-1, U128_MAX + 1, True):
            with self.subTest(quantity_max=quantity_max):
                decision = decide_policy_construction(
                    policy(AccountingMode.CONSERVED_FUNGIBLE, quantity_max)
                )
                self.assertEqual(decision.reason, Reason.QUANTITY_MAX_OUT_OF_RANGE)


class ResourceQuantityDecisionTests(unittest.TestCase):
    """Resource admission composes general and mode-specific quantity rules."""

    def test_unit_mismatch_rejects_for_every_mode(self) -> None:
        for mode in AccountingMode:
            with self.subTest(mode=mode):
                decision = decide_resource_quantity(
                    policy(mode, U128_MAX), resource(1, unit_id=UNIT_V)
                )
                self.assertEqual(decision.kind, DecisionKind.REJECT)
                self.assertEqual(decision.reason, Reason.UNIT_MISMATCH)

    def test_zero_rejects_for_every_mode(self) -> None:
        for mode in AccountingMode:
            with self.subTest(mode=mode):
                decision = decide_resource_quantity(policy(mode, 1), resource(0))
                self.assertEqual(decision.kind, DecisionKind.REJECT)
                self.assertEqual(
                    decision.reason,
                    Reason.ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION,
                )

    def test_non_lifecycle_modes_accept_exact_maximum(self) -> None:
        modes = (
            AccountingMode.CONSERVED_FUNGIBLE,
            AccountingMode.AUTHORITY_MINTABLE_FUNGIBLE,
            AccountingMode.TRANSFORMABLE,
        )
        for mode in modes:
            for quantity_max in (1, 2, U128_MAX):
                with self.subTest(mode=mode, quantity_max=quantity_max):
                    decision = decide_resource_quantity(
                        policy(mode, quantity_max), resource(quantity_max)
                    )
                    self.assertEqual(decision.kind, DecisionKind.ACCEPT)
                    self.assertEqual(decision.reason, Reason.RESOURCE_QUANTITY_ACCEPTED)

    def test_non_lifecycle_modes_reject_quantity_above_maximum(self) -> None:
        modes = (
            AccountingMode.CONSERVED_FUNGIBLE,
            AccountingMode.AUTHORITY_MINTABLE_FUNGIBLE,
            AccountingMode.TRANSFORMABLE,
        )
        for mode in modes:
            with self.subTest(mode=mode):
                decision = decide_resource_quantity(policy(mode, 1), resource(2))
                self.assertEqual(decision.reason, Reason.QUANTITY_EXCEEDS_MAXIMUM)

    def test_u128_maximum_is_accepted_without_truncation(self) -> None:
        for mode in (
            AccountingMode.CONSERVED_FUNGIBLE,
            AccountingMode.AUTHORITY_MINTABLE_FUNGIBLE,
            AccountingMode.TRANSFORMABLE,
        ):
            with self.subTest(mode=mode):
                decision = decide_resource_quantity(
                    policy(mode, U128_MAX), resource(U128_MAX)
                )
                self.assertEqual(decision.kind, DecisionKind.ACCEPT)

    def test_quantity_above_u128_rejects_before_maximum_comparison(self) -> None:
        decision = decide_resource_quantity(
            policy(AccountingMode.CONSERVED_FUNGIBLE, U128_MAX),
            resource(U128_MAX + 1),
        )
        self.assertEqual(decision.reason, Reason.QUANTITY_OUT_OF_RANGE)

    def test_lifecycle_maximum_zero_constructs_but_admits_no_resource(self) -> None:
        candidate_policy = policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, 0)
        self.assertEqual(
            decide_policy_construction(candidate_policy).kind, DecisionKind.ACCEPT
        )
        self.assertEqual(
            decide_resource_quantity(candidate_policy, resource(1)).reason,
            Reason.QUANTITY_EXCEEDS_MAXIMUM,
        )

    def test_lifecycle_maximum_one_admits_only_one(self) -> None:
        candidate_policy = policy(AccountingMode.LIFECYCLE_NON_FUNGIBLE, 1)
        self.assertEqual(
            decide_resource_quantity(candidate_policy, resource(1)).kind,
            DecisionKind.ACCEPT,
        )
        self.assertEqual(
            decide_resource_quantity(candidate_policy, resource(2)).reason,
            Reason.QUANTITY_EXCEEDS_MAXIMUM,
        )

    def test_lifecycle_maximum_greater_than_one_still_admits_only_one(self) -> None:
        for quantity_max in (2, U128_MAX):
            with self.subTest(quantity_max=quantity_max):
                candidate_policy = policy(
                    AccountingMode.LIFECYCLE_NON_FUNGIBLE, quantity_max
                )
                self.assertEqual(
                    decide_policy_construction(candidate_policy).kind,
                    DecisionKind.ACCEPT,
                )
                self.assertEqual(
                    decide_resource_quantity(candidate_policy, resource(1)).kind,
                    DecisionKind.ACCEPT,
                )
                self.assertEqual(
                    decide_resource_quantity(candidate_policy, resource(quantity_max)).reason,
                    Reason.LIFECYCLE_QUANTITY_MUST_EQUAL_ONE,
                )

    def test_evidence_only_zero_is_not_implicitly_a_marker(self) -> None:
        decision = decide_resource_quantity(
            policy(AccountingMode.EVIDENCE_ONLY, 1), resource(0)
        )
        self.assertEqual(
            decision.reason,
            Reason.ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION,
        )

    def test_evidence_only_positive_acceptance_carries_nonclaim(self) -> None:
        decision = decide_resource_quantity(
            policy(AccountingMode.EVIDENCE_ONLY, U128_MAX), resource(U128_MAX)
        )
        self.assertEqual(decision.kind, DecisionKind.ACCEPT)
        self.assertEqual(
            decision.reason, Reason.EVIDENCE_ONLY_QUANTITY_STRUCTURALLY_ACCEPTED
        )
        self.assertIn("nonmonetary semantics remain unestablished", decision.non_claims)

    def test_small_domain_matches_derived_predicates(self) -> None:
        for mode in AccountingMode:
            for quantity_max in range(5):
                for quantity_atoms in range(6):
                    with self.subTest(
                        mode=mode,
                        quantity_max=quantity_max,
                        quantity_atoms=quantity_atoms,
                    ):
                        decision = decide_resource_quantity(
                            policy(mode, quantity_max), resource(quantity_atoms)
                        )
                        if mode is AccountingMode.LIFECYCLE_NON_FUNGIBLE:
                            expected = quantity_atoms == 1 and quantity_max >= 1
                        else:
                            expected = 1 <= quantity_atoms <= quantity_max
                        self.assertEqual(decision.kind is DecisionKind.ACCEPT, expected)


class CounterexampleRecordTests(unittest.TestCase):
    """The machine-readable findings remain complete and replayable."""

    def test_findings_have_required_review_fields(self) -> None:
        document = json.loads(COUNTEREXAMPLES.read_text(encoding="utf-8"))
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

    def test_every_executable_counterexample_matches_oracle(self) -> None:
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
            if example["operation"] == "decide_policy_construction":
                actual = decide_policy_construction(candidate_policy)
            else:
                resource_input = example["resource"]
                actual = decide_resource_quantity(
                    candidate_policy,
                    ResourceQuantityCandidateV1(
                        unit_id=resource_input["unit_id"],
                        quantity_atoms=resource_input["quantity_atoms"],
                    ),
                )
            with self.subTest(finding=finding["id"]):
                self.assertEqual(actual.kind, DecisionKind(expected["decision"]))
                self.assertEqual(actual.reason, Reason(expected["reason"]))


if __name__ == "__main__":
    unittest.main()
