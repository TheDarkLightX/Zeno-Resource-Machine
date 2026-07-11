//! Opaque primitive types for the Zeno Resource Machine.
//!
//! WP1 types validate only their documented local representation invariants.
//! They do not establish resource, policy, state, or verifier authority.

#![no_std]

#[cfg(test)]
extern crate std;

use core::fmt;

/// The fixed byte width of ZRM identifiers, roots, and digests.
pub const DIGEST_BYTES: usize = 32;

/// Maximum byte length admitted by the isolated WP1 resource-wire decoder.
pub const MAX_RESOURCE_BYTES: usize = 16_384;

/// Canonical `ResourceWireV1` length when expiry is absent.
pub const RESOURCE_WIRE_V1_ABSENT_EXPIRY_BYTES: usize = 595;

/// Canonical `ResourceWireV1` length when expiry is present.
pub const RESOURCE_WIRE_V1_PRESENT_EXPIRY_BYTES: usize = 603;

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

fn write_hex(
    type_name: &str,
    bytes: &[u8; DIGEST_BYTES],
    formatter: &mut fmt::Formatter<'_>,
) -> fmt::Result {
    write!(formatter, "{type_name}(")?;
    for byte in bytes {
        write!(formatter, "{byte:02x}")?;
    }
    formatter.write_str(")")
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
                write_hex(stringify!($name), self.as_bytes(), formatter)
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

/// A nonnegative protocol quantity measured in indivisible atoms.
#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct QuantityAtoms(u128);

impl QuantityAtoms {
    /// Creates an inert quantity candidate.
    ///
    /// Resource-kind policy decides whether zero is semantically admissible.
    #[must_use]
    pub const fn new(value: u128) -> Self {
        Self(value)
    }

    /// Returns the number of atoms.
    #[must_use]
    pub const fn get(self) -> u128 {
        self.0
    }
}

/// Error returned when version-one resource flag bits are unknown.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UnknownResourceFlagsError {
    bits: u32,
}

impl UnknownResourceFlagsError {
    /// Returns the rejected flag bits.
    #[must_use]
    pub const fn bits(self) -> u32 {
        self.bits
    }
}

impl fmt::Display for UnknownResourceFlagsError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "unknown ResourceFlagsV1 bits: 0x{:08x}",
            self.bits
        )
    }
}

/// Semantically validated version-one resource flags.
///
/// Version one defines no flags. The WP1 wire decoder retains raw `u32` flag
/// candidates because semantic construction of `ResourceV1` is deferred.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(transparent)]
pub struct ResourceFlagsV1(u32);

impl ResourceFlagsV1 {
    /// The complete set of flag bits known to schema version one.
    pub const KNOWN_MASK: u32 = 0;

    /// Validates version-one resource flag bits.
    ///
    /// # Errors
    ///
    /// Returns [`UnknownResourceFlagsError`] when any bit is set.
    pub const fn try_from_bits(bits: u32) -> Result<Self, UnknownResourceFlagsError> {
        if bits == Self::KNOWN_MASK {
            Ok(Self(bits))
        } else {
            Err(UnknownResourceFlagsError { bits })
        }
    }

    /// Returns the validated raw bit representation.
    #[must_use]
    pub const fn bits(self) -> u32 {
        self.0
    }
}

/// Validation stage encoded in the high half of a [`RejectCodeV1`].
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RejectStageV1 {
    /// Raw input bounds and allocation ceilings.
    IngressBounds,
    /// Canonical framing, version, ordering, and trailing-byte checks.
    CanonicalDecode,
    /// Independently trusted validation context checks.
    TrustedContext,
    /// Transition identity, role, count, and root structure.
    TransitionStructure,
    /// Committed-state membership and nonmembership.
    StateMembership,
    /// Nullifier, replay, and validity-window freshness.
    Freshness,
    /// Resource-kind policy and resource semantic invariants.
    ResourcePolicy,
    /// Proof, signature, authority, and DA authentication.
    Authentication,
    /// Exact fact coverage and public statement binding.
    StatementBinding,
    /// Unit, arithmetic, conservation, and transformation checks.
    Accounting,
    /// Conflict-footprint and deterministic scheduling checks.
    Conflict,
    /// Journal-draft admission verification.
    Admission,
    /// Atomic commit, durability, and stale-plan checks.
    Commit,
    /// Fail-closed internal error without a stronger claim.
    Internal,
}

