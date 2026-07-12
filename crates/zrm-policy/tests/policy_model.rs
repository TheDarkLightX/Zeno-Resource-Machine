//! Public policy-model invariant and cross-field regression tests.

use zrm_crypto::SHA256_REFERENCE_V1_ID_BYTES;
use zrm_policy::{
    AccountingModeV1, AdmissionModeV1, AdmissionPolicyV1, DataAvailabilityRequirementV1,
    LimitFieldV1, MachinePolicyCandidateV1, MachinePolicyV1, PolicyLimitsCandidateV1,
    PolicyLimitsV1, PolicyObjectV1, PolicyValidationErrorV1, ProofModeV1, ResourceDimensionErrorV1,
    ResourceKindPolicyCandidateV1, ResourceKindPolicyV1, ValidationContextCandidateV1,
    ValidationContextV1, VerifierPolicyCandidateV1, VerifierPolicyV1,
};
use zrm_types::{CryptoSuiteId, QuantityAtoms, VerifierPolicyId, ZeroValueError};

#[derive(Debug)]
enum PolicyModelTestError {
    ZeroValue(ZeroValueError),
    PolicyValidation(PolicyValidationErrorV1),
}

impl From<ZeroValueError> for PolicyModelTestError {
    fn from(error: ZeroValueError) -> Self {
        Self::ZeroValue(error)
    }
}

impl From<PolicyValidationErrorV1> for PolicyModelTestError {
    fn from(error: PolicyValidationErrorV1) -> Self {
        Self::PolicyValidation(error)
    }
}

impl core::fmt::Display for PolicyModelTestError {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::ZeroValue(error) => write!(formatter, "invalid nonzero fixture: {error}"),
            Self::PolicyValidation(error) => write!(formatter, "invalid policy fixture: {error}"),
        }
    }
}

impl std::error::Error for PolicyModelTestError {}

type PolicyModelTestResult = Result<(), PolicyModelTestError>;

fn nonzero<T>(byte: u8) -> Result<T, ZeroValueError>
where
    T: TryFrom<[u8; 32], Error = ZeroValueError>,
{
    T::try_from([byte; 32])
}

fn strict_limits() -> PolicyLimitsCandidateV1 {
    PolicyLimitsV1::strict_default().as_candidate()
}

fn machine_candidate(
    admission_mode: AdmissionModeV1,
    admission_verifier_policy_id: Option<VerifierPolicyId>,
) -> Result<MachinePolicyCandidateV1, ZeroValueError> {
    Ok(MachinePolicyCandidateV1 {
        schema_version: 1,
        policy_id: nonzero(1)?,
        machine_id: nonzero(2)?,
        domain_id: nonzero(3)?,
        crypto_suite_id: CryptoSuiteId::try_from(SHA256_REFERENCE_V1_ID_BYTES)?,
        accumulator_profile_id: nonzero(4)?,
        verifier_cost_model_id: nonzero(5)?,
        supported_resource_schema_root: nonzero(6)?,
        supported_transition_schema_root: nonzero(7)?,
        resource_kind_policy_set_root: nonzero(8)?,
        creation_resource_kind_policy_map_root: nonzero(9)?,
        accepted_predecessor_resource_policy_set_root: nonzero(10)?,
        logic_verifier_policy_root: nonzero(11)?,
        transformation_verifier_policy_root: nonzero(12)?,
        authority_verifier_policy_root: nonzero(13)?,
        data_availability_policy_root: nonzero(14)?,
        admission_mode,
        admission_verifier_policy_id,
        governance_authority_root: nonzero(15)?,
        feature_suite_root: nonzero(16)?,
        limits: strict_limits(),
        validity_start_epoch: 10,
        validity_end_epoch: 20,
    })
}

fn resource_kind_candidate() -> Result<ResourceKindPolicyCandidateV1, ZeroValueError> {
    Ok(ResourceKindPolicyCandidateV1 {
        schema_version: 1,
        policy_id: nonzero(21)?,
        machine_id: nonzero(2)?,
        domain_id: nonzero(3)?,
        application_id: nonzero(22)?,
        resource_kind_id: nonzero(23)?,
        unit_id: nonzero(24)?,
        accounting_mode: AccountingModeV1::ConservedFungible,
        quantity_max: QuantityAtoms::new(1_000),
        allowed_logic_set_root: nonzero(25)?,
        allowed_logic_profile_set_root: nonzero(26)?,
        allowed_transformation_set_root: nonzero(27)?,
        controller_policy_root: nonzero(28)?,
        mint_authority_root: nonzero(29)?,
        burn_authority_root: nonzero(30)?,
        data_availability: DataAvailabilityRequirementV1::Optional,
        validity_start_epoch: 10,
        validity_end_epoch: 20,
    })
}

