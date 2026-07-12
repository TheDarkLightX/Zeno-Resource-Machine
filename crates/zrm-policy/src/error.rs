//! Typed local policy-validation errors.

use core::fmt;

/// Logical object whose local schema or validity window failed validation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PolicyObjectV1 {
    /// Version-one machine policy.
    MachinePolicy,
    /// Version-one resource-kind policy.
    ResourceKindPolicy,
    /// Version-one validation-context data.
    ValidationContext,
    /// Version-one verifier policy.
    VerifierPolicy,
}

/// Machine-limit field used by deterministic ceiling diagnostics.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LimitFieldV1 {
    /// Complete transition-envelope bytes.
    EnvelopeBytes,
    /// Bytes in one resource body.
    ResourceBytes,
    /// Consumed-resource count.
    ConsumedResources,
    /// Referenced-resource count.
    ReferencedResources,
    /// Created-resource count.
    CreatedResources,
    /// Logic-claim count.
    LogicClaims,
    /// Transformation-claim count.
    TransformationClaims,
    /// Authority-claim count.
    AuthorityClaims,
    /// Data-availability-claim count.
    DataAvailabilityClaims,
    /// Accounting-row count.
    AccountingRows,
    /// Evidence-reference count.
    EvidenceReferences,
    /// Bytes in one proof artifact.
    ProofArtifactBytes,
    /// Total proof-artifact bytes.
    TotalProofBytes,
    /// Total deterministic verifier-cost units.
    TotalVerifierCostUnits,
    /// Maximum nested object depth.
    NestingDepth,
    /// Maximum storage-write bytes.
    StorageWriteBytes,
}

/// Stable failures from local logical policy construction.
///
/// These variants are bounded diagnostics. They are not canonical protocol
/// reject codes; numeric reason tags remain blocked on the policy-ABI RFC.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PolicyValidationErrorV1 {
    /// A logical object declared a schema other than version one.
    UnsupportedSchemaVersion {
        /// Object whose version was rejected.
        object: PolicyObjectV1,
        /// Unsupported caller-provided version.
        actual: u16,
    },
    /// A validity interval has its end before its start.
    InvalidValidityWindow {
        /// Object whose window was rejected.
        object: PolicyObjectV1,
        /// Inclusive start epoch.
        start: u64,
        /// Inclusive end epoch.
        end: u64,
    },
    /// A lifecycle non-fungible policy declared a maximum other than one.
    LifecycleQuantityMaximumMustBeOne {
        /// Rejected maximum quantity.
        actual: u128,
    },
    /// A v1 machine policy selected a suite other than the schema-fixed suite.
    UnsupportedResourceCryptoSuite,
    /// One configured machine limit exceeds its compile-time ceiling.
    LimitExceedsProtocolCeiling {
        /// Limit that exceeded its ceiling.
        field: LimitFieldV1,
        /// Rejected value.
        actual: u64,
        /// Compile-time protocol ceiling.
        ceiling: u64,
    },
    /// The complete 603-byte `ResourceWireV1` form would not fit.
    ResourceWireLimitTooSmall {
        /// Rejected configured limit.
        actual: u32,
        /// Minimum accepted limit.
        minimum: u32,
    },
    /// `LocalKernel` was paired with an admission verifier policy.
    UnexpectedAdmissionVerifierPolicy,
    /// `RequiredVerifier` was not paired with an admission verifier policy.
    MissingAdmissionVerifierPolicy,
}

