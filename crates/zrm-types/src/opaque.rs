use crate::DIGEST_BYTES;
use core::fmt;

/// Error returned when a semantic 32-byte value is all zero.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ZeroValueError;

impl fmt::Display for ZeroValueError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("all-zero semantic values are prohibited")
    }
}

#[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
struct NonZeroBytes32([u8; DIGEST_BYTES]);

impl NonZeroBytes32 {
    fn try_new(bytes: [u8; DIGEST_BYTES]) -> Result<Self, ZeroValueError> {
        if bytes.iter().all(|byte| *byte == 0) {
            return Err(ZeroValueError);
        }
        Ok(Self(bytes))
    }

    const fn as_bytes(&self) -> &[u8; DIGEST_BYTES] {
        &self.0
    }

    const fn into_bytes(self) -> [u8; DIGEST_BYTES] {
        self.0
    }
}

fn write_redacted(type_name: &str, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
    write!(formatter, "{type_name}([REDACTED])")
}

// Every type below has the same representation invariant. Centralizing that
// one invariant keeps constructors identical while retaining distinct public
// Rust types at every semantic boundary.
macro_rules! define_nonzero_bytes32 {
    ($name:ident, $documentation:literal) => {
        #[doc = $documentation]
        #[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
        #[repr(transparent)]
        pub struct $name(NonZeroBytes32);

        impl $name {
            /// Returns the validated fixed-width bytes.
            #[must_use]
            pub const fn as_bytes(&self) -> &[u8; DIGEST_BYTES] {
                self.0.as_bytes()
            }

            /// Consumes the value and returns its fixed-width bytes.
            #[must_use]
            pub const fn into_bytes(self) -> [u8; DIGEST_BYTES] {
                self.0.into_bytes()
            }
        }

        impl TryFrom<[u8; DIGEST_BYTES]> for $name {
            type Error = ZeroValueError;

            /// Validates the local nonzero representation invariant.
            ///
            /// This conversion does not authenticate caller-provided data.
            fn try_from(bytes: [u8; DIGEST_BYTES]) -> Result<Self, Self::Error> {
                NonZeroBytes32::try_new(bytes).map(Self)
            }
        }

        impl fmt::Debug for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                write_redacted(stringify!($name), formatter)
            }
        }
    };
}