fn verifier_candidate() -> Result<VerifierPolicyCandidateV1, ZeroValueError> {
    Ok(VerifierPolicyCandidateV1 {
        schema_version: 1,
        verifier_policy_id: nonzero(31)?,
        machine_id: nonzero(2)?,
        domain_id: nonzero(3)?,
        backend_family_id: nonzero(32)?,
        verifier_id: nonzero(33)?,
        program_or_key_digest: nonzero(34)?,
        artifact_codec_id: nonzero(35)?,
        statement_schema_root: nonzero(36)?,
        journal_schema_root: nonzero(37)?,
        proof_parameter_root: nonzero(38)?,
        proof_mode: ProofModeV1::Production,
        coverage_claims_root: nonzero(39)?,
        non_claims_root: nonzero(40)?,
        trusted_computing_base_root: nonzero(41)?,
        verifier_cost_model_id: nonzero(5)?,
        max_verifier_cost_units: 10_000,
        max_artifact_bytes: 1_024,
        max_public_input_bytes: 2_048,
        max_public_output_bytes: 512,
        validity_start_epoch: 10,
        validity_end_epoch: 20,
    })
}

fn context_candidate() -> Result<ValidationContextCandidateV1, ZeroValueError> {
    Ok(ValidationContextCandidateV1 {
        schema_version: 1,
        machine_id: nonzero(2)?,
        domain_id: nonzero(3)?,
        current_epoch: u64::MAX,
        expected_machine_state_root: nonzero(51)?,
        expected_state_version: u64::MAX,
        expected_policy_root: nonzero(52)?,
        expected_crypto_suite_id: CryptoSuiteId::try_from(SHA256_REFERENCE_V1_ID_BYTES)?,
        expected_accumulator_profile_id: nonzero(4)?,
        ordering_context_root: nonzero(53)?,
    })
}

#[test]
fn machine_policy_accepts_local_and_required_admission_exactly() -> PolicyModelTestResult {
    let policy = MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;
    assert_eq!(policy.schema_version(), 1);
    assert_eq!(policy.admission_policy(), AdmissionPolicyV1::LocalKernel);
    assert!(policy.is_valid_at(10));
    assert!(policy.is_valid_at(20));
    assert!(!policy.is_valid_at(9));
    assert!(!policy.is_valid_at(21));

    let verifier_id = nonzero(42)?;
    let policy = MachinePolicyV1::try_from(machine_candidate(
        AdmissionModeV1::RequiredVerifier,
        Some(verifier_id),
    )?)?;
    assert_eq!(
        policy.admission_policy(),
        AdmissionPolicyV1::RequiredVerifier(verifier_id)
    );
    Ok(())
}

#[test]
fn machine_policy_rejects_both_invalid_admission_pairings() -> Result<(), ZeroValueError> {
    let verifier_id = nonzero(42)?;
    assert_eq!(
        MachinePolicyV1::try_from(machine_candidate(
            AdmissionModeV1::LocalKernel,
            Some(verifier_id)
        )?),
        Err(PolicyValidationErrorV1::UnexpectedAdmissionVerifierPolicy)
    );
    assert_eq!(
        MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::RequiredVerifier, None)?),
        Err(PolicyValidationErrorV1::MissingAdmissionVerifierPolicy)
    );
    Ok(())
}

#[test]
fn machine_policy_reject_precedence_is_schema_then_suite_then_limits() -> Result<(), ZeroValueError>
{
    let mut candidate = machine_candidate(AdmissionModeV1::RequiredVerifier, None)?;
    candidate.schema_version = 2;
    candidate.crypto_suite_id = nonzero(90)?;
    candidate.limits.max_envelope_bytes = PolicyLimitsV1::MAX_ENVELOPE_BYTES + 1;
    assert_eq!(
        MachinePolicyV1::try_from(candidate),
        Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
            object: PolicyObjectV1::MachinePolicy,
            actual: 2,
        })
    );

    candidate.schema_version = 1;
    assert_eq!(
        MachinePolicyV1::try_from(candidate),
        Err(PolicyValidationErrorV1::UnsupportedResourceCryptoSuite)
    );

    candidate.crypto_suite_id = CryptoSuiteId::try_from(SHA256_REFERENCE_V1_ID_BYTES)?;
    assert_eq!(
        MachinePolicyV1::try_from(candidate),
        Err(PolicyValidationErrorV1::LimitExceedsProtocolCeiling {
            field: LimitFieldV1::EnvelopeBytes,
            actual: u64::from(PolicyLimitsV1::MAX_ENVELOPE_BYTES) + 1,
            ceiling: u64::from(PolicyLimitsV1::MAX_ENVELOPE_BYTES),
        })
    );
    Ok(())
}

