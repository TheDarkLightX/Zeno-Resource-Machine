//! Logical verifier-policy validation without verifier authority.

use zrm_types::{
    ArtifactCodecId, BackendFamilyId, CoverageClaimsRoot, DomainId, JournalSchemaRoot, MachineId,
    NonClaimsRoot, ProgramOrKeyDigest, ProofParameterRoot, StatementSchemaRoot,
    TrustedComputingBaseRoot, VerifierCostModelId, VerifierId, VerifierPolicyId,
};

use crate::{
    AdmissionPolicyV1, MachinePolicyV1, POLICY_SCHEMA_VERSION_V1, PolicyObjectV1,
    PolicyValidationErrorV1, ValidityWindowV1, VerifierCompatibilityErrorV1,
    VerifierCostQuoteRequestV1,
};

/// Closed verifier proof-mode classification.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProofModeV1 {
    /// Production verifier profile.
    Production,
    /// Development-only verifier profile.
    Development,
    /// Test-only verifier profile.
    Test,
}

/// Public, non-authoritative logical verifier-policy candidate.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifierPolicyCandidateV1 {
    /// Candidate logical schema version.
    pub schema_version: u16,
    /// Externally governed verifier-policy identifier.
    pub verifier_policy_id: VerifierPolicyId,
    /// Machine identity.
    pub machine_id: MachineId,
    /// Replay and authority domain.
    pub domain_id: DomainId,
    /// Backend-family identity used to select one cost row.
    pub backend_family_id: BackendFamilyId,
    /// Concrete verifier identity.
    pub verifier_id: VerifierId,
    /// Digest of the required verifier program or key.
    pub program_or_key_digest: ProgramOrKeyDigest,
    /// Artifact-codec identity.
    pub artifact_codec_id: ArtifactCodecId,
    /// Root of accepted statement schemas.
    pub statement_schema_root: StatementSchemaRoot,
    /// Root of accepted journal schemas.
    pub journal_schema_root: JournalSchemaRoot,
    /// Root of proof-system parameters.
    pub proof_parameter_root: ProofParameterRoot,
    /// Production, development, or test classification.
    pub proof_mode: ProofModeV1,
    /// Root of scoped coverage claims.
    pub coverage_claims_root: CoverageClaimsRoot,
    /// Root of explicit non-claims.
    pub non_claims_root: NonClaimsRoot,
    /// Root of the declared trusted computing base.
    pub trusted_computing_base_root: TrustedComputingBaseRoot,
    /// Governed verifier-cost-model identity.
    pub verifier_cost_model_id: VerifierCostModelId,
    /// Maximum cost allowed for one dispatch under this verifier policy.
    pub max_verifier_cost_units: u64,
    /// Maximum artifact bytes accepted by the verifier wrapper.
    pub max_artifact_bytes: u64,
    /// Maximum canonical public-input bytes.
    pub max_public_input_bytes: u64,
    /// Maximum public-output bytes reserved before dispatch.
    pub max_public_output_bytes: u64,
    /// Inclusive first valid logical epoch.
    pub validity_start_epoch: u64,
    /// Inclusive final valid logical epoch.
    pub validity_end_epoch: u64,
}

/// Locally validated logical verifier policy.
///
/// This type validates schema and interval shape only. It does not establish
/// registry membership, release identity, revocation status, proof validity,
/// or any verified-fact capability.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifierPolicyV1 {
    candidate: VerifierPolicyCandidateV1,
    validity: ValidityWindowV1,
}

impl VerifierPolicyV1 {
    /// Returns the governed verifier-policy identifier candidate.
    #[must_use]
    pub const fn verifier_policy_id(&self) -> VerifierPolicyId {
        self.candidate.verifier_policy_id
    }

    /// Returns the machine identity.
    #[must_use]
    pub const fn machine_id(&self) -> MachineId {
        self.candidate.machine_id
    }

    /// Returns the replay and authority domain.
    #[must_use]
    pub const fn domain_id(&self) -> DomainId {
        self.candidate.domain_id
    }

    /// Returns the backend-family identity.
    #[must_use]
    pub const fn backend_family_id(&self) -> BackendFamilyId {
        self.candidate.backend_family_id
    }

    /// Returns the selected proof-mode classification.
    #[must_use]
    pub const fn proof_mode(&self) -> ProofModeV1 {
        self.candidate.proof_mode
    }

    /// Returns the governed verifier-cost-model identifier.
    #[must_use]
    pub const fn verifier_cost_model_id(&self) -> VerifierCostModelId {
        self.candidate.verifier_cost_model_id
    }

    /// Returns the per-dispatch verifier-cost cap.
    #[must_use]
    pub const fn max_verifier_cost_units(&self) -> u64 {
        self.candidate.max_verifier_cost_units
    }

    /// Returns the maximum accepted artifact bytes.
    #[must_use]
    pub const fn max_artifact_bytes(&self) -> u64 {
        self.candidate.max_artifact_bytes
    }

    /// Returns the maximum canonical public-input bytes.
    #[must_use]
    pub const fn max_public_input_bytes(&self) -> u64 {
        self.candidate.max_public_input_bytes
    }

    /// Returns the maximum reserved public-output bytes.
    #[must_use]
    pub const fn max_public_output_bytes(&self) -> u64 {
        self.candidate.max_public_output_bytes
    }