define_nonzero_bytes32!(MachineId, "Opaque machine identifier.");
define_nonzero_bytes32!(DomainId, "Opaque replay and authority domain identifier.");
define_nonzero_bytes32!(ApplicationId, "Opaque application-domain identifier.");
define_nonzero_bytes32!(
    ResourceId,
    "Opaque resource commitment identifier. Raw construction is inert data; authoritative use requires canonical derivation and later semantic validation."
);
define_nonzero_bytes32!(
    ResourceNonce,
    "Opaque nonzero resource nonce. This local invariant establishes no freshness, uniqueness, or privacy."
);
define_nonzero_bytes32!(ResourceKindId, "Opaque resource-kind identifier.");
define_nonzero_bytes32!(ResourceLogicId, "Opaque resource-logic identifier.");
define_nonzero_bytes32!(LogicProfileId, "Opaque resource-logic profile identifier.");
define_nonzero_bytes32!(
    TransformationRuleId,
    "Opaque transformation-rule identifier."
);
define_nonzero_bytes32!(
    TransformationProfileId,
    "Opaque transformation-profile identifier."
);
define_nonzero_bytes32!(AuthorityKindId, "Opaque authority-kind identifier.");
define_nonzero_bytes32!(
    DataAvailabilityProfileId,
    "Opaque data-availability profile identifier."
);
define_nonzero_bytes32!(PolicyId, "Opaque policy identifier.");
define_nonzero_bytes32!(VerifierId, "Opaque verifier implementation identifier.");
define_nonzero_bytes32!(
    VerifierPolicyId,
    "Opaque governed verifier-policy identifier."
);
define_nonzero_bytes32!(
    VerifierCostModelId,
    "Opaque verifier-cost-model identifier."
);
define_nonzero_bytes32!(VerifierCostRowHash, "Opaque verifier-cost-row hash.");
define_nonzero_bytes32!(
    BackendFamilyId,
    "Opaque verifier backend-family identifier."
);
define_nonzero_bytes32!(ArtifactCodecId, "Opaque proof-artifact codec identifier.");
define_nonzero_bytes32!(CryptoSuiteId, "Opaque cryptographic-suite identifier.");
define_nonzero_bytes32!(
    AccumulatorProfileId,
    "Opaque accumulator-profile identifier."
);
define_nonzero_bytes32!(UnitId, "Opaque quantity-unit identifier.");
define_nonzero_bytes32!(ControllerRoot, "Opaque resource-controller root.");
define_nonzero_bytes32!(Commitment, "Opaque generic protocol commitment.");
define_nonzero_bytes32!(Nullifier, "Opaque exact-once nullifier.");
define_nonzero_bytes32!(TransitionId, "Opaque transition identifier.");
define_nonzero_bytes32!(StatementHash, "Opaque transition-statement hash.");
define_nonzero_bytes32!(LogicClaimHash, "Opaque logic-claim hash.");
define_nonzero_bytes32!(
    LogicStatementHash,
    "Opaque proof-bound logic-statement hash."
);
define_nonzero_bytes32!(TransformationClaimHash, "Opaque transformation-claim hash.");
define_nonzero_bytes32!(
    TransformationStatementHash,
    "Opaque proof-bound transformation-statement hash."
);
define_nonzero_bytes32!(AuthorityClaimHash, "Opaque authority-claim hash.");
define_nonzero_bytes32!(
    AuthorityStatementHash,
    "Opaque proof-bound authority-statement hash."
);
define_nonzero_bytes32!(
    DataAvailabilityClaimHash,
    "Opaque data-availability claim hash."
);
define_nonzero_bytes32!(
    DataAvailabilityStatementHash,
    "Opaque proof-bound data-availability-statement hash."
);
define_nonzero_bytes32!(
    ValidationContextHash,
    "Opaque trusted-validation-context hash."
);
define_nonzero_bytes32!(RequestDigest, "Opaque bounded-request digest.");
define_nonzero_bytes32!(RejectReceiptHash, "Opaque reject-receipt hash.");
define_nonzero_bytes32!(JournalDraftHash, "Opaque precommit journal-draft hash.");
define_nonzero_bytes32!(JournalHash, "Opaque accepted-journal hash.");
define_nonzero_bytes32!(EvidenceRoot, "Opaque evidence root.");
define_nonzero_bytes32!(ProvenanceRoot, "Opaque provenance root.");
define_nonzero_bytes32!(
    DataAvailabilityRoot,
    "Opaque data-availability content root."
);
define_nonzero_bytes32!(
    MachineStateRoot,
    "Opaque committed machine-state root. Raw construction does not authenticate state."
);
define_nonzero_bytes32!(
    MachinePolicyRoot,
    "Opaque future machine-policy-root candidate. Raw construction establishes no encoding, derivation, authentication, or activation."
);
define_nonzero_bytes32!(
    OrderingContextRoot,
    "Opaque authenticated-ordering-context root candidate."
);
define_nonzero_bytes32!(
    SupportedResourceSchemaRoot,
    "Opaque root of resource schemas admitted by a machine policy."
);
define_nonzero_bytes32!(
    SupportedTransitionSchemaRoot,
    "Opaque root of transition schemas admitted by a machine policy."
);
define_nonzero_bytes32!(
    ResourceKindPolicySetRoot,
    "Opaque root of resource-kind policies accepted for reading or consumption."
);
define_nonzero_bytes32!(
    CreationResourceKindPolicyMapRoot,
    "Opaque root of the current creation-policy map."
);
define_nonzero_bytes32!(
    AcceptedPredecessorResourcePolicySetRoot,
    "Opaque root of accepted predecessor resource policies."
);
define_nonzero_bytes32!(
    LogicVerifierPolicyRoot,
    "Opaque root of governed logic-verifier policies."
);
define_nonzero_bytes32!(
    TransformationVerifierPolicyRoot,
    "Opaque root of governed transformation-verifier policies."
);
define_nonzero_bytes32!(
    AuthorityVerifierPolicyRoot,
    "Opaque root of governed authority-verifier policies."
);
define_nonzero_bytes32!(
    DataAvailabilityPolicyRoot,
    "Opaque root of governed data-availability policies."
);
define_nonzero_bytes32!(
    GovernanceAuthorityRoot,
    "Opaque root of policy-governance authority."
);
define_nonzero_bytes32!(FeatureSuiteRoot, "Opaque root of enabled feature profiles.");
define_nonzero_bytes32!(
    AllowedLogicSetRoot,
    "Opaque root of resource logics allowed by a resource-kind policy."
);
define_nonzero_bytes32!(
    AllowedLogicProfileSetRoot,
    "Opaque root of logic profiles allowed by a resource-kind policy."
);
define_nonzero_bytes32!(
    AllowedTransformationSetRoot,
    "Opaque root of transformations allowed by a resource-kind policy."
);
define_nonzero_bytes32!(
    ControllerPolicyRoot,
    "Opaque root of resource-controller policy."
);
define_nonzero_bytes32!(MintAuthorityRoot, "Opaque root of mint authority policy.");
define_nonzero_bytes32!(BurnAuthorityRoot, "Opaque root of burn authority policy.");
define_nonzero_bytes32!(
    ProgramOrKeyDigest,
    "Opaque digest of a verifier program or verification key."
);
define_nonzero_bytes32!(
    StatementSchemaRoot,
    "Opaque root of statement schemas accepted by a verifier policy."
);
define_nonzero_bytes32!(
    JournalSchemaRoot,
    "Opaque root of journal schemas accepted by a verifier policy."
);
define_nonzero_bytes32!(
    ProofParameterRoot,
    "Opaque root of proof-system parameters."
);
define_nonzero_bytes32!(
    CoverageClaimsRoot,
    "Opaque root of a verifier profile's scoped coverage claims."
);
define_nonzero_bytes32!(
    NonClaimsRoot,
    "Opaque root of a verifier profile's explicit non-claims."
);
define_nonzero_bytes32!(
    TrustedComputingBaseRoot,
    "Opaque root of a verifier profile's trusted computing base."
);
define_nonzero_bytes32!(
    VerifierCostRowsRoot,
    "Opaque future verifier-cost-rows-root candidate. Raw construction establishes no encoding, ordering, derivation, or authentication."
);