fn assert_protocol_ceiling_constants() {
    assert_eq!(PolicyLimitsV1::MAX_ENVELOPE_BYTES, 4_194_304);
    assert_eq!(PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES, 1_048_576);
    assert_eq!(PolicyLimitsV1::MAX_TOTAL_PROOF_BYTES, 3_145_728);
    assert_eq!(PolicyLimitsV1::MAX_STORAGE_WRITE_BYTES, 8_388_608);
}

fn assert_strict_default_limits() {
    let strict = PolicyLimitsV1::strict_default().as_candidate();
    assert_eq!(strict.max_envelope_bytes, 1_048_576);
    assert_eq!(strict.max_resource_bytes, 4_096);
    assert_eq!(strict.max_proof_artifact_bytes, 262_144);
    assert_eq!(strict.max_total_proof_bytes, 786_432);
    assert_eq!(strict.max_storage_write_bytes, 2_097_152);
}

fn assert_storage_write_limit_rejects(ceiling: PolicyLimitsCandidateV1) {
    let mut over = ceiling;
    over.max_storage_write_bytes = PolicyLimitsV1::MAX_STORAGE_WRITE_BYTES + 1;
    assert_eq!(
        PolicyLimitsV1::try_from(over),
        Err(PolicyValidationErrorV1::LimitExceedsProtocolCeiling {
            field: LimitFieldV1::StorageWriteBytes,
            actual: u64::from(over.max_storage_write_bytes),
            ceiling: u64::from(PolicyLimitsV1::MAX_STORAGE_WRITE_BYTES),
        })
    );
}

#[test]
fn every_machine_limit_accepts_its_ceiling_and_rejects_ceiling_plus_one() -> PolicyModelTestResult {
    let ceiling = PolicyLimitsV1::protocol_ceiling().as_candidate();
    let _validated_ceiling = PolicyLimitsV1::try_from(ceiling)?;
    assert_protocol_ceiling_constants();
    assert_strict_default_limits();
    assert_storage_write_limit_rejects(ceiling);
    Ok(())
}

fn assert_limit_failure(
    candidate: PolicyLimitsCandidateV1,
    field: LimitFieldV1,
    actual: u64,
    ceiling: u64,
) {
    assert_eq!(
        PolicyLimitsV1::try_from(candidate),
        Err(PolicyValidationErrorV1::LimitExceedsProtocolCeiling {
            field,
            actual,
            ceiling,
        })
    );
}

