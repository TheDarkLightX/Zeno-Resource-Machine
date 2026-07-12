use core::fmt;

use zrm_types::RejectCodeV1;

/// Stable failure returned by strict `ResourceWireV1` decoding.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ResourceWireDecodeError {
    code: RejectCodeV1,
}

impl ResourceWireDecodeError {
    pub(crate) const fn new(code: RejectCodeV1) -> Self {
        Self { code }
    }

    /// Returns the stable version-one reject code.
    #[must_use]
    pub const fn code(self) -> RejectCodeV1 {
        self.code
    }

    /// Returns the bounded public diagnostic label.
    #[must_use]
    pub fn label(self) -> &'static str {
        match self.code.resource_wire_label() {
            Some(label) => label,
            None => "zrm.internal.unknown_resource_wire_reject",
        }
    }
}

impl fmt::Display for ResourceWireDecodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.label())
    }
}

/// Failure while allocating a bounded canonical resource encoding.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ResourceWireEncodeError {
    /// The bounded output allocation could not be reserved.
    AllocationFailed,
    /// A field width did not fit its required `u32` frame.
    LengthOverflow,
}

impl fmt::Display for ResourceWireEncodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::AllocationFailed => {
                formatter.write_str("unable to reserve canonical resource bytes")
            }
            Self::LengthOverflow => formatter.write_str("canonical resource field length overflow"),
        }
    }
}

/// Failure while encoding and deriving a syntactic `ResourceId`.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ResourceIdDerivationError {
    /// Canonical resource encoding failed.
    Encode(ResourceWireEncodeError),
    /// A host length did not fit the protocol's explicit hash frame.
    HashFrameLengthOverflow,
    /// SHA-256 returned the prohibited all-zero identifier digest.
    AllZeroDigest,
}

impl fmt::Display for ResourceIdDerivationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Encode(error) => write!(formatter, "resource encoding failed: {error}"),
            Self::HashFrameLengthOverflow => formatter
                .write_str("resource hash derivation failed: hash frame length exceeds its explicit width"),
            Self::AllZeroDigest => formatter.write_str(
                "resource hash derivation failed: protocol hash produced a prohibited all-zero digest",
            ),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{ResourceIdDerivationError, ResourceWireDecodeError, ResourceWireEncodeError};
    use zrm_types::{RejectCodeV1, RejectStageV1};

    #[test]
    fn decode_error_exposes_stable_known_and_fallback_labels()
    -> Result<(), zrm_types::RejectCodeError> {
        let known = ResourceWireDecodeError::new(RejectCodeV1::RESOURCE_WIRE_MAGIC);
        assert_eq!(known.label(), "zrm.malformed.resource_wire_magic");
        assert_eq!(std::format!("{known}"), "zrm.malformed.resource_wire_magic");

        let unknown_code = RejectCodeV1::try_new(RejectStageV1::Internal, 1)?;
        let unknown = ResourceWireDecodeError::new(unknown_code);
        assert_eq!(unknown.label(), "zrm.internal.unknown_resource_wire_reject");
        Ok(())
    }

    #[test]
    fn encode_and_derivation_errors_have_bounded_diagnostics() {
        let allocation = ResourceWireEncodeError::AllocationFailed;
        let overflow = ResourceWireEncodeError::LengthOverflow;
        assert_eq!(
            std::format!("{allocation}"),
            "unable to reserve canonical resource bytes"
        );
        assert_eq!(
            std::format!("{overflow}"),
            "canonical resource field length overflow"
        );
        assert_eq!(
            std::format!("{}", ResourceIdDerivationError::Encode(allocation)),
            "resource encoding failed: unable to reserve canonical resource bytes"
        );
        assert_eq!(
            std::format!("{}", ResourceIdDerivationError::AllZeroDigest),
            "resource hash derivation failed: protocol hash produced a prohibited all-zero digest"
        );
    }
}
