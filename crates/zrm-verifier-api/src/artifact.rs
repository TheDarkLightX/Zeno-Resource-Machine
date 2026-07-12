use alloc::vec::Vec;
use core::fmt;

use zrm_policy::PolicyLimitsV1;

/// Failure while bounding one untrusted verifier artifact.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ArtifactErrorV1 {
    /// The caller selected a limit above the protocol ceiling.
    LimitExceedsProtocolCeiling,
    /// The artifact length exceeds the selected policy limit.
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
        if selected_max_bytes > PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES {
            return Err(ArtifactErrorV1::LimitExceedsProtocolCeiling);
        }
        let byte_len = u64::try_from(bytes.len()).map_err(|_| ArtifactErrorV1::ArtifactTooLarge)?;
        if byte_len > u64::from(selected_max_bytes) {
            return Err(ArtifactErrorV1::ArtifactTooLarge);
        }
        let mut bounded = Vec::new();
        bounded
            .try_reserve_exact(bytes.len())
            .map_err(|_| ArtifactErrorV1::AllocationLimitExceeded)?;
        bounded.extend_from_slice(bytes);
        Ok(Self { bytes: bounded })
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