#[test]
#[expect(
    clippy::too_many_lines,
    reason = "the explicit atlas keeps every governed field and expected reject reviewable"
)]
fn limit_boundary_atlas_flips_every_governed_ceiling() {
    let ceiling = PolicyLimitsV1::protocol_ceiling().as_candidate();

    let mut candidate = ceiling;
    candidate.max_envelope_bytes = PolicyLimitsV1::MAX_ENVELOPE_BYTES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::EnvelopeBytes,
        u64::from(candidate.max_envelope_bytes),
        u64::from(PolicyLimitsV1::MAX_ENVELOPE_BYTES),
    );

    let mut candidate = ceiling;
    candidate.max_resource_bytes = PolicyLimitsV1::MAX_RESOURCE_BYTES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::ResourceBytes,
        u64::from(candidate.max_resource_bytes),
        u64::from(PolicyLimitsV1::MAX_RESOURCE_BYTES),
    );

    let mut candidate = ceiling;
    candidate.max_consumed_resources = PolicyLimitsV1::MAX_CONSUMED_RESOURCES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::ConsumedResources,
        u64::from(candidate.max_consumed_resources),
        u64::from(PolicyLimitsV1::MAX_CONSUMED_RESOURCES),
    );

    let mut candidate = ceiling;
    candidate.max_referenced_resources = PolicyLimitsV1::MAX_REFERENCED_RESOURCES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::ReferencedResources,
        u64::from(candidate.max_referenced_resources),
        u64::from(PolicyLimitsV1::MAX_REFERENCED_RESOURCES),
    );

    let mut candidate = ceiling;
    candidate.max_created_resources = PolicyLimitsV1::MAX_CREATED_RESOURCES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::CreatedResources,
        u64::from(candidate.max_created_resources),
        u64::from(PolicyLimitsV1::MAX_CREATED_RESOURCES),
    );

    let mut candidate = ceiling;
    candidate.max_logic_claims = PolicyLimitsV1::MAX_LOGIC_CLAIMS + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::LogicClaims,
        u64::from(candidate.max_logic_claims),
        u64::from(PolicyLimitsV1::MAX_LOGIC_CLAIMS),
    );

    let mut candidate = ceiling;
    candidate.max_transformation_claims = PolicyLimitsV1::MAX_TRANSFORMATION_CLAIMS + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::TransformationClaims,
        u64::from(candidate.max_transformation_claims),
        u64::from(PolicyLimitsV1::MAX_TRANSFORMATION_CLAIMS),
    );

    let mut candidate = ceiling;
    candidate.max_authority_claims = PolicyLimitsV1::MAX_AUTHORITY_CLAIMS + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::AuthorityClaims,
        u64::from(candidate.max_authority_claims),
        u64::from(PolicyLimitsV1::MAX_AUTHORITY_CLAIMS),
    );

    let mut candidate = ceiling;
    candidate.max_data_availability_claims = PolicyLimitsV1::MAX_DATA_AVAILABILITY_CLAIMS + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::DataAvailabilityClaims,
        u64::from(candidate.max_data_availability_claims),
        u64::from(PolicyLimitsV1::MAX_DATA_AVAILABILITY_CLAIMS),
    );

    let mut candidate = ceiling;
    candidate.max_accounting_rows = PolicyLimitsV1::MAX_ACCOUNTING_ROWS + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::AccountingRows,
        u64::from(candidate.max_accounting_rows),
        u64::from(PolicyLimitsV1::MAX_ACCOUNTING_ROWS),
    );

    let mut candidate = ceiling;
    candidate.max_evidence_references = PolicyLimitsV1::MAX_EVIDENCE_REFERENCES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::EvidenceReferences,
        u64::from(candidate.max_evidence_references),
        u64::from(PolicyLimitsV1::MAX_EVIDENCE_REFERENCES),
    );

    let mut candidate = ceiling;
    candidate.max_proof_artifact_bytes = PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::ProofArtifactBytes,
        u64::from(candidate.max_proof_artifact_bytes),
        u64::from(PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES),
    );

    let mut candidate = ceiling;
    candidate.max_total_proof_bytes = PolicyLimitsV1::MAX_TOTAL_PROOF_BYTES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::TotalProofBytes,
        u64::from(candidate.max_total_proof_bytes),
        u64::from(PolicyLimitsV1::MAX_TOTAL_PROOF_BYTES),
    );

    let mut candidate = ceiling;
    candidate.max_total_verifier_cost_units = PolicyLimitsV1::MAX_TOTAL_VERIFIER_COST_UNITS + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::TotalVerifierCostUnits,
        candidate.max_total_verifier_cost_units,
        PolicyLimitsV1::MAX_TOTAL_VERIFIER_COST_UNITS,
    );

    let mut candidate = ceiling;
    candidate.max_nesting_depth = PolicyLimitsV1::MAX_NESTING_DEPTH + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::NestingDepth,
        u64::from(candidate.max_nesting_depth),
        u64::from(PolicyLimitsV1::MAX_NESTING_DEPTH),
    );

    let mut candidate = ceiling;
    candidate.max_storage_write_bytes = PolicyLimitsV1::MAX_STORAGE_WRITE_BYTES + 1;
    assert_limit_failure(
        candidate,
        LimitFieldV1::StorageWriteBytes,
        u64::from(candidate.max_storage_write_bytes),
        u64::from(PolicyLimitsV1::MAX_STORAGE_WRITE_BYTES),
    );
}

#[test]
fn limit_reject_precedence_crosses_invariant_families() {
    let strict = strict_limits();
    let mut candidate = strict;
    candidate.max_envelope_bytes = PolicyLimitsV1::MAX_ENVELOPE_BYTES + 1;
    candidate.max_logic_claims = PolicyLimitsV1::MAX_LOGIC_CLAIMS + 1;
    candidate.max_proof_artifact_bytes = PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES + 1;
    candidate.max_resource_bytes = PolicyLimitsV1::MIN_RESOURCE_WIRE_V1_BYTES - 1;

    assert_limit_failure(
        candidate,
        LimitFieldV1::EnvelopeBytes,
        u64::from(candidate.max_envelope_bytes),
        u64::from(PolicyLimitsV1::MAX_ENVELOPE_BYTES),
    );

    candidate.max_envelope_bytes = strict.max_envelope_bytes;
    assert_limit_failure(
        candidate,
        LimitFieldV1::LogicClaims,
        u64::from(candidate.max_logic_claims),
        u64::from(PolicyLimitsV1::MAX_LOGIC_CLAIMS),
    );

    candidate.max_logic_claims = strict.max_logic_claims;
    assert_limit_failure(
        candidate,
        LimitFieldV1::ProofArtifactBytes,
        u64::from(candidate.max_proof_artifact_bytes),
        u64::from(PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES),
    );

    candidate.max_proof_artifact_bytes = strict.max_proof_artifact_bytes;
    assert_eq!(
        PolicyLimitsV1::try_from(candidate),
        Err(PolicyValidationErrorV1::ResourceWireLimitTooSmall {
            actual: PolicyLimitsV1::MIN_RESOURCE_WIRE_V1_BYTES - 1,
            minimum: PolicyLimitsV1::MIN_RESOURCE_WIRE_V1_BYTES,
        })
    );
}

