//! Behavioral tests for the inert WP5 bounded-artifact boundary.

use zrm_policy::PolicyLimitsV1;
use zrm_verifier_api::{ArtifactErrorV1, BoundedArtifactV1};

#[test]
fn bounded_artifact_copies_bytes_under_the_selected_limit() -> Result<(), ArtifactErrorV1> {
    let bytes = [1_u8, 2, 3];
    let artifact = BoundedArtifactV1::try_new(&bytes, 3)?;
    assert_eq!(artifact.as_bytes(), &bytes);
    assert_eq!(artifact.len(), 3);
    assert!(!artifact.is_empty());
    Ok(())
}

#[test]
fn oversized_artifact_rejects_before_copy() {
    let bytes = [0_u8; 4];
    assert!(matches!(
        BoundedArtifactV1::try_new(&bytes, 3),
        Err(ArtifactErrorV1::ArtifactTooLarge)
    ));
}

#[test]
fn protocol_ceiling_rejects_an_unbounded_policy_limit() {
    assert!(matches!(
        BoundedArtifactV1::try_new(&[], u32::MAX),
        Err(ArtifactErrorV1::LimitExceedsProtocolCeiling)
    ));
}

#[test]
fn exact_selected_limit_and_protocol_ceiling_are_accepted() -> Result<(), ArtifactErrorV1> {
    let at_selected_limit = BoundedArtifactV1::try_new(&[7_u8; 4], 4)?;
    assert_eq!(at_selected_limit.len(), 4);

    let ceiling = usize::try_from(PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES)
        .map_err(|_| ArtifactErrorV1::ArtifactTooLarge)?;
    let bytes = vec![0xA5_u8; ceiling];
    let at_protocol_ceiling =
        BoundedArtifactV1::try_new(&bytes, PolicyLimitsV1::MAX_PROOF_ARTIFACT_BYTES)?;
    assert_eq!(at_protocol_ceiling.as_bytes(), bytes);
    Ok(())
}

#[test]
fn zero_limit_accepts_only_an_empty_artifact() -> Result<(), ArtifactErrorV1> {
    let empty = BoundedArtifactV1::try_new(&[], 0)?;
    assert!(empty.is_empty());
    assert!(matches!(
        BoundedArtifactV1::try_new(&[1], 0),
        Err(ArtifactErrorV1::ArtifactTooLarge)
    ));
    Ok(())
}

#[test]
fn bounded_artifact_owns_an_independent_copy() -> Result<(), ArtifactErrorV1> {
    let mut source = [1_u8, 2, 3];
    let artifact = BoundedArtifactV1::try_new(&source, 3)?;
    source.fill(9);
    assert_eq!(artifact.as_bytes(), &[1, 2, 3]);
    Ok(())
}

#[test]
fn invalid_limit_precedes_artifact_length_rejection() {
    assert_eq!(
        BoundedArtifactV1::try_new(&[0_u8; 4], u32::MAX).err(),
        Some(ArtifactErrorV1::LimitExceedsProtocolCeiling)
    );
}

#[test]
fn every_error_has_a_bounded_nonsecret_diagnostic() {
    let cases = [
        (
            ArtifactErrorV1::LimitExceedsProtocolCeiling,
            "artifact limit exceeds protocol ceiling",
            "LimitExceedsProtocolCeiling",
        ),
        (
            ArtifactErrorV1::ArtifactTooLarge,
            "verifier artifact exceeds selected limit",
            "ArtifactTooLarge",
        ),
        (
            ArtifactErrorV1::AllocationLimitExceeded,
            "bounded artifact allocation refused",
            "AllocationLimitExceeded",
        ),
    ];

    for (error, display, debug) in cases {
        assert_eq!(error.to_string(), display);
        assert_eq!(format!("{error:?}"), debug);
    }
}
