use alloc::{collections::TryReserveError, vec::Vec};
use core::fmt;

use zrm_policy::PolicyLimitsV1;

struct ReservationRefused;

fn reserve_copy_capacity(requested_bytes: usize) -> Result<Vec<u8>, ReservationRefused> {
    let mut destination = Vec::new();
    destination
        .try_reserve_exact(requested_bytes)
        .map_err(|_: TryReserveError| ReservationRefused)?;
    Ok(destination)
}

/// Failure while bounding one untrusted verifier artifact.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ArtifactErrorV1 {
    /// The caller selected a limit above the protocol ceiling.
    LimitExceedsProtocolCeiling,
    /// The artifact length exceeds the selected explicit limit.
    ArtifactTooLarge,
    /// The bounded copy allocation was refused.
    AllocationLimitExceeded,
}

impl fmt::Display for ArtifactErrorV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let label = match self {
            Self::LimitExceedsProtocolCeiling => "artifact limit exceeds protocol ceiling",
            Self::ArtifactTooLarge => "verifier artifact exceeds selected limit",
            Self::AllocationLimitExceeded => "bounded artifact allocation refused",
        };
        formatter.write_str(label)
    }
}

/// A copied, bounded verifier artifact with no verification authority.
///
/// This type proves only that a byte slice was copied under an explicit bound.
/// It does not authenticate a program, statement, output, policy, role,
/// ordinal, freshness window, or verifier fact.
///
/// Artifact bytes deliberately do not implement [`core::fmt::Debug`]:
///
/// ```compile_fail
/// use zrm_verifier_api::BoundedArtifactV1;
///
/// fn requires_debug<T: core::fmt::Debug>() {}
/// requires_debug::<BoundedArtifactV1>();
/// ```
#[derive(Eq, PartialEq)]
#[must_use = "a bounded artifact has no authority until a governed verifier accepts it"]
pub struct BoundedArtifactV1 {
    bytes: Vec<u8>,
}

fn try_new_with_reservation(
    bytes: &[u8],
    selected_max_bytes: u32,
    reserve_exact: fn(usize) -> Result<Vec<u8>, ReservationRefused>,
) -> Result<BoundedArtifactV1, ArtifactErrorV1> {
    if selected_max_bytes > PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES {
        return Err(ArtifactErrorV1::LimitExceedsProtocolCeiling);
    }
    // On a target narrower than `u32`, an unrepresentable selected bound is
    // larger than every possible slice, so `usize::MAX` preserves the
    // comparison without a platform-dependent rejection branch.
    let selected_max_bytes = match usize::try_from(selected_max_bytes) {
        Ok(limit) => limit,
        Err(_) => usize::MAX,
    };
    if bytes.len() > selected_max_bytes {
        return Err(ArtifactErrorV1::ArtifactTooLarge);
    }
    let mut bounded =
        reserve_exact(bytes.len()).map_err(|_| ArtifactErrorV1::AllocationLimitExceeded)?;
    bounded.extend_from_slice(bytes);
    Ok(BoundedArtifactV1 { bytes: bounded })
}

impl BoundedArtifactV1 {
    /// Copies untrusted bytes under an explicit protocol-bounded limit.
    ///
    /// The numeric limit is caller supplied. Passing this function proves
    /// neither that governance selected the limit nor that any verifier policy
    /// authorized the artifact. A later governed boundary must establish those
    /// facts independently.
    /// The governed verifier registry must recheck [`Self::len`] against its
    /// authenticated machine and verifier policies before dispatch.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactErrorV1::ArtifactTooLarge`] before allocating when
    /// the source exceeds the selected limit. It rejects limits above the
    /// closed protocol ceiling and allocation refusal.
    pub fn try_new(bytes: &[u8], selected_max_bytes: u32) -> Result<Self, ArtifactErrorV1> {
        try_new_with_reservation(bytes, selected_max_bytes, reserve_copy_capacity)
    }

    /// Returns the copied artifact bytes.
    #[must_use]
    pub fn as_bytes(&self) -> &[u8] {
        &self.bytes
    }

    /// Returns the copied artifact length.
    #[must_use]
    pub fn len(&self) -> usize {
        self.bytes.len()
    }

    /// Returns whether the copied artifact is empty.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.bytes.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use alloc::vec::Vec;

    use super::{
        ArtifactErrorV1, ReservationRefused, reserve_copy_capacity, try_new_with_reservation,
    };

    fn refuse_three_bytes(requested_bytes: usize) -> Result<Vec<u8>, ReservationRefused> {
        assert_eq!(requested_bytes, 3);
        Err(ReservationRefused)
    }

    #[test]
    fn capacity_overflow_returns_reservation_refusal() {
        assert!(reserve_copy_capacity(usize::MAX).is_err());
    }

    #[test]
    fn injected_reservation_refusal_reaches_the_constructor_error_path() {
        let result = try_new_with_reservation(&[1, 2, 3], 3, refuse_three_bytes);

        assert!(matches!(
            result,
            Err(ArtifactErrorV1::AllocationLimitExceeded)
        ));
    }

    #[test]
    fn invalid_limit_precedes_the_injected_reserver() {
        let result = try_new_with_reservation(&[], u32::MAX, refuse_three_bytes);

        assert!(matches!(
            result,
            Err(ArtifactErrorV1::LimitExceedsProtocolCeiling)
        ));
    }

    #[test]
    fn oversized_artifact_precedes_the_injected_reserver() {
        let result = try_new_with_reservation(&[1], 0, refuse_three_bytes);

        assert!(matches!(result, Err(ArtifactErrorV1::ArtifactTooLarge)));
    }
}
