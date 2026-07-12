"""Proposed RFC-0003 ResourceKindPolicyV1 quantity decisions.

This module encodes a supplied semantic amendment independently of production
code.  It is non-authoritative unless RFC-0003 is accepted through the governed
RFC process.  The frozen prior-specification oracle remains in
``resource_kind_policy_v1.py`` and is imported only for its inert input types and
closed accounting-mode enum.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from reference_models.resource_kind_policy_v1 import (
    U128_MAX,
    U64_MAX,
    AccountingMode,
    PolicyCandidateV1,
    ResourceQuantityCandidateV1,
)


class ProposedDecisionKind(str, Enum):
    """Binary result of the non-normative RFC-0003 proposal."""

    ACCEPT = "accept"
    REJECT = "reject"


class ProposedReason(str, Enum):
    """Transparent proposal reasons, not stable protocol reject codes."""

    POLICY_SHAPE_ACCEPTED = "policy_shape_accepted"
    RESOURCE_QUANTITY_ACCEPTED = "resource_quantity_accepted"
    EVIDENCE_ONLY_QUANTITY_STRUCTURALLY_ACCEPTED = (
        "evidence_only_quantity_structurally_accepted"
    )
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    UNSUPPORTED_ACCOUNTING_MODE = "unsupported_accounting_mode"
    VALIDITY_EPOCH_OUT_OF_RANGE = "validity_epoch_out_of_range"
    INVALID_VALIDITY_WINDOW = "invalid_validity_window"
    QUANTITY_MAX_OUT_OF_RANGE = "quantity_max_out_of_range"
    LIFECYCLE_POLICY_MAXIMUM_MUST_EQUAL_ONE = (
        "lifecycle_policy_maximum_must_equal_one"
    )
    UNIT_MISMATCH = "unit_mismatch"
    QUANTITY_OUT_OF_RANGE = "quantity_out_of_range"
    LIFECYCLE_QUANTITY_MUST_EQUAL_ONE = "lifecycle_quantity_must_equal_one"
    ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION = (
        "zero_quantity_requires_explicit_marker_permission"
    )
    QUANTITY_EXCEEDS_MAXIMUM = "quantity_exceeds_maximum"


@dataclass(frozen=True)
class ProposedDecision:
    """Non-authoritative RFC-0003 decision and explicit non-claims."""

    kind: ProposedDecisionKind
    reason: ProposedReason
    non_claims: tuple[str, ...] = ()


def _is_protocol_unsigned(value: object, maximum: int) -> bool:
    """Return whether a host value is an exact non-boolean protocol integer."""

    return type(value) is int and 0 <= value <= maximum


def _accept(reason: ProposedReason, *non_claims: str) -> ProposedDecision:
    """Construct a proposed accept decision."""

    return ProposedDecision(ProposedDecisionKind.ACCEPT, reason, tuple(non_claims))


def _reject(reason: ProposedReason) -> ProposedDecision:
    """Construct a proposed reject decision."""

    return ProposedDecision(ProposedDecisionKind.REJECT, reason)


def decide_rfc0003_policy_construction(
    candidate: PolicyCandidateV1,
) -> ProposedDecision:
    """Apply the proposed RFC-0003 policy-construction relation.

    For typed semantic candidates, precedence is schema, validity window, then
    lifecycle maximum.  The closed enum check and host-width checks fail closed
    at their representation boundaries.  A non-lifecycle maximum of zero is a
    constructible empty candidate; a lifecycle maximum must be exactly one.

    Complexity is O(1), the function has no side effects, and acceptance creates
    no authenticated policy capability.
    """

    if type(candidate.schema_version) is not int or candidate.schema_version != 1:
        return _reject(ProposedReason.UNSUPPORTED_SCHEMA)
    if not isinstance(candidate.accounting_mode, AccountingMode):
        return _reject(ProposedReason.UNSUPPORTED_ACCOUNTING_MODE)
    if not _is_protocol_unsigned(candidate.validity_start_epoch, U64_MAX):
        return _reject(ProposedReason.VALIDITY_EPOCH_OUT_OF_RANGE)
    if not _is_protocol_unsigned(candidate.validity_end_epoch, U64_MAX):
        return _reject(ProposedReason.VALIDITY_EPOCH_OUT_OF_RANGE)
    if candidate.validity_start_epoch > candidate.validity_end_epoch:
        return _reject(ProposedReason.INVALID_VALIDITY_WINDOW)
    if not _is_protocol_unsigned(candidate.quantity_max, U128_MAX):
        return _reject(ProposedReason.QUANTITY_MAX_OUT_OF_RANGE)
    if (
        candidate.accounting_mode is AccountingMode.LIFECYCLE_NON_FUNGIBLE
        and candidate.quantity_max != 1
    ):
        return _reject(ProposedReason.LIFECYCLE_POLICY_MAXIMUM_MUST_EQUAL_ONE)
    non_claims = [
        "RFC-0003 remains proposed until governed acceptance",
        "policy authentication and activation remain unestablished",
    ]
    if candidate.quantity_max == 0:
        non_claims.append("an admitted resource may not exist")
    return _accept(ProposedReason.POLICY_SHAPE_ACCEPTED, *non_claims)


def decide_rfc0003_resource_quantity(
    candidate_policy: PolicyCandidateV1,
    candidate_resource: ResourceQuantityCandidateV1,
) -> ProposedDecision:
    """Apply the proposed RFC-0003 local unit and quantity relation.

    Policy construction completes first.  For a constructed typed policy,
    semantic reason precedence is unit mismatch, lifecycle exact-one, general
    zero, then maximum.  The host u128 check occurs at the representation
    boundary before the semantic quantity predicates.

    Complexity is O(1), the function has no side effects, and acceptance creates
    no resource or authority-bearing capability.
    """

    policy_decision = decide_rfc0003_policy_construction(candidate_policy)
    if policy_decision.kind is ProposedDecisionKind.REJECT:
        return policy_decision
    if candidate_resource.unit_id != candidate_policy.unit_id:
        return _reject(ProposedReason.UNIT_MISMATCH)
    if not _is_protocol_unsigned(candidate_resource.quantity_atoms, U128_MAX):
        return _reject(ProposedReason.QUANTITY_OUT_OF_RANGE)
    if (
        candidate_policy.accounting_mode is AccountingMode.LIFECYCLE_NON_FUNGIBLE
        and candidate_resource.quantity_atoms != 1
    ):
        return _reject(ProposedReason.LIFECYCLE_QUANTITY_MUST_EQUAL_ONE)
    if candidate_resource.quantity_atoms == 0:
        return _reject(
            ProposedReason.ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION
        )
    if candidate_resource.quantity_atoms > candidate_policy.quantity_max:
        return _reject(ProposedReason.QUANTITY_EXCEEDS_MAXIMUM)
    if candidate_policy.accounting_mode is AccountingMode.EVIDENCE_ONLY:
        return _accept(
            ProposedReason.EVIDENCE_ONLY_QUANTITY_STRUCTURALLY_ACCEPTED,
            "RFC-0003 remains proposed until governed acceptance",
            "evidence meaning remains unestablished",
            "nonmonetary and nonfungible interpretation remain unestablished",
            "v1 has no zero-marker permission",
        )
    return _accept(
        ProposedReason.RESOURCE_QUANTITY_ACCEPTED,
        "RFC-0003 remains proposed until governed acceptance",
        "transition accounting and authority remain unestablished",
    )


__all__ = [
    "ProposedDecision",
    "ProposedDecisionKind",
    "ProposedReason",
    "decide_rfc0003_policy_construction",
    "decide_rfc0003_resource_quantity",
]