impl fmt::Display for PolicyValidationErrorV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnsupportedSchemaVersion { object, actual } => {
                write!(formatter, "unsupported {object:?} schema version: {actual}")
            }
            Self::InvalidValidityWindow { object, start, end } => {
                write!(
                    formatter,
                    "invalid {object:?} validity window: {start}..={end}"
                )
            }
            Self::LifecycleQuantityMaximumMustBeOne { actual } => write!(
                formatter,
                "lifecycle quantity maximum must be one, got {actual}"
            ),
            Self::UnsupportedResourceCryptoSuite => {
                formatter.write_str("unsupported ResourceWireV1 cryptographic suite")
            }
            Self::LimitExceedsProtocolCeiling {
                field,
                actual,
                ceiling,
            } => write!(
                formatter,
                "{field:?} limit {actual} exceeds protocol ceiling {ceiling}"
            ),
            Self::ResourceWireLimitTooSmall { actual, minimum } => write!(
                formatter,
                "resource byte limit {actual} is smaller than required minimum {minimum}"
            ),
            Self::UnexpectedAdmissionVerifierPolicy => {
                formatter.write_str("LocalKernel forbids an admission verifier policy")
            }
            Self::MissingAdmissionVerifierPolicy => {
                formatter.write_str("RequiredVerifier requires an admission verifier policy")
            }
        }
    }
}

/// Failure while checking one resource's unit and bounded quantity.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ResourceDimensionErrorV1 {
    /// The resource unit differs from the resource-kind policy unit.
    UnitMismatch,
    /// A lifecycle non-fungible resource did not carry exactly one atom.
    LifecycleQuantityMustBeOne {
        /// Rejected quantity.
        actual: u128,
    },
    /// The current policy schema does not permit zero-quantity resources.
    ZeroQuantityForbidden,
    /// The resource quantity exceeds the policy maximum.
    QuantityExceedsMaximum {
        /// Rejected quantity.
        actual: u128,
        /// Policy maximum.
        maximum: u128,
    },
}

impl fmt::Display for ResourceDimensionErrorV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnitMismatch => formatter.write_str("resource unit does not match policy unit"),
            Self::LifecycleQuantityMustBeOne { actual } => write!(
                formatter,
                "lifecycle non-fungible resource quantity must be one, got {actual}"
            ),
            Self::ZeroQuantityForbidden => {
                formatter.write_str("zero resource quantity is forbidden by policy")
            }
            Self::QuantityExceedsMaximum { actual, maximum } => {
                write!(
                    formatter,
                    "resource quantity {actual} exceeds maximum {maximum}"
                )
            }
        }
    }
}

/// Internal failure while checking untrusted machine/verifier candidate shape.
#[cfg(any(test, kani))]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum VerifierCompatibilityErrorV1 {
    /// Local-kernel admission forbids an admission verifier candidate.
    AdmissionVerifierForbidden,
    /// A required admission verifier carries a different policy identifier.
    AdmissionVerifierPolicyMismatch,
    /// Machine identifiers differ.
    MachineMismatch,
    /// Authority-domain identifiers differ.
    DomainMismatch,
    /// Governed verifier-cost-model identifiers differ.
    CostModelMismatch,
    /// The machine policy is not active at the supplied epoch candidate.
    MachinePolicyInactive,
    /// The verifier policy is not active at the supplied epoch candidate.
    VerifierPolicyInactive,
    /// The verifier artifact maximum exceeds the machine's per-artifact or total limit.
    ArtifactLimitExceedsMachine,
    /// The verifier's per-dispatch cap exceeds the machine's total cost budget.
    VerifierCostLimitExceedsMachine,
}

#[cfg(any(test, kani))]
impl fmt::Display for VerifierCompatibilityErrorV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::AdmissionVerifierForbidden => {
                "LocalKernel forbids an admission verifier candidate"
            }
            Self::AdmissionVerifierPolicyMismatch => {
                "admission verifier policy identifier mismatch"
            }
            Self::MachineMismatch => "verifier policy machine mismatch",
            Self::DomainMismatch => "verifier policy domain mismatch",
            Self::CostModelMismatch => "verifier policy cost-model mismatch",
            Self::MachinePolicyInactive => {
                "machine-policy validity window excludes epoch candidate"
            }
            Self::VerifierPolicyInactive => {
                "verifier-policy validity window excludes epoch candidate"
            }
            Self::ArtifactLimitExceedsMachine => "verifier artifact bound exceeds machine policy",
            Self::VerifierCostLimitExceedsMachine => "verifier cost bound exceeds machine policy",
        })
    }
}
