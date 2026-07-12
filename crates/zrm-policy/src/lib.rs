//! Pure in-memory policy validation for the Zeno Resource Machine.
//!
//! This pre-RFC WP2 slice validates logical policy invariants only. It exposes
//! no policy codec or hash, trusted context, verifier registry, backend, or
//! verified authority capability.

#![no_std]

#[cfg(test)]
extern crate std;

mod context;
mod cost;
mod error;
mod limits;
mod machine;
mod resource_kind;
mod verifier;
mod window;

pub use context::{ValidationContextCandidateV1, ValidationContextV1};
pub use cost::{
    VerifierCostErrorV1, VerifierCostModelCandidateV1, VerifierCostModelV1,
    VerifierCostRowCandidateV1, VerifierCostRowV1,
};
pub use error::{LimitFieldV1, PolicyObjectV1, PolicyValidationErrorV1, ResourceDimensionErrorV1};
pub use limits::{PolicyLimitsCandidateV1, PolicyLimitsV1};
pub use machine::{AdmissionModeV1, AdmissionPolicyV1, MachinePolicyCandidateV1, MachinePolicyV1};
pub use resource_kind::{
    AccountingModeV1, DataAvailabilityRequirementV1, ResourceKindPolicyCandidateV1,
    ResourceKindPolicyV1,
};
pub use verifier::{ProofModeV1, VerifierPolicyCandidateV1, VerifierPolicyV1};
pub use window::ValidityWindowV1;

#[cfg(any(test, kani, fuzzing))]
pub(crate) use cost::CandidateVerifierCostQuoteRequestV1;
#[cfg(any(test, kani))]
pub(crate) use error::VerifierCompatibilityErrorV1;

/// Runs assertion-only coverage-guided checks over quarantined cost arithmetic.
///
/// This fuzz-build-only function returns no quote, capability, policy decision,
/// or cost value. It exists solely so an external Cargo Fuzz target can drive
/// internal assertions without exposing authority-shaped results. See the
/// function documentation for its panic contract and constant resource bound.
#[cfg(fuzzing)]
#[doc(hidden)]
pub use cost::fuzz_assert_untrusted_candidate_cost_invariants;

/// Supported logical policy schema version.
pub const POLICY_SCHEMA_VERSION_V1: u16 = 1;