#[test]
fn resource_wire_complete_form_must_fit_policy_limit() {
    let mut exact = strict_limits();
    exact.max_resource_bytes = PolicyLimitsV1::MIN_RESOURCE_WIRE_V1_BYTES;
    assert!(PolicyLimitsV1::try_from(exact).is_ok());

    let mut candidate = strict_limits();
    candidate.max_resource_bytes = 602;
    assert_eq!(
        PolicyLimitsV1::try_from(candidate),
        Err(PolicyValidationErrorV1::ResourceWireLimitTooSmall {
            actual: 602,
            minimum: 603,
        })
    );
}

fn assert_conserved_fungible_dimensions(
    candidate: &ResourceKindPolicyCandidateV1,
) -> PolicyModelTestResult {
    let expected_unit = candidate.unit_id;
    let policy = ResourceKindPolicyV1::try_from(*candidate)?;
    assert!(policy.is_valid_at(10));
    assert!(policy.is_valid_at(20));
    assert!(!policy.is_valid_at(9));
    assert!(!policy.is_valid_at(21));
    assert_eq!(
        policy.validate_dimensions(expected_unit, QuantityAtoms::new(1_000)),
        Ok(())
    );
    assert_eq!(
        policy.validate_dimensions(nonzero(91)?, QuantityAtoms::new(1_000)),
        Err(ResourceDimensionErrorV1::UnitMismatch)
    );
    assert_eq!(
        policy.validate_dimensions(expected_unit, QuantityAtoms::new(1_001)),
        Err(ResourceDimensionErrorV1::QuantityExceedsMaximum {
            actual: 1_001,
            maximum: 1_000,
        })
    );
    Ok(())
}

fn assert_lifecycle_non_fungible_dimensions(
    candidate: &ResourceKindPolicyCandidateV1,
) -> PolicyModelTestResult {
    let mut lifecycle = *candidate;
    lifecycle.accounting_mode = AccountingModeV1::LifecycleNonFungible;
    lifecycle.quantity_max = QuantityAtoms::new(1);
    let lifecycle_policy = ResourceKindPolicyV1::try_from(lifecycle)?;
    assert_eq!(
        lifecycle_policy.validate_dimensions(lifecycle.unit_id, QuantityAtoms::new(0)),
        Err(ResourceDimensionErrorV1::LifecycleQuantityMustBeOne { actual: 0 })
    );
    assert_eq!(
        lifecycle_policy.validate_dimensions(lifecycle.unit_id, QuantityAtoms::new(1)),
        Ok(())
    );
    assert_eq!(
        lifecycle_policy.validate_dimensions(lifecycle.unit_id, QuantityAtoms::new(2)),
        Err(ResourceDimensionErrorV1::LifecycleQuantityMustBeOne { actual: 2 })
    );
    Ok(())
}

#[test]
fn resource_kind_policy_enforces_unit_quantity_and_lifecycle_bounds() -> PolicyModelTestResult {
    let candidate = resource_kind_candidate()?;
    assert_conserved_fungible_dimensions(&candidate)?;
    assert_lifecycle_non_fungible_dimensions(&candidate)
}

#[test]
fn lifecycle_policy_requires_quantity_maximum_exactly_one() -> Result<(), ZeroValueError> {
    for invalid_maximum in [0, 2, u128::MAX] {
        let mut candidate = resource_kind_candidate()?;
        candidate.accounting_mode = AccountingModeV1::LifecycleNonFungible;
        candidate.quantity_max = QuantityAtoms::new(invalid_maximum);
        assert_eq!(
            ResourceKindPolicyV1::try_from(candidate),
            Err(PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne {
                actual: invalid_maximum,
            })
        );
    }

    let mut candidate = resource_kind_candidate()?;
    candidate.accounting_mode = AccountingModeV1::LifecycleNonFungible;
    candidate.quantity_max = QuantityAtoms::new(1);
    assert!(ResourceKindPolicyV1::try_from(candidate).is_ok());
    Ok(())
}

