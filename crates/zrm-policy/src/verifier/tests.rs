use super::{ProofModeV1, VerifierPolicyCandidateV1, VerifierPolicyV1};
use crate::{
    AdmissionModeV1, MachinePolicyCandidateV1, MachinePolicyV1, PolicyLimitsCandidateV1,
    PolicyLimitsV1, PolicyValidationErrorV1, VerifierCompatibilityErrorV1,
};
use zrm_crypto::SHA256_REFERENCE_V1_ID_BYTES;
use zrm_types::{CryptoSuiteId, VerifierPolicyId, ZeroValueError};

#[derive(Debug)]
enum TestError {
    ZeroValue,
    PolicyValidation,
}

impl From<ZeroValueError> for TestError {
    fn from(_: ZeroValueError) -> Self {
        Self::ZeroValue
    }
}

impl From<PolicyValidationErrorV1> for TestError {
    fn from(_: PolicyValidationErrorV1) -> Self {
        Self::PolicyValidation
    }
}

type TestResult = Result<(), TestError>;

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

fn assert_identity_and_window_shape_rejects(machine: &MachinePolicyV1) -> TestResult {
    let verifier = VerifierPolicyV1::try_from(verifier_candidate()?)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Ok(())
    );
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 9),
        Err(VerifierCompatibilityErrorV1::MachinePolicyInactive)
    );

    let mut candidate = verifier_candidate()?;
    candidate.machine_id = nonzero(90)?;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::MachineMismatch)
    );

    let mut candidate = verifier_candidate()?;
    candidate.domain_id = nonzero(91)?;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::DomainMismatch)
    );

    let mut candidate = verifier_candidate()?;
    candidate.verifier_cost_model_id = nonzero(92)?;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::CostModelMismatch)
    );

    let mut candidate = verifier_candidate()?;
    candidate.validity_start_epoch = 16;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::VerifierPolicyInactive)
    );
    Ok(())
}

fn assert_limit_shape_rejects(machine: &MachinePolicyV1) -> TestResult {
    let mut candidate = verifier_candidate()?;
    candidate.max_artifact_bytes =
        u64::from(PolicyLimitsV1::strict_default().max_proof_artifact_bytes()).saturating_add(1);
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::ArtifactLimitExceedsMachine)
    );

    let mut candidate = verifier_candidate()?;
    candidate.max_verifier_cost_units = PolicyLimitsV1::strict_default()
        .max_total_verifier_cost_units()
        .saturating_add(1);
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::VerifierCostLimitExceedsMachine)
    );
    Ok(())
}

#[test]
fn untrusted_shape_helper_retains_structural_rejects() -> TestResult {
    let machine =
        MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;
    assert_identity_and_window_shape_rejects(&machine)?;
    assert_limit_shape_rejects(&machine)
}

#[test]
fn untrusted_shape_helper_enforces_total_proof_bound_independently() -> TestResult {
    let mut machine = machine_candidate(AdmissionModeV1::LocalKernel, None)?;
    machine.limits.max_proof_artifact_bytes = 700_000;
    machine.limits.max_total_proof_bytes = 600_000;
    let machine = MachinePolicyV1::try_from(machine)?;

    let mut verifier_candidate = verifier_candidate()?;
    verifier_candidate.max_artifact_bytes = 600_000;
    let verifier = VerifierPolicyV1::try_from(verifier_candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Ok(())
    );

    verifier_candidate.max_artifact_bytes = 600_001;
    let verifier = VerifierPolicyV1::try_from(verifier_candidate)?;
    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::ArtifactLimitExceedsMachine)
    );
    Ok(())
}

#[test]
fn untrusted_shape_helper_accepts_exact_machine_artifact_and_cost_caps() -> TestResult {
    let machine =
        MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;
    let limits = machine.limits();
    let mut verifier_candidate = verifier_candidate()?;
    verifier_candidate.max_artifact_bytes = u64::from(limits.max_proof_artifact_bytes());
    verifier_candidate.max_verifier_cost_units = limits.max_total_verifier_cost_units();
    let verifier = VerifierPolicyV1::try_from(verifier_candidate)?;

    assert_eq!(
        machine.check_untrusted_verifier_candidate_shape(&verifier, 15),
        Ok(())
    );
    Ok(())
}

#[test]
fn untrusted_admission_shape_retains_mode_and_identifier_rejects() -> TestResult {
    let verifier = VerifierPolicyV1::try_from(verifier_candidate()?)?;
    let local = MachinePolicyV1::try_from(machine_candidate(AdmissionModeV1::LocalKernel, None)?)?;
    assert_eq!(
        local.check_untrusted_admission_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::AdmissionVerifierForbidden)
    );

    let wrong_id = MachinePolicyV1::try_from(machine_candidate(
        AdmissionModeV1::RequiredVerifier,
        Some(nonzero(99)?),
    )?)?;
    assert_eq!(
        wrong_id.check_untrusted_admission_candidate_shape(&verifier, 15),
        Err(VerifierCompatibilityErrorV1::AdmissionVerifierPolicyMismatch)
    );

    let exact = MachinePolicyV1::try_from(machine_candidate(
        AdmissionModeV1::RequiredVerifier,
        Some(verifier.verifier_policy_id()),
    )?)?;
    assert_eq!(
        exact.check_untrusted_admission_candidate_shape(&verifier, 15),
        Ok(())
    );
    Ok(())
}

