//! Compile-time ceilings and validated machine-policy limits.

use crate::{LimitFieldV1, PolicyValidationErrorV1};

/// Public, non-authoritative candidate for v1 machine limits.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PolicyLimitsCandidateV1 {
    /// Maximum complete transition-envelope bytes.
    pub max_envelope_bytes: u32,
    /// Maximum bytes in one resource body.
    pub max_resource_bytes: u32,
    /// Maximum consumed-resource count.
    pub max_consumed_resources: u16,
    /// Maximum referenced-resource count.
    pub max_referenced_resources: u16,
    /// Maximum created-resource count.
    pub max_created_resources: u16,
    /// Maximum logic-claim count.
    pub max_logic_claims: u16,
    /// Maximum transformation-claim count.
    pub max_transformation_claims: u16,
    /// Maximum authority-claim count.
    pub max_authority_claims: u16,
    /// Maximum data-availability-claim count.
    pub max_data_availability_claims: u16,
    /// Maximum accounting-row count.
    pub max_accounting_rows: u16,
    /// Maximum evidence-reference count.
    pub max_evidence_references: u16,
    /// Maximum bytes in one proof artifact.
    pub max_proof_artifact_bytes: u32,
    /// Maximum bytes across all transition proof artifacts.
    pub max_total_proof_bytes: u32,
    /// Maximum deterministic verifier-cost units for one transition attempt.
    pub max_total_verifier_cost_units: u64,
    /// Maximum nested-object depth.
    pub max_nesting_depth: u16,
    /// Maximum storage-write bytes planned by one transition.
    pub max_storage_write_bytes: u32,
}

/// Validated machine-policy limits bounded by the v1 protocol ceilings.
///
/// Zero is retained for limits where policy may disable a surface. The
/// resource-byte limit has a 603-byte minimum because this v1 implementation
/// admits both frozen `ResourceWireV1` forms.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PolicyLimitsV1(PolicyLimitsCandidateV1);

impl PolicyLimitsV1 {
    /// Protocol ceiling for complete transition envelopes.
    pub const MAX_ENVELOPE_BYTES: u32 = 4 * 1024 * 1024;
    /// Protocol ceiling for one resource body.
    pub const MAX_RESOURCE_BYTES: u32 = 16 * 1024;
    /// Protocol ceiling for consumed resources.
    pub const MAX_CONSUMED_RESOURCES: u16 = 256;
    /// Protocol ceiling for referenced resources.
    pub const MAX_REFERENCED_RESOURCES: u16 = 256;
    /// Protocol ceiling for created resources.
    pub const MAX_CREATED_RESOURCES: u16 = 256;
    /// Protocol ceiling for logic claims.
    pub const MAX_LOGIC_CLAIMS: u16 = 768;
    /// Protocol ceiling for transformation claims.
    pub const MAX_TRANSFORMATION_CLAIMS: u16 = 256;
    /// Protocol ceiling for authority claims.
    pub const MAX_AUTHORITY_CLAIMS: u16 = 768;
    /// Protocol ceiling for data-availability claims.
    pub const MAX_DATA_AVAILABILITY_CLAIMS: u16 = 256;
    /// Protocol ceiling for accounting rows.
    pub const MAX_ACCOUNTING_ROWS: u16 = 512;
    /// Protocol ceiling for evidence references.
    pub const MAX_EVIDENCE_REFERENCES: u16 = 512;
    /// Protocol ceiling for one proof artifact.
    pub const MAX_PROOF_ARTIFACT_BYTES: u32 = 1024 * 1024;
    /// Protocol ceiling for total proof bytes.
    pub const MAX_TOTAL_PROOF_BYTES: u32 = 3 * 1024 * 1024;
    /// Protocol ceiling for total verifier-cost units.
    pub const MAX_TOTAL_VERIFIER_COST_UNITS: u64 = 281_474_976_710_655;
    /// Protocol ceiling for nested-object depth.
    pub const MAX_NESTING_DEPTH: u16 = 16;
    /// Protocol ceiling for storage-write bytes.
    pub const MAX_STORAGE_WRITE_BYTES: u32 = 8 * 1024 * 1024;
    /// Minimum bytes required for the complete present-expiry resource form.
    pub const MIN_RESOURCE_WIRE_V1_BYTES: u32 = 603;

    /// Returns the strict reference-default profile from the specification.
    #[must_use]
    pub const fn strict_default() -> Self {
        Self(PolicyLimitsCandidateV1 {
            max_envelope_bytes: 1024 * 1024,
            max_resource_bytes: 4 * 1024,
            max_consumed_resources: 64,
            max_referenced_resources: 64,
            max_created_resources: 64,
            max_logic_claims: 192,
            max_transformation_claims: 64,
            max_authority_claims: 192,
            max_data_availability_claims: 64,
            max_accounting_rows: 128,
            max_evidence_references: 128,
            max_proof_artifact_bytes: 256 * 1024,
            max_total_proof_bytes: 768 * 1024,
            max_total_verifier_cost_units: 4_294_967_295,
            max_nesting_depth: 8,
            max_storage_write_bytes: 2 * 1024 * 1024,
        })
    }

