//! Version-one logical machine-policy validation.

use zrm_crypto::SHA256_REFERENCE_V1_ID_BYTES;
use zrm_types::{
    AcceptedPredecessorResourcePolicySetRoot, AccumulatorProfileId, AuthorityVerifierPolicyRoot,
    CreationResourceKindPolicyMapRoot, CryptoSuiteId, DataAvailabilityPolicyRoot, DomainId,
    FeatureSuiteRoot, GovernanceAuthorityRoot, LogicVerifierPolicyRoot, MachineId, PolicyId,
    ResourceKindPolicySetRoot, SupportedResourceSchemaRoot, SupportedTransitionSchemaRoot,
    TransformationVerifierPolicyRoot, VerifierCostModelId, VerifierPolicyId,
};

use crate::{
    POLICY_SCHEMA_VERSION_V1, PolicyLimitsCandidateV1, PolicyLimitsV1, PolicyObjectV1,
    PolicyValidationErrorV1, ValidityWindowV1,
};

/// Untrusted admission-mode candidate.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AdmissionModeV1 {
    /// Pure local-kernel admission with no admission verifier.
    LocalKernel,
    /// A separately verified admission receipt is mandatory.
    RequiredVerifier,
}

/// Validated admission policy with invalid option combinations unrepresentable.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AdmissionPolicyV1 {
    /// Pure local-kernel admission and no admission verifier policy.
    LocalKernel,
    /// Required admission verifier policy.
    RequiredVerifier(VerifierPolicyId),
}

impl AdmissionPolicyV1 {
    fn try_from_pair(
        mode: AdmissionModeV1,
        verifier_policy_id: Option<VerifierPolicyId>,
    ) -> Result<Self, PolicyValidationErrorV1> {
        match (mode, verifier_policy_id) {
            (AdmissionModeV1::LocalKernel, None) => Ok(Self::LocalKernel),
            (AdmissionModeV1::LocalKernel, Some(_)) => {
                Err(PolicyValidationErrorV1::UnexpectedAdmissionVerifierPolicy)
            }
            (AdmissionModeV1::RequiredVerifier, Some(policy_id)) => {
                Ok(Self::RequiredVerifier(policy_id))
            }
            (AdmissionModeV1::RequiredVerifier, None) => {
                Err(PolicyValidationErrorV1::MissingAdmissionVerifierPolicy)
            }
        }
    }
}

/// Public, non-authoritative logical machine-policy candidate.
///
/// Opaque roots are data. This candidate does not prove registry membership,
/// governance activation, predecessor acceptance, or creation-policy mapping.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MachinePolicyCandidateV1 {
    /// Candidate logical schema version.
    pub schema_version: u16,
    /// Externally governed policy identifier; no content-hash derivation is yet frozen.
    pub policy_id: PolicyId,
    /// Machine identity.
    pub machine_id: MachineId,
    /// Replay and authority domain.
    pub domain_id: DomainId,
    /// Resource cryptographic suite fixed by schema v1.
    pub crypto_suite_id: CryptoSuiteId,
    /// State-accumulator profile.
    pub accumulator_profile_id: AccumulatorProfileId,
    /// Governed verifier-cost-model identity.
    pub verifier_cost_model_id: VerifierCostModelId,
    /// Root of admitted resource schemas.
    pub supported_resource_schema_root: SupportedResourceSchemaRoot,
    /// Root of admitted transition schemas.
    pub supported_transition_schema_root: SupportedTransitionSchemaRoot,
    /// Root of resource-kind policies accepted for reading or consumption.
    pub resource_kind_policy_set_root: ResourceKindPolicySetRoot,
    /// Root of the one-current-creation-policy-per-kind map.
    pub creation_resource_kind_policy_map_root: CreationResourceKindPolicyMapRoot,
    /// Root of predecessor policies accepted only for reading or consumption.
    pub accepted_predecessor_resource_policy_set_root: AcceptedPredecessorResourcePolicySetRoot,
    /// Root of governed logic-verifier policies.
    pub logic_verifier_policy_root: LogicVerifierPolicyRoot,
    /// Root of governed transformation-verifier policies.
    pub transformation_verifier_policy_root: TransformationVerifierPolicyRoot,
    /// Root of governed authority-verifier policies.
    pub authority_verifier_policy_root: AuthorityVerifierPolicyRoot,
    /// Root of governed data-availability policies.
    pub data_availability_policy_root: DataAvailabilityPolicyRoot,
    /// Candidate admission mode.
    pub admission_mode: AdmissionModeV1,
    /// Admission verifier policy when the mode requires it.
    pub admission_verifier_policy_id: Option<VerifierPolicyId>,
    /// Root of governance authority.
    pub governance_authority_root: GovernanceAuthorityRoot,
    /// Root of enabled feature profiles.
    pub feature_suite_root: FeatureSuiteRoot,
    /// Candidate byte, count, depth, storage, and verifier-cost limits.
    pub limits: PolicyLimitsCandidateV1,
    /// Inclusive first valid logical epoch.
    pub validity_start_epoch: u64,
    /// Inclusive final valid logical epoch.
    pub validity_end_epoch: u64,
}