    /// Returns whether this policy's inclusive validity window contains `epoch`.
    #[must_use]
    pub const fn is_valid_at(&self, epoch: u64) -> bool {
        self.validity.contains(epoch)
    }

    /// Creates inert policy-derived inputs for one local pre-dispatch cost quote.
    ///
    /// This does not compute a charge or invoke a verifier.
    #[must_use]
    pub const fn cost_quote_request(
        &self,
        artifact_len: u64,
        canonical_statement_len: u64,
    ) -> VerifierCostQuoteRequestV1 {
        VerifierCostQuoteRequestV1::from_policy(self, artifact_len, canonical_statement_len)
    }

    /// Creates the conservative admission-reservation request using maxima.
    ///
    /// The returned request remains inert and carries no admission authority.
    #[must_use]
    pub const fn admission_reservation_quote_request(&self) -> VerifierCostQuoteRequestV1 {
        self.cost_quote_request(
            self.candidate.max_artifact_bytes,
            self.candidate.max_public_input_bytes,
        )
    }

    /// Returns a copy of the validated logical data.
    ///
    /// The returned candidate carries no registry or verifier authority.
    #[must_use]
    pub const fn as_candidate(&self) -> VerifierPolicyCandidateV1 {
        self.candidate
    }
}

impl TryFrom<VerifierPolicyCandidateV1> for VerifierPolicyV1 {
    type Error = PolicyValidationErrorV1;

    /// Validates the logical schema and inclusive validity interval.
    ///
    /// # Errors
    ///
    /// Returns the first schema or interval error.
    fn try_from(candidate: VerifierPolicyCandidateV1) -> Result<Self, Self::Error> {
        if candidate.schema_version != POLICY_SCHEMA_VERSION_V1 {
            return Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
                object: PolicyObjectV1::VerifierPolicy,
                actual: candidate.schema_version,
            });
        }
        let validity = ValidityWindowV1::try_new(
            PolicyObjectV1::VerifierPolicy,
            candidate.validity_start_epoch,
            candidate.validity_end_epoch,
        )?;
        Ok(Self {
            candidate,
            validity,
        })
    }
}

impl MachinePolicyV1 {
    /// Checks deterministic structural compatibility with one verifier policy.
    ///
    /// Order: machine, domain, cost model, machine window, verifier window,
    /// artifact limits, then verifier-cost limit. Opaque registry roots are not
    /// treated as membership evidence, and this method creates no capability.
    ///
    /// # Errors
    ///
    /// Returns the first [`VerifierCompatibilityErrorV1`] in the order above.
    pub fn validate_verifier_candidate_compatibility(
        &self,
        verifier: &VerifierPolicyV1,
        epoch_candidate: u64,
    ) -> Result<(), VerifierCompatibilityErrorV1> {
        if self.machine_id() != verifier.machine_id() {
            return Err(VerifierCompatibilityErrorV1::MachineMismatch);
        }
        if self.domain_id() != verifier.domain_id() {
            return Err(VerifierCompatibilityErrorV1::DomainMismatch);
        }
        if self.verifier_cost_model_id() != verifier.verifier_cost_model_id() {
            return Err(VerifierCompatibilityErrorV1::CostModelMismatch);
        }
        if !self.is_valid_at(epoch_candidate) {
            return Err(VerifierCompatibilityErrorV1::MachinePolicyInactive);
        }
        if !verifier.is_valid_at(epoch_candidate) {
            return Err(VerifierCompatibilityErrorV1::VerifierPolicyInactive);
        }
        let machine_limits = self.limits();
        if verifier.max_artifact_bytes() > u64::from(machine_limits.max_proof_artifact_bytes())
            || verifier.max_artifact_bytes() > u64::from(machine_limits.max_total_proof_bytes())
        {
            return Err(VerifierCompatibilityErrorV1::ArtifactLimitExceedsMachine);
        }
        if verifier.max_verifier_cost_units() > machine_limits.max_total_verifier_cost_units() {
            return Err(VerifierCompatibilityErrorV1::VerifierCostLimitExceedsMachine);
        }
        Ok(())
    }

    /// Checks the exact admission-policy ID before generic candidate shape.
    ///
    /// `LocalKernel` rejects every admission verifier candidate. A required
    /// verifier must carry the exact `VerifierPolicyId` selected by this
    /// machine-policy candidate. The supplied epoch remains caller-provided
    /// data; this method performs no activation, registry, or revocation check.
    ///
    /// # Errors
    ///
    /// Returns an admission-mode or policy-ID error first, followed by the
    /// generic structural compatibility errors.
    pub fn validate_admission_verifier_candidate(
        &self,
        verifier: &VerifierPolicyV1,
        epoch_candidate: u64,
    ) -> Result<(), VerifierCompatibilityErrorV1> {
        match self.admission_policy() {
            AdmissionPolicyV1::LocalKernel => {
                return Err(VerifierCompatibilityErrorV1::AdmissionVerifierForbidden);
            }
            AdmissionPolicyV1::RequiredVerifier(expected_policy_id)
                if expected_policy_id != verifier.verifier_policy_id() =>
            {
                return Err(VerifierCompatibilityErrorV1::AdmissionVerifierPolicyMismatch);
            }
            AdmissionPolicyV1::RequiredVerifier(_) => {}
        }
        self.validate_verifier_candidate_compatibility(verifier, epoch_candidate)
    }
}