impl RejectStageV1 {
    /// Returns the stable version-one stage tag.
    #[must_use]
    pub const fn tag(self) -> u16 {
        match self {
            Self::IngressBounds => 0x0001,
            Self::CanonicalDecode => 0x0002,
            Self::TrustedContext => 0x0003,
            Self::TransitionStructure => 0x0004,
            Self::StateMembership => 0x0005,
            Self::Freshness => 0x0006,
            Self::ResourcePolicy => 0x0007,
            Self::Authentication => 0x0008,
            Self::StatementBinding => 0x0009,
            Self::Accounting => 0x000a,
            Self::Conflict => 0x000b,
            Self::Admission => 0x000c,
            Self::Commit => 0x000d,
            Self::Internal => 0x00ff,
        }
    }
}

impl TryFrom<u16> for RejectStageV1 {
    type Error = RejectCodeError;

    /// Converts a stable version-one stage tag.
    fn try_from(tag: u16) -> Result<Self, Self::Error> {
        match tag {
            0x0001 => Ok(Self::IngressBounds),
            0x0002 => Ok(Self::CanonicalDecode),
            0x0003 => Ok(Self::TrustedContext),
            0x0004 => Ok(Self::TransitionStructure),
            0x0005 => Ok(Self::StateMembership),
            0x0006 => Ok(Self::Freshness),
            0x0007 => Ok(Self::ResourcePolicy),
            0x0008 => Ok(Self::Authentication),
            0x0009 => Ok(Self::StatementBinding),
            0x000a => Ok(Self::Accounting),
            0x000b => Ok(Self::Conflict),
            0x000c => Ok(Self::Admission),
            0x000d => Ok(Self::Commit),
            0x00ff => Ok(Self::Internal),
            unknown => Err(RejectCodeError::UnknownStage(unknown)),
        }
    }
}

/// Error returned when a raw reject code violates version-one framing.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RejectCodeError {
    /// The complete reject code was zero.
    Zero,
    /// The high-half stage tag is unknown.
    UnknownStage(u16),
    /// The low-half reason tag was zero.
    ZeroReason,
}

impl fmt::Display for RejectCodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Zero => formatter.write_str("reject code must be nonzero"),
            Self::UnknownStage(stage) => write!(formatter, "unknown reject stage: 0x{stage:04x}"),
            Self::ZeroReason => formatter.write_str("reject reason must be nonzero"),
        }
    }
}

/// Stable version-one reject code encoded as `stage || reason`.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RejectCodeV1 {
    stage: RejectStageV1,
    reason: u16,
}

impl RejectCodeV1 {
    /// Resource wire input exceeds its effective byte bound.
    pub const RESOURCE_WIRE_BYTES: Self = Self::known(RejectStageV1::IngressBounds, 0x0001);
    /// Resource wire input does not contain a complete ten-byte header.
    pub const RESOURCE_WIRE_HEADER: Self = Self::known(RejectStageV1::CanonicalDecode, 0x0001);
    /// Resource wire magic is not `ZRM1`.
    pub const RESOURCE_WIRE_MAGIC: Self = Self::known(RejectStageV1::CanonicalDecode, 0x0002);
    /// Resource wire schema version is unsupported.
    pub const RESOURCE_WIRE_VERSION: Self = Self::known(RejectStageV1::CanonicalDecode, 0x0003);
    /// Resource wire object tag is unsupported.
    pub const RESOURCE_WIRE_OBJECT: Self = Self::known(RejectStageV1::CanonicalDecode, 0x0004);
    /// Resource wire field count is not eighteen.
    pub const RESOURCE_WIRE_FIELD_COUNT: Self = Self::known(RejectStageV1::CanonicalDecode, 0x0005);
    /// A resource field tag/length header is truncated.
    pub const RESOURCE_WIRE_FIELD_HEADER: Self =
        Self::known(RejectStageV1::CanonicalDecode, 0x0006);
    /// A resource field tag is missing, repeated, out of order, or unknown.
    pub const RESOURCE_WIRE_FIELD_TAG: Self = Self::known(RejectStageV1::CanonicalDecode, 0x0007);
    /// A resource field declares a noncanonical value length.
    pub const RESOURCE_WIRE_FIELD_LENGTH: Self =
        Self::known(RejectStageV1::CanonicalDecode, 0x0008);
    /// A resource field value is truncated.
    pub const RESOURCE_WIRE_FIELD_VALUE: Self = Self::known(RejectStageV1::CanonicalDecode, 0x0009);
    /// The expiry option tag and length do not form a canonical option.
    pub const RESOURCE_WIRE_OPTION_TAG: Self = Self::known(RejectStageV1::CanonicalDecode, 0x000a);
    /// Bytes remain after the eighteenth resource field.
    pub const RESOURCE_WIRE_TRAILING: Self = Self::known(RejectStageV1::CanonicalDecode, 0x000b);

