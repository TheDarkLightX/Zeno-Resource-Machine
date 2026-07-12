//! Public policy-model invariant and cross-field regression tests.

use zrm_crypto::SHA256_REFERENCE_V1_ID_BYTES;
use zrm_policy::{
    AccountingModeV1, AdmissionModeV1, AdmissionPolicyV1, DataAvailabilityRequirementV1,
    LimitFieldV1, MachinePolicyCandidateV1, MachinePolicyV1, PolicyLimitsCandidateV1,
    PolicyLimitsV1, PolicyObjectV1, PolicyValidationErrorV1, ProofModeV1, ResourceDimensionErrorV1,
    ResourceKindPolicyCandidateV1, ResourceKindPolicyV1, ValidationContextCandidateV1,
    ValidationContextV1, VerifierCompatibilityErrorV1, VerifierCostErrorV1,
    VerifierCostModelCandidateV1, VerifierCostModelV1, VerifierCostRowCandidateV1,
    VerifierCostRowV1, VerifierPolicyCandidateV1, VerifierPolicyV1,
};
use zrm_types::{CryptoSuiteId, QuantityAtoms, VerifierPolicyId, ZeroValueError};

#[derive(Debug)]
enum PolicyModelTestError {
    ZeroValue(ZeroValueError),
    PolicyValidation(PolicyValidationErrorV1),
    VerifierCost(VerifierCostErrorV1),
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

impl From<VerifierCostErrorV1> for PolicyModelTestError {
    fn from(error: VerifierCostErrorV1) -> Self {
        Self::VerifierCost(error)
    }
}

impl core::fmt::Display for PolicyModelTestError {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::ZeroValue(error) => write!(formatter, "invalid nonzero fixture: {error}"),
            Self::PolicyValidation(error) => write!(formatter, "invalid policy fixture: {error}"),
            Self::VerifierCost(error) => write!(formatter, "unexpected quote failure: {error}"),
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
    lifecycle.quantity_max = QuantityAtoms::new(2);
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

const MAX_LOCAL_DIAGNOSTIC_BYTES: usize = 64;

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

fn assert_verifier_compatibility_diagnostics() {
    let compatibility_errors = [
        (
            VerifierCompatibilityErrorV1::AdmissionVerifierForbidden,
            "LocalKernel forbids an admission verifier candidate",
        ),
        (
            VerifierCompatibilityErrorV1::AdmissionVerifierPolicyMismatch,
            "admission verifier policy identifier mismatch",
        ),
        (
            VerifierCompatibilityErrorV1::MachineMismatch,
            "verifier policy machine mismatch",
        ),
        (
            VerifierCompatibilityErrorV1::DomainMismatch,
            "verifier policy domain mismatch",
        ),
        (
            VerifierCompatibilityErrorV1::CostModelMismatch,
            "verifier policy cost-model mismatch",
        ),
        (
            VerifierCompatibilityErrorV1::MachinePolicyInactive,
            "machine-policy validity window excludes epoch candidate",
        ),
        (
            VerifierCompatibilityErrorV1::VerifierPolicyInactive,
            "verifier-policy validity window excludes epoch candidate",
        ),
        (
            VerifierCompatibilityErrorV1::ArtifactLimitExceedsMachine,
            "verifier artifact bound exceeds machine policy",
        ),
        (
            VerifierCompatibilityErrorV1::VerifierCostLimitExceedsMachine,
            "verifier cost bound exceeds machine policy",
        ),
    ];
    for (error, expected) in compatibility_errors {
        assert_stable_bounded_diagnostic(error, expected);
    }
}

#[test]
fn policy_error_diagnostics_are_stable_and_bounded() {
    assert_policy_validation_diagnostics();
    assert_resource_dimension_diagnostics();
    assert_verifier_compatibility_diagnostics();
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
    assert_eq!(verifier.as_candidate(), verifier_candidate);
    let request = verifier.cost_quote_request(7, 9);
    assert_eq!(request.artifact_len(), 7);
    assert_eq!(request.canonical_statement_len(), 9);
    let reservation = verifier.admission_reservation_quote_request();
    assert_eq!(
        reservation.artifact_len(),
        verifier_candidate.max_artifact_bytes
    );
    assert_eq!(
        reservation.canonical_statement_len(),
        verifier_candidate.max_public_input_bytes
    );
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

#[test]
fn policy_derived_cost_quotes_preserve_formula_and_reservation() -> PolicyModelTestResult {
    let mut candidate = verifier_candidate()?;
    candidate.max_artifact_bytes = 10;
    candidate.max_public_input_bytes = 20;
    candidate.max_public_output_bytes = 30;
    candidate.max_verifier_cost_units = 1_000;
    let policy = VerifierPolicyV1::try_from(candidate)?;
    let model = VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
        schema_version: 1,
        rows_root: nonzero(61)?,
        max_charge_units: 10_000,
    })?;
    let row = VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
        backend_family_id: candidate.backend_family_id,
        base_units: 7,
        artifact_byte_units: 3,
        statement_byte_units: 5,
        reserved_output_byte_units: 11,
    });

    assert_eq!(
        model
            .compute_quote(&row, &policy.cost_quote_request(4, 6))?
            .units(),
        379
    );
    assert_eq!(
        model
            .compute_quote(&row, &policy.admission_reservation_quote_request())?
            .units(),
        467
    );
    Ok(())
}