    /// Returns the exact v1 protocol-ceiling profile.
    #[must_use]
    pub const fn protocol_ceiling() -> Self {
        Self(PolicyLimitsCandidateV1 {
            max_envelope_bytes: Self::MAX_ENVELOPE_BYTES,
            max_resource_bytes: Self::MAX_RESOURCE_BYTES,
            max_consumed_resources: Self::MAX_CONSUMED_RESOURCES,
            max_referenced_resources: Self::MAX_REFERENCED_RESOURCES,
            max_created_resources: Self::MAX_CREATED_RESOURCES,
            max_logic_claims: Self::MAX_LOGIC_CLAIMS,
            max_transformation_claims: Self::MAX_TRANSFORMATION_CLAIMS,
            max_authority_claims: Self::MAX_AUTHORITY_CLAIMS,
            max_data_availability_claims: Self::MAX_DATA_AVAILABILITY_CLAIMS,
            max_accounting_rows: Self::MAX_ACCOUNTING_ROWS,
            max_evidence_references: Self::MAX_EVIDENCE_REFERENCES,
            max_proof_artifact_bytes: Self::MAX_PROOF_ARTIFACT_BYTES,
            max_total_proof_bytes: Self::MAX_TOTAL_PROOF_BYTES,
            max_total_verifier_cost_units: Self::MAX_TOTAL_VERIFIER_COST_UNITS,
            max_nesting_depth: Self::MAX_NESTING_DEPTH,
            max_storage_write_bytes: Self::MAX_STORAGE_WRITE_BYTES,
        })
    }

    /// Returns a copy of the validated fixed-width values.
    #[must_use]
    pub const fn as_candidate(self) -> PolicyLimitsCandidateV1 {
        self.0
    }

    /// Returns the maximum consumed-resource count.
    #[must_use]
    pub const fn max_consumed_resources(self) -> u16 {
        self.0.max_consumed_resources
    }

    /// Returns the maximum referenced-resource count.
    #[must_use]
    pub const fn max_referenced_resources(self) -> u16 {
        self.0.max_referenced_resources
    }

    /// Returns the maximum created-resource count.
    #[must_use]
    pub const fn max_created_resources(self) -> u16 {
        self.0.max_created_resources
    }

    /// Returns the per-artifact proof-byte limit.
    #[must_use]
    pub const fn max_proof_artifact_bytes(self) -> u32 {
        self.0.max_proof_artifact_bytes
    }

    /// Returns the total proof-byte limit.
    #[must_use]
    pub const fn max_total_proof_bytes(self) -> u32 {
        self.0.max_total_proof_bytes
    }

    /// Returns the total verifier-cost budget.
    #[must_use]
    pub const fn max_total_verifier_cost_units(self) -> u64 {
        self.0.max_total_verifier_cost_units
    }
}

impl TryFrom<PolicyLimitsCandidateV1> for PolicyLimitsV1 {
    type Error = PolicyValidationErrorV1;

    /// Validates every field in normative declaration order.
    ///
    /// # Errors
    ///
    /// Returns the first ceiling violation, then checks that both frozen
    /// `ResourceWireV1` forms fit the resource-byte limit.
    fn try_from(candidate: PolicyLimitsCandidateV1) -> Result<Self, Self::Error> {
        validate_candidate(candidate)?;
        Ok(Self(candidate))
    }
}

fn ensure_at_most(
    field: LimitFieldV1,
    actual: u64,
    ceiling: u64,
) -> Result<(), PolicyValidationErrorV1> {
    if actual > ceiling {
        Err(PolicyValidationErrorV1::LimitExceedsProtocolCeiling {
            field,
            actual,
            ceiling,
        })
    } else {
        Ok(())
    }
}

fn validate_candidate(candidate: PolicyLimitsCandidateV1) -> Result<(), PolicyValidationErrorV1> {
    validate_ingress_and_resource_count_limits(&candidate)?;
    validate_claim_and_accounting_limits(&candidate)?;
    validate_proof_and_runtime_limits(&candidate)?;
    validate_resource_wire_minimum(candidate.max_resource_bytes)
}