#[test]
fn internal_candidate_requests_preserve_exact_lengths_and_maxima() -> TestResult {
    let candidate = verifier_candidate()?;
    let verifier = VerifierPolicyV1::try_from(candidate)?;
    let request = verifier.candidate_cost_quote_request(7, 9);
    assert_eq!(request.artifact_len(), 7);
    assert_eq!(request.canonical_statement_len(), 9);

    let reservation = verifier.candidate_admission_reservation_request();
    assert_eq!(reservation.artifact_len(), candidate.max_artifact_bytes);
    assert_eq!(
        reservation.canonical_statement_len(),
        candidate.max_public_input_bytes
    );
    Ok(())
}

fn identity_substitutions(
    original: &VerifierPolicyCandidateV1,
) -> Result<[VerifierPolicyCandidateV1; 11], ZeroValueError> {
    let original = *original;
    let mut backend = original;
    backend.backend_family_id = nonzero(60)?;
    let mut verifier_id = original;
    verifier_id.verifier_id = nonzero(61)?;
    let mut program = original;
    program.program_or_key_digest = nonzero(62)?;
    let mut codec = original;
    codec.artifact_codec_id = nonzero(63)?;
    let mut statement_schema = original;
    statement_schema.statement_schema_root = nonzero(64)?;
    let mut journal_schema = original;
    journal_schema.journal_schema_root = nonzero(65)?;
    let mut parameters = original;
    parameters.proof_parameter_root = nonzero(66)?;
    let mut proof_mode = original;
    proof_mode.proof_mode = ProofModeV1::Test;
    let mut coverage = original;
    coverage.coverage_claims_root = nonzero(67)?;
    let mut nonclaims = original;
    nonclaims.non_claims_root = nonzero(68)?;
    let mut tcb = original;
    tcb.trusted_computing_base_root = nonzero(69)?;
    Ok([
        backend,
        verifier_id,
        program,
        codec,
        statement_schema,
        journal_schema,
        parameters,
        proof_mode,
        coverage,
        nonclaims,
        tcb,
    ])
}

fn bound_substitutions(original: &VerifierPolicyCandidateV1) -> [VerifierPolicyCandidateV1; 5] {
    let original = *original;
    let mut public_input = original;
    public_input.max_public_input_bytes = original.max_public_input_bytes.saturating_add(1);
    let mut public_output = original;
    public_output.max_public_output_bytes = original.max_public_output_bytes.saturating_add(1);
    let mut artifact_bound = original;
    artifact_bound.max_artifact_bytes = 1;
    let mut cost_bound = original;
    cost_bound.max_verifier_cost_units = 1;
    let mut validity = original;
    validity.validity_start_epoch = 11;
    validity.validity_end_epoch = 19;
    [
        public_input,
        public_output,
        artifact_bound,
        cost_bound,
        validity,
    ]
}

#[test]
fn inert_helper_exposes_copied_policy_sensitive_field_counterexamples() -> TestResult {
    let original = verifier_candidate()?;
    let expected_policy_id = original.verifier_policy_id;
    let machine = MachinePolicyV1::try_from(machine_candidate(
        AdmissionModeV1::RequiredVerifier,
        Some(expected_policy_id),
    )?)?;

    let substituted = identity_substitutions(&original)?
        .into_iter()
        .chain(bound_substitutions(&original));
    for candidate in substituted {
        assert_eq!(candidate.verifier_policy_id, expected_policy_id);
        let verifier = VerifierPolicyV1::try_from(candidate)?;
        // This accepted result is retained only as a counterexample proving why
        // the shape helper cannot be part of the default public authority API.
        assert_eq!(
            machine.check_untrusted_admission_candidate_shape(&verifier, 15),
            Ok(())
        );
    }
    Ok(())
}

const ADMISSION_AND_IDENTITY_DIAGNOSTICS: [(VerifierCompatibilityErrorV1, &str); 5] = [
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
];
const WINDOW_AND_LIMIT_DIAGNOSTICS: [(VerifierCompatibilityErrorV1, &str); 4] = [
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

fn assert_bounded_diagnostics(cases: &[(VerifierCompatibilityErrorV1, &str)]) {
    for (error, expected) in cases {
        let diagnostic = std::format!("{error}");
        assert_eq!(diagnostic, *expected);
        assert!(diagnostic.len() <= 80);
    }
}

#[test]
fn internal_shape_diagnostics_remain_bounded() {
    assert_bounded_diagnostics(&ADMISSION_AND_IDENTITY_DIAGNOSTICS);
    assert_bounded_diagnostics(&WINDOW_AND_LIMIT_DIAGNOSTICS);
}
