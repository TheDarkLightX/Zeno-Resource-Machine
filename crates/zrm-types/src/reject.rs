use core::fmt;

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
    use super::{RejectCodeError, RejectCodeV1, RejectStageV1};

    fn assert_labels(cases: &[(RejectCodeV1, &'static str)]) {
        for (code, label) in cases {
            assert_eq!(code.resource_wire_label(), Some(*label));
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
    fn resource_wire_bounds_code_has_a_stable_label() {
        assert_labels(&[(
            RejectCodeV1::RESOURCE_WIRE_BYTES,
            "zrm.bounds.resource_wire_bytes",
        )]);
    }

    #[test]
    fn malformed_resource_wire_codes_have_stable_labels() {
        assert_labels(&[
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
                RejectCodeV1::RESOURCE_WIRE_FIELD_VALUE,
                "zrm.malformed.resource_wire_field_value",
            ),
        ]);
    }

    #[test]
    fn canonical_resource_wire_codes_have_stable_labels() {
        assert_labels(&[
            (
                RejectCodeV1::RESOURCE_WIRE_FIELD_TAG,
                "zrm.canonical.resource_wire_field_tag",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH,
                "zrm.canonical.resource_wire_field_length",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_OPTION_TAG,
                "zrm.canonical.resource_wire_option_tag",
            ),
            (
                RejectCodeV1::RESOURCE_WIRE_TRAILING,
                "zrm.canonical.resource_wire_trailing",
            ),
        ]);
    }

    #[test]
    fn unknown_resource_wire_code_has_no_label() {
        assert_eq!(
            RejectCodeV1::try_new(RejectStageV1::Internal, 1)
                .map(RejectCodeV1::resource_wire_label),
            Ok(None)
        );
    }

    #[test]
    fn reject_code_errors_have_stable_diagnostics() {
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
