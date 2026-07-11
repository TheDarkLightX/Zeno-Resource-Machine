use core::fmt;

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

#[cfg(test)]
mod tests {
    use super::{ResourceFlagsV1, UnknownResourceFlagsError};

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
            rejected.map_err(|error| { (error.bits(), std::format!("{error}"),) }),
            Err((
                0x8000_0001,
                std::string::String::from("unknown ResourceFlagsV1 bits: 0x80000001"),
            ))
        );
    }
}
