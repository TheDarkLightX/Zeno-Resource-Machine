//! Local, noncanonical intrinsic-resource diagnostics.

use core::fmt;

use zrm_codec::ResourceIdDerivationError;

/// A version-one wire field whose local nonzero invariant can fail.
///
/// The variant order follows the frozen `ResourceWireV1` field order. It is a
/// local diagnostic set, not a canonical wire tag or stable reject code.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IntrinsicResourceFieldV1 {
    /// Candidate machine identifier.
    MachineId,
    /// Candidate authority and replay domain identifier.
    DomainId,
    /// Candidate application identifier.
    ApplicationId,
    /// Candidate resource-kind identifier.
    ResourceKindId,
    /// Candidate resource-logic identifier.
    ResourceLogicId,
    /// Candidate logic-profile identifier.
    LogicProfileId,
    /// Candidate resource-kind-policy identifier.
    ResourceKindPolicyId,
    /// Candidate unit identifier.
    UnitId,
    /// Candidate label commitment.
    LabelRoot,
    /// Candidate value commitment.
    ValueRoot,
    /// Candidate controller root.
    ControllerRoot,
    /// Candidate resource policy root.
    PolicyRoot,
    /// Candidate provenance root.
    ProvenanceRoot,
    /// Candidate resource nonce.
    Nonce,
}

impl IntrinsicResourceFieldV1 {
    const fn label(self) -> &'static str {
        match self {
            Self::MachineId => "machine_id",
            Self::DomainId => "domain_id",
            Self::ApplicationId => "application_id",
            Self::ResourceKindId => "resource_kind_id",
            Self::ResourceLogicId => "resource_logic_id",
            Self::LogicProfileId => "logic_profile_id",
            Self::ResourceKindPolicyId => "resource_kind_policy_id",
            Self::UnitId => "unit_id",
            Self::LabelRoot => "label_root",
            Self::ValueRoot => "value_root",
            Self::ControllerRoot => "controller_root",
            Self::PolicyRoot => "policy_root",
            Self::ProvenanceRoot => "provenance_root",
            Self::Nonce => "nonce",
        }
    }
}

/// Local failure while constructing an `IntrinsicResourceV1`.
///
/// This closed error set has deterministic local precedence. It is not mapped
/// to `RejectCodeV1` and does not freeze final resource-validation precedence.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IntrinsicResourceErrorV1 {
    /// A field required to be nonzero contained only zero bytes.
    ZeroField {
        /// The first zero field in canonical field order.
        field: IntrinsicResourceFieldV1,
    },
    /// The expiry epoch preceded the creation epoch.
    ExpiryBeforeCreation {
        /// Candidate resource creation epoch.
        created_epoch: u64,
        /// Candidate resource expiry epoch.
        expiry_epoch: u64,
    },
    /// Version one encountered flag bits outside its empty known mask.
    UnknownFlags {
        /// Exact rejected flag bits.
        bits: u32,
    },
    /// Canonical encoding or exact resource-commitment derivation failed.
    ResourceIdDerivation(ResourceIdDerivationError),
}

impl fmt::Display for IntrinsicResourceErrorV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ZeroField { field } => {
                write!(
                    formatter,
                    "zero intrinsic resource field: {}",
                    field.label()
                )
            }
            Self::ExpiryBeforeCreation { .. } => {
                formatter.write_str("resource expiry precedes creation")
            }
            Self::UnknownFlags { bits } => {
                write!(formatter, "unknown ResourceFlagsV1 bits: 0x{bits:08x}")
            }
            Self::ResourceIdDerivation(error) => {
                write!(formatter, "resource ID derivation failed: {error}")
            }
        }
    }
}
