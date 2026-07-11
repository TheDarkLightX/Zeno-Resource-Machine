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

#[cfg(test)]
mod tests {
    use super::QuantityAtoms;

    #[test]
    fn quantity_preserves_full_u128_range() {
        assert_eq!(QuantityAtoms::new(u128::MAX).get(), u128::MAX);
    }
}