#[test]
fn policy_derived_cost_quotes_preserve_every_hidden_bound() -> PolicyModelTestResult {
    let mut candidate = verifier_candidate()?;
    candidate.max_artifact_bytes = 10;
    candidate.max_public_input_bytes = 20;
    candidate.max_public_output_bytes = 30;
    candidate.max_verifier_cost_units = 1_000;
    let policy = VerifierPolicyV1::try_from(candidate)?;
    let model = VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
        schema_version: 1,
        rows_root: nonzero(61)?,
        max_charge_units: 10_000,
    })?;
    let row = VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
        backend_family_id: candidate.backend_family_id,
        base_units: 7,
        artifact_byte_units: 3,
        statement_byte_units: 5,
        reserved_output_byte_units: 11,
    });
    assert_eq!(
        model.compute_quote(&row, &policy.cost_quote_request(11, 6)),
        Err(VerifierCostErrorV1::ArtifactBytesExceeded)
    );
    assert_eq!(
        model.compute_quote(&row, &policy.cost_quote_request(4, 21)),
        Err(VerifierCostErrorV1::PublicInputBytesExceeded)
    );

    let wrong_backend_row = VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
        backend_family_id: nonzero(62)?,
        base_units: 7,
        artifact_byte_units: 3,
        statement_byte_units: 5,
        reserved_output_byte_units: 11,
    });
    assert_eq!(
        model.compute_quote(&wrong_backend_row, &policy.cost_quote_request(4, 6)),
        Err(VerifierCostErrorV1::BackendFamilyMismatch)
    );

    candidate.max_verifier_cost_units = 378;
    let capped_policy = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        model.compute_quote(&row, &capped_policy.cost_quote_request(4, 6)),
        Err(VerifierCostErrorV1::VerifierChargeLimitExceeded)
    );
    Ok(())
}

#[test]
fn verifier_compatibility_binds_machine_domain_cost_model_window_and_limits()
-> PolicyModelTestResult {
    let machine =
        MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;
    let verifier = VerifierPolicyV1::try_from(verifier_candidate()?)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Ok(())
    );
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 9),
        Err(VerifierCompatibilityErrorV1::MachinePolicyInactive)
    );

    let mut wrong_model = verifier_candidate()?;
    wrong_model.verifier_cost_model_id = nonzero(99)?;
    let verifier = VerifierPolicyV1::try_from(wrong_model)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::CostModelMismatch)
    );
    Ok(())
}