#[test]
fn resource_kind_policy_reject_precedence_is_schema_then_window_then_lifecycle_maximum()
-> Result<(), ZeroValueError> {
    let mut candidate = resource_kind_candidate()?;
    candidate.accounting_mode = AccountingModeV1::LifecycleNonFungible;
    candidate.quantity_max = QuantityAtoms::new(0);
    candidate.schema_version = 2;
    candidate.validity_start_epoch = 21;
    assert_eq!(
        ResourceKindPolicyV1::try_from(candidate),
        Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
            object: PolicyObjectV1::ResourceKindPolicy,
            actual: 2,
        })
    );

    candidate.schema_version = 1;
    assert_eq!(
        ResourceKindPolicyV1::try_from(candidate),
        Err(PolicyValidationErrorV1::InvalidValidityWindow {
            object: PolicyObjectV1::ResourceKindPolicy,
            start: 21,
            end: 20,
        })
    );

    candidate.validity_start_epoch = 20;
    assert_eq!(
        ResourceKindPolicyV1::try_from(candidate),
        Err(PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne { actual: 0 })
    );
    Ok(())
}

#[test]
fn every_policy_object_rejects_wrong_schema_and_inverted_validity() -> Result<(), ZeroValueError> {
    let mut machine = machine_candidate(AdmissionModeV1::LocalKernel, None)?;
    machine.validity_start_epoch = 21;
    assert_eq!(
        MachinePolicyV1::try_from(machine),
        Err(PolicyValidationErrorV1::InvalidValidityWindow {
            object: PolicyObjectV1::MachinePolicy,
            start: 21,
            end: 20,
        })
    );

    let mut resource = resource_kind_candidate()?;
    resource.schema_version = 2;
    assert_eq!(
        ResourceKindPolicyV1::try_from(resource),
        Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
            object: PolicyObjectV1::ResourceKindPolicy,
            actual: 2,
        })
    );
    resource.schema_version = 1;
    resource.validity_start_epoch = 21;
    assert_eq!(
        ResourceKindPolicyV1::try_from(resource),
        Err(PolicyValidationErrorV1::InvalidValidityWindow {
            object: PolicyObjectV1::ResourceKindPolicy,
            start: 21,
            end: 20,
        })
    );

    let mut verifier = verifier_candidate()?;
    verifier.schema_version = 2;
    assert_eq!(
        VerifierPolicyV1::try_from(verifier),
        Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
            object: PolicyObjectV1::VerifierPolicy,
            actual: 2,
        })
    );
    verifier.schema_version = 1;
    verifier.validity_start_epoch = 21;
    assert_eq!(
        VerifierPolicyV1::try_from(verifier),
        Err(PolicyValidationErrorV1::InvalidValidityWindow {
            object: PolicyObjectV1::VerifierPolicy,
            start: 21,
            end: 20,
        })
    );

    let mut context = context_candidate()?;
    context.schema_version = 2;
    assert_eq!(
        ValidationContextV1::try_from(context),
        Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
            object: PolicyObjectV1::ValidationContext,
            actual: 2,
        })
    );
    Ok(())
}

#[test]
fn validation_context_is_validated_data_without_a_trusted_constructor() -> Result<(), ZeroValueError>
{
    let context = ValidationContextV1::try_from(context_candidate()?);
    assert!(context.is_ok());
    if let Ok(context) = context {
        assert_eq!(context.current_epoch(), u64::MAX);
        assert_eq!(context.expected_state_version(), u64::MAX);
    }
    Ok(())
}

#[test]
fn verifier_policy_preserves_each_closed_proof_mode() -> Result<(), ZeroValueError> {
    for mode in [
        ProofModeV1::Production,
        ProofModeV1::Development,
        ProofModeV1::Test,
    ] {
        let mut candidate = verifier_candidate()?;
        candidate.proof_mode = mode;
        let policy = VerifierPolicyV1::try_from(candidate);
        assert!(policy.is_ok());
        if let Ok(policy) = policy {
            assert_eq!(policy.proof_mode(), mode);
        }
    }
    Ok(())
}

const MAX_LOCAL_DIAGNOSTIC_BYTES: usize = 128;

fn assert_stable_bounded_diagnostic(error: impl core::fmt::Display, expected: &str) {
    let diagnostic = format!("{error}");
    assert_eq!(diagnostic, expected);
    assert!(diagnostic.len() <= MAX_LOCAL_DIAGNOSTIC_BYTES);
}