fn validate_ingress_and_resource_count_limits(
    candidate: &PolicyLimitsCandidateV1,
) -> Result<(), PolicyValidationErrorV1> {
    ensure_at_most(
        LimitFieldV1::EnvelopeBytes,
        u64::from(candidate.max_envelope_bytes),
        u64::from(PolicyLimitsV1::MAX_ENVELOPE_BYTES),
    )?;
    ensure_at_most(
        LimitFieldV1::ResourceBytes,
        u64::from(candidate.max_resource_bytes),
        u64::from(PolicyLimitsV1::MAX_RESOURCE_BYTES),
    )?;
    ensure_at_most(
        LimitFieldV1::ConsumedResources,
        u64::from(candidate.max_consumed_resources),
        u64::from(PolicyLimitsV1::MAX_CONSUMED_RESOURCES),
    )?;
    ensure_at_most(
        LimitFieldV1::ReferencedResources,
        u64::from(candidate.max_referenced_resources),
        u64::from(PolicyLimitsV1::MAX_REFERENCED_RESOURCES),
    )?;
    ensure_at_most(
        LimitFieldV1::CreatedResources,
        u64::from(candidate.max_created_resources),
        u64::from(PolicyLimitsV1::MAX_CREATED_RESOURCES),
    )?;
    Ok(())
}

fn validate_claim_and_accounting_limits(
    candidate: &PolicyLimitsCandidateV1,
) -> Result<(), PolicyValidationErrorV1> {
    ensure_at_most(
        LimitFieldV1::LogicClaims,
        u64::from(candidate.max_logic_claims),
        u64::from(PolicyLimitsV1::MAX_LOGIC_CLAIMS),
    )?;
    ensure_at_most(
        LimitFieldV1::TransformationClaims,
        u64::from(candidate.max_transformation_claims),
        u64::from(PolicyLimitsV1::MAX_TRANSFORMATION_CLAIMS),
    )?;
    ensure_at_most(
        LimitFieldV1::AuthorityClaims,
        u64::from(candidate.max_authority_claims),
        u64::from(PolicyLimitsV1::MAX_AUTHORITY_CLAIMS),
    )?;
    ensure_at_most(
        LimitFieldV1::DataAvailabilityClaims,
        u64::from(candidate.max_data_availability_claims),
        u64::from(PolicyLimitsV1::MAX_DATA_AVAILABILITY_CLAIMS),
    )?;
    ensure_at_most(
        LimitFieldV1::AccountingRows,
        u64::from(candidate.max_accounting_rows),
        u64::from(PolicyLimitsV1::MAX_ACCOUNTING_ROWS),
    )?;
    ensure_at_most(
        LimitFieldV1::EvidenceReferences,
        u64::from(candidate.max_evidence_references),
        u64::from(PolicyLimitsV1::MAX_EVIDENCE_REFERENCES),
    )?;
    Ok(())
}

fn validate_proof_and_runtime_limits(
    candidate: &PolicyLimitsCandidateV1,
) -> Result<(), PolicyValidationErrorV1> {
    ensure_at_most(
        LimitFieldV1::ProofArtifactBytes,
        u64::from(candidate.max_proof_artifact_bytes),
        u64::from(PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES),
    )?;
    ensure_at_most(
        LimitFieldV1::TotalProofBytes,
        u64::from(candidate.max_total_proof_bytes),
        u64::from(PolicyLimitsV1::MAX_TOTAL_PROOF_BYTES),
    )?;
    ensure_at_most(
        LimitFieldV1::TotalVerifierCostUnits,
        candidate.max_total_verifier_cost_units,
        PolicyLimitsV1::MAX_TOTAL_VERIFIER_COST_UNITS,
    )?;
    ensure_at_most(
        LimitFieldV1::NestingDepth,
        u64::from(candidate.max_nesting_depth),
        u64::from(PolicyLimitsV1::MAX_NESTING_DEPTH),
    )?;
    ensure_at_most(
        LimitFieldV1::StorageWriteBytes,
        u64::from(candidate.max_storage_write_bytes),
        u64::from(PolicyLimitsV1::MAX_STORAGE_WRITE_BYTES),
    )?;
    Ok(())
}

fn validate_resource_wire_minimum(max_resource_bytes: u32) -> Result<(), PolicyValidationErrorV1> {
    if max_resource_bytes < PolicyLimitsV1::MIN_RESOURCE_WIRE_V1_BYTES {
        return Err(PolicyValidationErrorV1::ResourceWireLimitTooSmall {
            actual: max_resource_bytes,
            minimum: PolicyLimitsV1::MIN_RESOURCE_WIRE_V1_BYTES,
        });
    }
    Ok(())
}

#[cfg(kani)]
mod kani_harnesses {
    use super::{PolicyLimitsCandidateV1, PolicyLimitsV1};

    #[kani::proof]
    fn resource_limit_accepts_exact_v1_interval() {
        let mut candidate: PolicyLimitsCandidateV1 =
            PolicyLimitsV1::strict_default().as_candidate();
        candidate.max_resource_bytes = kani::any();
        let accepted = PolicyLimitsV1::try_from(candidate).is_ok();
        let in_range = PolicyLimitsV1::MIN_RESOURCE_WIRE_V1_BYTES <= candidate.max_resource_bytes
            && candidate.max_resource_bytes <= PolicyLimitsV1::MAX_RESOURCE_BYTES;
        assert_eq!(accepted, in_range);
    }
}
