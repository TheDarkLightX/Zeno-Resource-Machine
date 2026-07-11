//! Inclusive policy-validity windows.

use crate::{PolicyObjectV1, PolicyValidationErrorV1};

/// Validated inclusive epoch window.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ValidityWindowV1 {
    start: u64,
    end: u64,
}

impl ValidityWindowV1 {
    /// Validates one inclusive epoch interval for the named object.
    ///
    /// # Errors
    ///
    /// Returns [`PolicyValidationErrorV1::InvalidValidityWindow`] when `end`
    /// is less than `start`.
    pub(crate) const fn try_new(
        object: PolicyObjectV1,
        start: u64,
        end: u64,
    ) -> Result<Self, PolicyValidationErrorV1> {
        if end < start {
            Err(PolicyValidationErrorV1::InvalidValidityWindow { object, start, end })
        } else {
            Ok(Self { start, end })
        }
    }

    /// Returns the inclusive start epoch.
    #[must_use]
    pub const fn start(self) -> u64 {
        self.start
    }

    /// Returns the inclusive end epoch.
    #[must_use]
    pub const fn end(self) -> u64 {
        self.end
    }

    /// Returns whether `epoch` lies in the inclusive interval.
    #[must_use]
    pub const fn contains(self, epoch: u64) -> bool {
        self.start <= epoch && epoch <= self.end
    }
}

#[cfg(test)]
mod tests {
    use super::ValidityWindowV1;
    use crate::{PolicyObjectV1, PolicyValidationErrorV1};

    #[test]
    fn zero_length_window_preserves_both_inclusive_endpoints() -> Result<(), PolicyValidationErrorV1>
    {
        let window = ValidityWindowV1::try_new(PolicyObjectV1::MachinePolicy, 7, 7)?;
        assert_eq!(window.start(), 7);
        assert_eq!(window.end(), 7);
        assert!(window.contains(7));
        Ok(())
    }
}

#[cfg(kani)]
mod kani_harnesses {
    use super::ValidityWindowV1;
    use crate::PolicyObjectV1;

    #[kani::proof]
    fn validity_window_accepts_exactly_noninverted_intervals() {
        let start: u64 = kani::any();
        let end: u64 = kani::any();
        let result = ValidityWindowV1::try_new(PolicyObjectV1::MachinePolicy, start, end);
        assert_eq!(result.is_ok(), start <= end);
        if let Ok(window) = result {
            assert!(window.contains(start));
            assert!(window.contains(end));
        }
    }
}