#[test]
fn admission_verifier_candidate_requires_mode_and_exact_policy_id() -> PolicyModelTestResult {
    let verifier = VerifierPolicyV1::try_from(verifier_candidate()?)?;

    let local = MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;
    assert_eq!(
        local.validate_admission_verifier_candidate(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::AdmissionVerifierForbidden)
    );

    let wrong_id = MachinePolicyV1::try_from(machine_candidate(
        AdmissionModeV1::RequiredVerifier,
        Some(nonzero(99)?),
    )?)?;
    assert_eq!(
        wrong_id.validate_admission_verifier_candidate(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::AdmissionVerifierPolicyMismatch)
    );

    let exact = MachinePolicyV1::try_from(machine_candidate(
        AdmissionModeV1::RequiredVerifier,
        Some(verifier.verifier_policy_id()),
    )?)?;
    assert_eq!(
        exact.validate_admission_verifier_candidate(&verifier, 15),
        Ok(())
    );
    Ok(())
}

#[test]
fn verifier_compatibility_rejects_every_mismatch_before_authority() -> PolicyModelTestResult {
    let machine =
        MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;

    let mut candidate = verifier_candidate()?;
    candidate.machine_id = nonzero(90)?;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::MachineMismatch)
    );

    let mut candidate = verifier_candidate()?;
    candidate.domain_id = nonzero(91)?;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::DomainMismatch)
    );

    let mut candidate = verifier_candidate()?;
    candidate.validity_start_epoch = 16;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::VerifierPolicyInactive)
    );

    let mut candidate = verifier_candidate()?;
    candidate.max_artifact_bytes =
        u64::from(PolicyLimitsV1::strict_default().max_proof_artifact_bytes()) + 1;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::ArtifactLimitExceedsMachine)
    );

    let mut candidate = verifier_candidate()?;
    candidate.max_verifier_cost_units =
        PolicyLimitsV1::strict_default().max_total_verifier_cost_units() + 1;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::VerifierCostLimitExceedsMachine)
    );
    Ok(())
}

#[test]
fn verifier_compatibility_accepts_exact_machine_caps_and_rejects_one_more() -> PolicyModelTestResult
{
    let machine =
        MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;
    let limits = machine.limits();

    let mut exact = verifier_candidate()?;
    exact.max_artifact_bytes = u64::from(limits.max_proof_artifact_bytes());
    exact.max_verifier_cost_units = limits.max_total_verifier_cost_units();
    let verifier = VerifierPolicyV1::try_from(exact)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Ok(())
    );

    let mut artifact_over = exact;
    artifact_over.max_artifact_bytes =
        u64::from(limits.max_proof_artifact_bytes()).saturating_add(1);
    let verifier = VerifierPolicyV1::try_from(artifact_over)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::ArtifactLimitExceedsMachine)
    );

    let mut cost_over = exact;
    cost_over.max_verifier_cost_units = limits.max_total_verifier_cost_units().saturating_add(1);
    let verifier = VerifierPolicyV1::try_from(cost_over)?;
    assert_eq!(
        machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::VerifierCostLimitExceedsMachine)
    );

    let mut total_bound_machine = machine_candidate(AdmissionModeV1::LocalKernel, None)?;
    total_bound_machine.limits.max_proof_artifact_bytes = 700_000;
    total_bound_machine.limits.max_total_proof_bytes = 600_000;
    let total_bound_machine = MachinePolicyV1::try_from(total_bound_machine)?;

    let mut total_exact = verifier_candidate()?;
    total_exact.max_artifact_bytes = 600_000;
    let verifier = VerifierPolicyV1::try_from(total_exact)?;
    assert_eq!(
        total_bound_machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Ok(())
    );
    total_exact.max_artifact_bytes = 600_001;
    let verifier = VerifierPolicyV1::try_from(total_exact)?;
    assert_eq!(
        total_bound_machine.validate_verifier_candidate_compatibility(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::ArtifactLimitExceedsMachine)
    );
    Ok(())
}
