//! Opaque primitive types for the Zeno Resource Machine.
//!
//! WP1 types validate only their documented local representation invariants.
//! They do not establish resource, policy, state, or verifier authority.

#![no_std]

#[cfg(test)]
extern crate std;

mod opaque;
mod quantity;
mod reject;
mod resource_flags;

pub use opaque::{
    AcceptedPredecessorResourcePolicySetRoot, AccumulatorProfileId, AllowedLogicProfileSetRoot,
    AllowedLogicSetRoot, AllowedTransformationSetRoot, ApplicationId, ArtifactCodecId,
    AuthorityClaimHash, AuthorityKindId, AuthorityStatementHash, AuthorityVerifierPolicyRoot,
    BackendFamilyId, BurnAuthorityRoot, Commitment, ControllerPolicyRoot, ControllerRoot,
    CoverageClaimsRoot, CreationResourceKindPolicyMapRoot, CryptoSuiteId,
    DataAvailabilityClaimHash, DataAvailabilityPolicyRoot, DataAvailabilityProfileId,
    DataAvailabilityRoot, DataAvailabilityStatementHash, DomainId, EvidenceRoot, FeatureSuiteRoot,
    GovernanceAuthorityRoot, JournalDraftHash, JournalHash, JournalSchemaRoot, LogicClaimHash,
    LogicProfileId, LogicStatementHash, LogicVerifierPolicyRoot, MachineId, MachinePolicyRoot,
    MachineStateRoot, MintAuthorityRoot, NonClaimsRoot, Nullifier, OrderingContextRoot, PolicyId,
    ProgramOrKeyDigest, ProofParameterRoot, ProvenanceRoot, RejectReceiptHash, RequestDigest,
    ResourceId, ResourceKindId, ResourceKindPolicySetRoot, ResourceLogicId, StatementHash,
    StatementSchemaRoot, SupportedResourceSchemaRoot, SupportedTransitionSchemaRoot,
    TransformationClaimHash, TransformationProfileId, TransformationRuleId,
    TransformationStatementHash, TransformationVerifierPolicyRoot, TransitionId,
    TrustedComputingBaseRoot, UnitId, ValidationContextHash, VerifierCostModelId,
    VerifierCostRowHash, VerifierCostRowsRoot, VerifierId, VerifierPolicyId, ZeroValueError,
};
pub use quantity::QuantityAtoms;
pub use reject::{RejectCodeError, RejectCodeV1, RejectStageV1};
pub use resource_flags::{ResourceFlagsV1, UnknownResourceFlagsError};

/// The fixed byte width of ZRM identifiers, roots, and digests.
pub const DIGEST_BYTES: usize = 32;

/// Maximum byte length admitted by the isolated WP1 resource-wire decoder.
pub const MAX_RESOURCE_BYTES: usize = 16_384;

/// Canonical `ResourceWireV1` length when expiry is absent.
pub const RESOURCE_WIRE_V1_ABSENT_EXPIRY_BYTES: usize = 595;

/// Canonical `ResourceWireV1` length when expiry is present.
pub const RESOURCE_WIRE_V1_PRESENT_EXPIRY_BYTES: usize = 603;