fn assert_policy_validation_diagnostics() {
    let policy_errors = [
        (
            PolicyValidationErrorV1::UnsupportedSchemaVersion {
                object: PolicyObjectV1::MachinePolicy,
                actual: 2,
            },
            "unsupported MachinePolicy schema version: 2",
        ),
        (
            PolicyValidationErrorV1::InvalidValidityWindow {
                object: PolicyObjectV1::VerifierPolicy,
                start: 2,
                end: 1,
            },
            "invalid VerifierPolicy validity window: 2..=1",
        ),
        (
            PolicyValidationErrorV1::UnsupportedResourceCryptoSuite,
            "unsupported ResourceWireV1 cryptographic suite",
        ),
        (
            PolicyValidationErrorV1::LimitExceedsProtocolCeiling {
                field: LimitFieldV1::EnvelopeBytes,
                actual: 2,
                ceiling: 1,
            },
            "EnvelopeBytes limit 2 exceeds protocol ceiling 1",
        ),
        (
            PolicyValidationErrorV1::ResourceWireLimitTooSmall {
                actual: 602,
                minimum: 603,
            },
            "resource byte limit 602 is smaller than required minimum 603",
        ),
        (
            PolicyValidationErrorV1::UnexpectedAdmissionVerifierPolicy,
            "LocalKernel forbids an admission verifier policy",
        ),
        (
            PolicyValidationErrorV1::MissingAdmissionVerifierPolicy,
            "RequiredVerifier requires an admission verifier policy",
        ),
        (
            PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne { actual: 2 },
            "lifecycle quantity maximum must be one, got 2",
        ),
    ];
    for (error, expected) in policy_errors {
        assert_stable_bounded_diagnostic(error, expected);
    }
}

fn assert_resource_dimension_diagnostics() {
    let dimension_errors = [
        (
            ResourceDimensionErrorV1::UnitMismatch,
            "resource unit does not match policy unit",
        ),
        (
            ResourceDimensionErrorV1::LifecycleQuantityMustBeOne { actual: 0 },
            "lifecycle non-fungible resource quantity must be one, got 0",
        ),
        (
            ResourceDimensionErrorV1::ZeroQuantityForbidden,
            "zero resource quantity is forbidden by policy",
        ),
        (
            ResourceDimensionErrorV1::QuantityExceedsMaximum {
                actual: 2,
                maximum: 1,
            },
            "resource quantity 2 exceeds maximum 1",
        ),
    ];
    for (error, expected) in dimension_errors {
        assert_stable_bounded_diagnostic(error, expected);
    }
}

#[test]
fn policy_error_diagnostics_are_stable_and_bounded() {
    assert_policy_validation_diagnostics();
    assert_resource_dimension_diagnostics();
}

#[test]
fn policy_error_diagnostic_bound_covers_every_numeric_width_maximum() {
    let policy_objects = [
        PolicyObjectV1::MachinePolicy,
        PolicyObjectV1::ResourceKindPolicy,
        PolicyObjectV1::ValidationContext,
        PolicyObjectV1::VerifierPolicy,
    ];
    for object in policy_objects {
        assert_diagnostic_is_bounded(PolicyValidationErrorV1::UnsupportedSchemaVersion {
            object,
            actual: u16::MAX,
        });
        assert_diagnostic_is_bounded(PolicyValidationErrorV1::InvalidValidityWindow {
            object,
            start: u64::MAX,
            end: u64::MAX,
        });
    }

    let limit_fields = [
        LimitFieldV1::EnvelopeBytes,
        LimitFieldV1::ResourceBytes,
        LimitFieldV1::ConsumedResources,
        LimitFieldV1::ReferencedResources,
        LimitFieldV1::CreatedResources,
        LimitFieldV1::LogicClaims,
        LimitFieldV1::TransformationClaims,
        LimitFieldV1::AuthorityClaims,
        LimitFieldV1::DataAvailabilityClaims,
        LimitFieldV1::AccountingRows,
        LimitFieldV1::EvidenceReferences,
        LimitFieldV1::ProofArtifactBytes,
        LimitFieldV1::TotalProofBytes,
        LimitFieldV1::TotalVerifierCostUnits,
        LimitFieldV1::NestingDepth,
        LimitFieldV1::StorageWriteBytes,
    ];
    for field in limit_fields {
        assert_diagnostic_is_bounded(PolicyValidationErrorV1::LimitExceedsProtocolCeiling {
            field,
            actual: u64::MAX,
            ceiling: u64::MAX,
        });
    }

    assert_diagnostic_is_bounded(PolicyValidationErrorV1::LifecycleQuantityMaximumMustBeOne {
        actual: u128::MAX,
    });
    assert_diagnostic_is_bounded(PolicyValidationErrorV1::ResourceWireLimitTooSmall {
        actual: u32::MAX,
        minimum: u32::MAX,
    });
    assert_diagnostic_is_bounded(ResourceDimensionErrorV1::LifecycleQuantityMustBeOne {
        actual: u128::MAX,
    });
    assert_diagnostic_is_bounded(ResourceDimensionErrorV1::QuantityExceedsMaximum {
        actual: u128::MAX,
        maximum: u128::MAX,
    });
}

