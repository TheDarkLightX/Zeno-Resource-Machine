//! Inert validation-context data with local schema validation.

use zrm_types::{
    AccumulatorProfileId, CryptoSuiteId, DomainId, MachineId, MachinePolicyRoot, MachineStateRoot,
    OrderingContextRoot,
};

use crate::{POLICY_SCHEMA_VERSION_V1, PolicyObjectV1, PolicyValidationErrorV1};

/// Public, non-authoritative validation-context candidate.
///
/// Callers may propose this data. Successful local construction never creates
/// a `TrustedValidationContext`; runtime authentication is a later authority
/// boundary and this crate deliberately exports no such constructor or type.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ValidationContextCandidateV1 {
    /// Candidate logical schema version.
    pub schema_version: u16,
    /// Machine identity.
    pub machine_id: MachineId,
    /// Replay and authority domain.
    pub domain_id: DomainId,
    /// Caller-provided logical epoch candidate.
    pub current_epoch: u64,
    /// Expected committed pre-machine-state root candidate.
    pub expected_machine_state_root: MachineStateRoot,
    /// Expected committed state version candidate.
    pub expected_state_version: u64,
    /// Expected active machine-policy-root candidate.
    pub expected_policy_root: MachinePolicyRoot,
    /// Expected resource cryptographic suite.
    pub expected_crypto_suite_id: CryptoSuiteId,
    /// Expected accumulator profile.
    pub expected_accumulator_profile_id: AccumulatorProfileId,
    /// Expected authenticated ordering-context root candidate.
    pub ordering_context_root: OrderingContextRoot,
}

/// Locally validated, non-authoritative validation-context data.
///
/// Private fields prevent unchecked construction of this logical schema, but
/// this type remains inert. Its name intentionally omits `Trusted`.
#[derive(Debug, Eq, PartialEq)]
pub struct ValidationContextV1 {
    candidate: ValidationContextCandidateV1,
}

impl ValidationContextV1 {
    /// Returns the machine identity candidate.
    #[must_use]
    pub const fn machine_id(&self) -> MachineId {
        self.candidate.machine_id
    }

    /// Returns the replay and authority domain candidate.
    #[must_use]
    pub const fn domain_id(&self) -> DomainId {
        self.candidate.domain_id
    }

    /// Returns the unauthenticated logical epoch candidate.
    #[must_use]
    pub const fn current_epoch(&self) -> u64 {
        self.candidate.current_epoch
    }

    /// Returns the expected state-version candidate.
    #[must_use]
    pub const fn expected_state_version(&self) -> u64 {
        self.candidate.expected_state_version
    }

    /// Returns the expected policy-root candidate.
    #[must_use]
    pub const fn expected_policy_root(&self) -> MachinePolicyRoot {
        self.candidate.expected_policy_root
    }

    /// Returns a copy of the locally validated data.
    ///
    /// The returned value is still unauthenticated and non-authoritative.
    #[must_use]
    pub const fn as_candidate(&self) -> ValidationContextCandidateV1 {
        self.candidate
    }
}

impl TryFrom<ValidationContextCandidateV1> for ValidationContextV1 {
    type Error = PolicyValidationErrorV1;

    /// Checks only the currently frozen logical schema version.
    ///
    /// # Errors
    ///
    /// Returns [`PolicyValidationErrorV1::UnsupportedSchemaVersion`] when the
    /// candidate version is not one.
    fn try_from(candidate: ValidationContextCandidateV1) -> Result<Self, Self::Error> {
        if candidate.schema_version != POLICY_SCHEMA_VERSION_V1 {
            return Err(PolicyValidationErrorV1::UnsupportedSchemaVersion {
                object: PolicyObjectV1::ValidationContext,
                actual: candidate.schema_version,
            });
        }
        Ok(Self { candidate })
    }
}