/// Locally validated version-one logical machine policy.
///
/// This private-field wrapper establishes schema, suite, limit, admission, and
/// interval invariants only. It is not a canonical policy hash or proof that a
/// runtime activated the policy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MachinePolicyV1 {
    candidate: MachinePolicyCandidateV1,
    admission_policy: AdmissionPolicyV1,
    limits: PolicyLimitsV1,
    validity: ValidityWindowV1,
}

impl MachinePolicyV1 {
    /// Returns the local logical schema version.
    #[must_use]
    pub const fn schema_version(&self) -> u16 {
        self.candidate.schema_version
    }

    /// Returns the externally governed policy identifier.
    #[must_use]
    pub const fn policy_id(&self) -> PolicyId {
        self.candidate.policy_id
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

    /// Returns the schema-fixed resource cryptographic suite.
    #[must_use]
    pub const fn crypto_suite_id(&self) -> CryptoSuiteId {
        self.candidate.crypto_suite_id
    }

    /// Returns the governed verifier-cost-model identifier.
    #[must_use]
    pub const fn verifier_cost_model_id(&self) -> VerifierCostModelId {
        self.candidate.verifier_cost_model_id
    }

    /// Returns the validated admission policy.
    #[must_use]
    pub const fn admission_policy(&self) -> AdmissionPolicyV1 {
        self.admission_policy
    }

    /// Returns the validated machine limits.
    #[must_use]
    pub const fn limits(&self) -> PolicyLimitsV1 {
        self.limits
    }

    /// Returns whether this policy's inclusive validity window contains `epoch`.
    #[must_use]
    pub const fn is_valid_at(&self, epoch: u64) -> bool {
        self.validity.contains(epoch)
    }

    /// Returns a copy of the originally validated logical data.
    ///
    /// The returned candidate carries no governance or activation authority.
    #[must_use]
    pub const fn as_candidate(&self) -> MachinePolicyCandidateV1 {
        self.candidate
    }
}

impl TryFrom<MachinePolicyCandidateV1> for MachinePolicyV1 {
    type Error = PolicyValidationErrorV1;

    /// Validates local machine-policy invariants in a deterministic order.
    ///
    /// Order: schema, schema-fixed suite, limits, admission pairing, validity.
    ///
    /// # Errors
    ///
    /// Returns the first [`PolicyValidationErrorV1`] in the order above.
    fn try_from(candidate: MachinePolicyCandidateV1) -> Result<Self, Self::Error> {
        if candidate.schema_version != POLICY_SCHEMA_VERSION_V1 {
            return Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
                object: PolicyObjectV1::MachinePolicy,
                actual: candidate.schema_version,
            });
        }
        if candidate.crypto_suite_id.as_bytes() != &SHA256_REFERENCE_V1_ID_BYTES {
            return Err(PolicyValidationErrorV1::UnsupportedResourceCryptoSuite);
        }
        let limits = PolicyLimitsV1::try_from(candidate.limits)?;
        let admission_policy = AdmissionPolicyV1::try_from_pair(
            candidate.admission_mode,
            candidate.admission_verifier_policy_id,
        )?;
        let validity = ValidityWindowV1::try_new(
            PolicyObjectV1::MachinePolicy,
            candidate.validity_start_epoch,
            candidate.validity_end_epoch,
        )?;
        Ok(Self {
            candidate,
            admission_policy,
            limits,
            validity,
        })
    }
}

#[cfg(kani)]
mod kani_harnesses {
    use super::{AdmissionModeV1, AdmissionPolicyV1};
    use zrm_types::VerifierPolicyId;

    #[kani::proof]
    fn admission_mode_and_policy_presence_matrix_is_exact() {
        let mode = if kani::any() {
            AdmissionModeV1::LocalKernel
        } else {
            AdmissionModeV1::RequiredVerifier
        };
        let has_policy: bool = kani::any();
        let policy = VerifierPolicyId::try_from([1; 32]).ok();
        let candidate_policy = if has_policy { policy } else { None };
        let result = AdmissionPolicyV1::try_from_pair(mode, candidate_policy);
        let expected = matches!(
            (mode, has_policy),
            (AdmissionModeV1::LocalKernel, false) | (AdmissionModeV1::RequiredVerifier, true)
        );
        assert_eq!(result.is_ok(), expected);
    }
}
