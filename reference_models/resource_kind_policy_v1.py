"""Literal ResourceKindPolicyV1 quantity decisions from the draft specification.

This module is deliberately small and non-authoritative.  It models only policy
construction shape and local resource unit/quantity admission.  It does not
authenticate a policy, construct a validated protocol capability, perform
transition accounting, or define canonical policy bytes.

The interpretation and its ambiguities are recorded in
``RESOURCE_KIND_POLICY_V1_ORACLE.md`` next to this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


U64_MAX = (1 << 64) - 1
U128_MAX = (1 << 128) - 1


class AccountingMode(str, Enum):
    """Closed accounting-mode set named by ResourceKindPolicyV1."""

    CONSERVED_FUNGIBLE = "ConservedFungible"
    AUTHORITY_MINTABLE_FUNGIBLE = "AuthorityMintableFungible"
    LIFECYCLE_NON_FUNGIBLE = "LifecycleNonFungible"
    TRANSFORMABLE = "Transformable"
    EVIDENCE_ONLY = "EvidenceOnly"


class DecisionKind(str, Enum):
    """Binary structural result returned by this bounded oracle."""

    ACCEPT = "accept"
    REJECT = "reject"


class Reason(str, Enum):
    """Transparent reasons local to this oracle, not protocol reject codes."""

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
    UNIT_MISMATCH = "unit_mismatch"
    QUANTITY_OUT_OF_RANGE = "quantity_out_of_range"
    ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION = (
        "zero_quantity_requires_explicit_marker_permission"
    )
    QUANTITY_EXCEEDS_MAXIMUM = "quantity_exceeds_maximum"
    LIFECYCLE_QUANTITY_MUST_EQUAL_ONE = "lifecycle_quantity_must_equal_one"


@dataclass(frozen=True)
class PolicyCandidateV1:
    """Inert policy fields needed by the quantity oracle.

    The object is intentionally constructible without validation.  Call
    :func:`decide_policy_construction` before interpreting it as a v1 policy
    shape.  ``unit_id`` stands for an already typed, nonzero ``UnitId``.
    """

    schema_version: int
    accounting_mode: AccountingMode
    unit_id: str
    quantity_max: int
    validity_start_epoch: int
    validity_end_epoch: int


@dataclass(frozen=True)
class ResourceQuantityCandidateV1:
    """Inert resource fields needed by the quantity oracle.

    ``unit_id`` stands for an already typed, nonzero ``UnitId``.  The quantity
    remains an untrusted Python value until the oracle checks its u128 range.
    """

    unit_id: str
    quantity_atoms: int


@dataclass(frozen=True)
class Decision:
    """Non-authoritative structural decision and its explicit non-claims."""

    kind: DecisionKind
    reason: Reason
    non_claims: tuple[str, ...] = ()


def _is_protocol_unsigned(value: object, maximum: int) -> bool:
    """Return whether ``value`` is an exact, non-boolean protocol integer."""

    return type(value) is int and 0 <= value <= maximum


def _accept(reason: Reason, *non_claims: str) -> Decision:
    """Construct a local accept decision."""

    return Decision(DecisionKind.ACCEPT, reason, tuple(non_claims))


def _reject(reason: Reason) -> Decision:
    """Construct a local reject decision."""

    return Decision(DecisionKind.REJECT, reason)


def decide_policy_construction(candidate: PolicyCandidateV1) -> Decision:
    """Decide the policy shape relevant to quantity admission.

    Checks are constant-time and side-effect free.  The local reason precedence
    is schema, closed accounting mode, epoch widths, validity ordering, then
    quantity-maximum width.  The draft does not assign stable reason codes or a
    complete within-stage precedence for this logical policy schema.

    No equality is imposed between ``LifecycleNonFungible`` and
    ``quantity_max == 1``.  The specification constrains lifecycle *resources*
    to quantity one and separately caps every resource at ``quantity_max``.
    """

    if type(candidate.schema_version) is not int or candidate.schema_version != 1:
        return _reject(Reason.UNSUPPORTED_SCHEMA)
    if not isinstance(candidate.accounting_mode, AccountingMode):
        return _reject(Reason.UNSUPPORTED_ACCOUNTING_MODE)
    if not _is_protocol_unsigned(candidate.validity_start_epoch, U64_MAX):
        return _reject(Reason.VALIDITY_EPOCH_OUT_OF_RANGE)
    if not _is_protocol_unsigned(candidate.validity_end_epoch, U64_MAX):
        return _reject(Reason.VALIDITY_EPOCH_OUT_OF_RANGE)
    if candidate.validity_start_epoch > candidate.validity_end_epoch:
        return _reject(Reason.INVALID_VALIDITY_WINDOW)
    if not _is_protocol_unsigned(candidate.quantity_max, U128_MAX):
        return _reject(Reason.QUANTITY_MAX_OUT_OF_RANGE)
    return _accept(
        Reason.POLICY_SHAPE_ACCEPTED,
        "policy authentication and activation remain unestablished",
        "policy construction does not guarantee an admitted resource exists",
    )


def decide_resource_quantity(
    candidate_policy: PolicyCandidateV1,
    candidate_resource: ResourceQuantityCandidateV1,
) -> Decision:
    """Decide local unit and quantity admission under an inert policy candidate.

    The policy shape is checked first.  Within the ResourcePolicy-stage slice,
    this oracle reports unit mismatch before numeric quantity errors.  It then
    checks u128 representation, the general zero rule, the policy maximum, and
    finally the exact lifecycle quantity.  This ordering only selects a local
    reason; the accept/reject relation follows the conjunction of all rules.

    Complexity is O(1).  The function has no side effects and constructs no
    authority-bearing value.
    """

    policy_decision = decide_policy_construction(candidate_policy)
    if policy_decision.kind is DecisionKind.REJECT:
        return policy_decision
    if candidate_resource.unit_id != candidate_policy.unit_id:
        return _reject(Reason.UNIT_MISMATCH)
    if not _is_protocol_unsigned(candidate_resource.quantity_atoms, U128_MAX):
        return _reject(Reason.QUANTITY_OUT_OF_RANGE)
    if candidate_resource.quantity_atoms == 0:
        return _reject(Reason.ZERO_QUANTITY_REQUIRES_EXPLICIT_MARKER_PERMISSION)
    if candidate_resource.quantity_atoms > candidate_policy.quantity_max:
        return _reject(Reason.QUANTITY_EXCEEDS_MAXIMUM)
    if (
        candidate_policy.accounting_mode is AccountingMode.LIFECYCLE_NON_FUNGIBLE
        and candidate_resource.quantity_atoms != 1
    ):
        return _reject(Reason.LIFECYCLE_QUANTITY_MUST_EQUAL_ONE)
    if candidate_policy.accounting_mode is AccountingMode.EVIDENCE_ONLY:
        return _accept(
            Reason.EVIDENCE_ONLY_QUANTITY_STRUCTURALLY_ACCEPTED,
            "nonmonetary semantics remain unestablished",
            "nonfungible interpretation remains unestablished",
            "zero-marker permission remains unavailable in the v1 schema",
        )
    return _accept(
        Reason.RESOURCE_QUANTITY_ACCEPTED,
        "transition accounting and authority remain unestablished",
    )


__all__ = [
    "U64_MAX",
    "U128_MAX",
    "AccountingMode",
    "Decision",
    "DecisionKind",
    "PolicyCandidateV1",
    "Reason",
    "ResourceQuantityCandidateV1",
    "decide_policy_construction",
    "decide_resource_quantity",
]