#[cfg(test)]
mod tests {
    use super::{CryptoSuiteId, MachineId, ResourceNonce, ZeroValueError};

    #[test]
    fn opaque_identifier_rejects_all_zero_bytes() {
        assert_eq!(MachineId::try_from([0; 32]), Err(ZeroValueError));
    }

    #[test]
    fn opaque_identifier_preserves_nonzero_bytes() -> Result<(), ZeroValueError> {
        let bytes = [0x5a; 32];
        let identifier = MachineId::try_from(bytes)?;
        assert_eq!(identifier.as_bytes(), &bytes);
        assert_eq!(identifier.into_bytes(), bytes);
        assert_eq!(std::format!("{identifier:?}"), "MachineId([REDACTED])");
        Ok(())
    }

    #[test]
    fn resource_nonce_debug_is_value_independent_and_bytes_remain_explicitly_available()
    -> Result<(), ZeroValueError> {
        let first_bytes = [0xa5; 32];
        let second_bytes = [0x5a; 32];
        let first = ResourceNonce::try_from(first_bytes)?;
        let second = ResourceNonce::try_from(second_bytes)?;
        assert_eq!(std::format!("{first:?}"), "ResourceNonce([REDACTED])");
        assert_eq!(std::format!("{first:?}"), std::format!("{second:?}"));
        assert_eq!(first.as_bytes(), &first_bytes);
        assert_eq!(second.into_bytes(), second_bytes);
        Ok(())
    }

    #[test]
    fn distinct_identifier_types_validate_independently() {
        let machine = MachineId::try_from([1; 32]);
        let suite = CryptoSuiteId::try_from([1; 32]);
        assert!(machine.is_ok());
        assert!(suite.is_ok());
    }

    #[test]
    fn zero_value_error_has_stable_diagnostic() {
        assert_eq!(
            std::format!("{ZeroValueError}"),
            "all-zero semantic values are prohibited"
        );
    }
}

#[cfg(kani)]
mod kani_harnesses {
    use super::MachineId;

    #[kani::proof]
    #[kani::unwind(33)]
    fn nonzero_identifier_constructor_matches_byte_predicate() {
        let bytes: [u8; 32] = kani::any();
        let constructed = MachineId::try_from(bytes);
        let has_nonzero_byte = bytes.iter().any(|byte| *byte != 0);
        assert_eq!(constructed.is_ok(), has_nonzero_byte);
    }
}