    const fn known(stage: RejectStageV1, reason: u16) -> Self {
        Self { stage, reason }
    }

    /// Constructs a framed reject code.
    ///
    /// # Errors
    ///
    /// Returns [`RejectCodeError::ZeroReason`] when `reason` is zero.
    pub const fn try_new(stage: RejectStageV1, reason: u16) -> Result<Self, RejectCodeError> {
        if reason == 0 {
            Err(RejectCodeError::ZeroReason)
        } else {
            Ok(Self { stage, reason })
        }
    }

    /// Returns the stable stage.
    #[must_use]
    pub const fn stage(self) -> RejectStageV1 {
        self.stage
    }

    /// Returns the nonzero reason tag.
    #[must_use]
    pub const fn reason(self) -> u16 {
        self.reason
    }

    /// Returns the canonical `u32` representation.
    #[must_use]
    pub fn value(self) -> u32 {
        (u32::from(self.stage.tag()) << 16) | u32::from(self.reason)
    }

    /// Returns the stable public label for a known WP1 resource-wire code.
    #[must_use]
    pub fn resource_wire_label(self) -> Option<&'static str> {
        match self.value() {
            0x0001_0001 => Some("zrm.bounds.resource_wire_bytes"),
            0x0002_0001 => Some("zrm.malformed.resource_wire_header"),
            0x0002_0002 => Some("zrm.malformed.resource_wire_magic"),
            0x0002_0003 => Some("zrm.malformed.resource_wire_version"),
            0x0002_0004 => Some("zrm.malformed.resource_wire_object"),
            0x0002_0005 => Some("zrm.malformed.resource_wire_field_count"),
            0x0002_0006 => Some("zrm.malformed.resource_wire_field_header"),
            0x0002_0007 => Some("zrm.canonical.resource_wire_field_tag"),
            0x0002_0008 => Some("zrm.canonical.resource_wire_field_length"),
            0x0002_0009 => Some("zrm.malformed.resource_wire_field_value"),
            0x0002_000a => Some("zrm.canonical.resource_wire_option_tag"),
            0x0002_000b => Some("zrm.canonical.resource_wire_trailing"),
            _ => None,
        }
    }
}

impl TryFrom<u32> for RejectCodeV1 {
    type Error = RejectCodeError;

    /// Validates a raw version-one reject code.
    fn try_from(value: u32) -> Result<Self, Self::Error> {
        if value == 0 {
            return Err(RejectCodeError::Zero);
        }
        let stage_tag = u16::try_from(value >> 16).map_err(|_| RejectCodeError::UnknownStage(0))?;
        let stage = RejectStageV1::try_from(stage_tag)?;
        let reason = u16::try_from(value & 0x0000_ffff).map_err(|_| RejectCodeError::ZeroReason)?;
        Self::try_new(stage, reason)
    }
}

#[cfg(test)]
mod tests {
    use super::{
        CryptoSuiteId, MachineId, QuantityAtoms, RejectCodeError, RejectCodeV1, RejectStageV1,
        ResourceFlagsV1, UnknownResourceFlagsError, ZeroValueError,
    };

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
        assert_eq!(
            std::format!("{identifier:?}"),
            std::format!("MachineId({})", "5a".repeat(32))
        );
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
    fn quantity_preserves_full_u128_range() {
        assert_eq!(QuantityAtoms::new(u128::MAX).get(), u128::MAX);
    }

    #[test]
    fn resource_flags_v1_accept_only_zero() {
        assert_eq!(
            ResourceFlagsV1::try_from_bits(0).map(ResourceFlagsV1::bits),
            Ok(0)
        );
        assert_eq!(
            ResourceFlagsV1::try_from_bits(1),
            Err(UnknownResourceFlagsError { bits: 1 })
        );
        let rejected = ResourceFlagsV1::try_from_bits(0x8000_0001);
        assert_eq!(
            rejected,
            Err(UnknownResourceFlagsError { bits: 0x8000_0001 })
        );
        if let Err(error) = rejected {
            assert_eq!(error.bits(), 0x8000_0001);
            assert_eq!(
                std::format!("{error}"),
                "unknown ResourceFlagsV1 bits: 0x80000001"
            );
        }
    }