fn assert_diagnostic_is_bounded(error: impl core::fmt::Display) {
    let diagnostic = format!("{error}");
    assert!(
        diagnostic.len() <= MAX_LOCAL_DIAGNOSTIC_BYTES,
        "diagnostic has {} bytes: {diagnostic}",
        diagnostic.len()
    );
}

fn assert_machine_policy_getters() -> PolicyModelTestResult {
    let machine_candidate = machine_candidate(AdmissionModeV1::LocalKernel, None)?;
    let machine = MachinePolicyV1::try_from(machine_candidate)?;
    assert_eq!(machine.policy_id(), machine_candidate.policy_id);
    assert_eq!(machine.machine_id(), machine_candidate.machine_id);
    assert_eq!(machine.domain_id(), machine_candidate.domain_id);
    assert_eq!(machine.crypto_suite_id(), machine_candidate.crypto_suite_id);
    assert_eq!(
        machine.verifier_cost_model_id(),
        machine_candidate.verifier_cost_model_id
    );
    assert_eq!(machine.as_candidate(), machine_candidate);
    Ok(())
}

fn assert_resource_kind_policy_getters() -> PolicyModelTestResult {
    let resource_candidate = resource_kind_candidate()?;
    let resource = ResourceKindPolicyV1::try_from(resource_candidate)?;
    assert_eq!(resource.unit_id(), resource_candidate.unit_id);
    assert_eq!(resource.quantity_max(), resource_candidate.quantity_max);
    assert_eq!(
        resource.accounting_mode(),
        resource_candidate.accounting_mode
    );
    assert_eq!(resource.as_candidate(), resource_candidate);
    Ok(())
}

fn assert_policy_limit_count_getters() -> PolicyModelTestResult {
    let mut candidate = strict_limits();
    candidate.max_consumed_resources = 17;
    candidate.max_referenced_resources = 19;
    candidate.max_created_resources = 23;
    let limits = PolicyLimitsV1::try_from(candidate)?;
    assert_eq!(limits.max_consumed_resources(), 17);
    assert_eq!(limits.max_referenced_resources(), 19);
    assert_eq!(limits.max_created_resources(), 23);
    Ok(())
}

#[test]
fn validated_policy_getters_preserve_typed_candidates() -> PolicyModelTestResult {
    assert_machine_policy_getters()?;
    assert_resource_kind_policy_getters()?;
    assert_policy_limit_count_getters()
}

fn assert_verifier_policy_getters() -> PolicyModelTestResult {
    let verifier_candidate = verifier_candidate()?;
    let verifier = VerifierPolicyV1::try_from(verifier_candidate)?;
    assert_eq!(
        verifier.verifier_policy_id(),
        verifier_candidate.verifier_policy_id
    );
    assert_eq!(
        verifier.backend_family_id(),
        verifier_candidate.backend_family_id
    );
    assert_eq!(
        verifier.max_public_input_bytes(),
        verifier_candidate.max_public_input_bytes
    );
    assert_eq!(
        verifier.max_public_output_bytes(),
        verifier_candidate.max_public_output_bytes
    );
    assert_eq!(verifier.as_candidate(), verifier_candidate);
    Ok(())
}

fn assert_validation_context_getters() -> PolicyModelTestResult {
    let context_candidate = context_candidate()?;
    let context = ValidationContextV1::try_from(context_candidate)?;
    assert_eq!(context.machine_id(), context_candidate.machine_id);
    assert_eq!(context.domain_id(), context_candidate.domain_id);
    assert_eq!(
        context.expected_policy_root(),
        context_candidate.expected_policy_root
    );
    assert_eq!(context.as_candidate(), context_candidate);
    Ok(())
}

#[test]
fn verifier_and_context_getters_preserve_typed_candidates() -> PolicyModelTestResult {
    assert_verifier_policy_getters()?;
    assert_validation_context_getters()
}