    #[test]
    fn reject_code_round_trips_stage_and_reason() {
        let code = RejectCodeV1::RESOURCE_WIRE_TRAILING;
        assert_eq!(code.value(), 0x0002_000b);
        assert_eq!(RejectCodeV1::try_from(code.value()), Ok(code));
        assert_eq!(code.stage(), RejectStageV1::CanonicalDecode);
        assert_eq!(code.reason(), 0x000b);
    }

    #[test]
    fn every_reject_stage_tag_round_trips() {
        let stages = [
            (RejectStageV1::IngressBounds, 0x0001),
            (RejectStageV1::CanonicalDecode, 0x0002),
            (RejectStageV1::TrustedContext, 0x0003),
            (RejectStageV1::TransitionStructure, 0x0004),
            (RejectStageV1::StateMembership, 0x0005),
            (RejectStageV1::Freshness, 0x0006),
            (RejectStageV1::ResourcePolicy, 0x0007),
            (RejectStageV1::Authentication, 0x0008),
            (RejectStageV1::StatementBinding, 0x0009),
            (RejectStageV1::Accounting, 0x000a),
            (RejectStageV1::Conflict, 0x000b),
            (RejectStageV1::Admission, 0x000c),
            (RejectStageV1::Commit, 0x000d),
            (RejectStageV1::Internal, 0x00ff),
        ];
        for (stage, tag) in stages {
            assert_eq!(stage.tag(), tag);
            assert_eq!(RejectStageV1::try_from(tag), Ok(stage));
        }
    }

    #[test]
    fn reject_code_rejects_zero_and_unknown_stage() {
        assert_eq!(RejectCodeV1::try_from(0), Err(RejectCodeError::Zero));
        assert_eq!(
            RejectCodeV1::try_from(0x0010_0001),
            Err(RejectCodeError::UnknownStage(0x0010))
        );
        assert_eq!(
            RejectCodeV1::try_from(0x0002_0000),
            Err(RejectCodeError::ZeroReason)
        );
    }

    #[test]
    fn every_known_resource_wire_code_has_a_stable_label() {
        let cases = [
            (
                RejectCodeV1::RESOURCE_WIRE_BYTES,
                "zrm.bounds.resource_wire_bytes",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_HEADER,
                "zrm.malformed.resource_wire_header",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_MAGIC,
                "zrm.malformed.resource_wire_magic",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_VERSION,
                "zrm.malformed.resource_wire_version",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_OBJECT,
                "zrm.malformed.resource_wire_object",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_FIELD_COUNT,
                "zrm.malformed.resource_wire_field_count",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_FIELD_HEADER,
                "zrm.malformed.resource_wire_field_header",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_FIELD_TAG,
                "zrm.canonical.resource_wire_field_tag",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH,
                "zrm.canonical.resource_wire_field_length",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_FIELD_VALUE,
                "zrm.malformed.resource_wire_field_value",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_OPTION_TAG,
                "zrm.canonical.resource_wire_option_tag",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_TRAILING,
                "zrm.canonical.resource_wire_trailing",
            ),
        ];
        for (code, label) in cases {
            assert_eq!(code.resource_wire_label(), Some(label));
        }
        let unknown = RejectCodeV1::try_new(RejectStageV1::Internal, 1);
        assert!(unknown.is_ok());
        if let Ok(unknown) = unknown {
            assert_eq!(unknown.resource_wire_label(), None);
        }
    }

    #[test]
    fn primitive_errors_have_stable_diagnostics() {
        assert_eq!(
            std::format!("{ZeroValueError}"),
            "all-zero semantic values are prohibited"
        );
        assert_eq!(
            std::format!("{}", RejectCodeError::Zero),
            "reject code must be nonzero"
        );
        assert_eq!(
            std::format!("{}", RejectCodeError::UnknownStage(0x1234)),
            "unknown reject stage: 0x1234"
        );
        assert_eq!(
            std::format!("{}", RejectCodeError::ZeroReason),
            "reject reason must be nonzero"
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
