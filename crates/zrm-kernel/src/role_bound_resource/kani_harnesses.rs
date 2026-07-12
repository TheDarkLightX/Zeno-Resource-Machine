//! Bounded checks for the production role-position binding path.
//!
//! Intrinsic construction and SHA-256 are outside this harness. Existing WP3b
//! vectors, fuzzing, mutation, and Kani evidence cover that earlier stage.

use super::{IntrinsicRoleBindingErrorV1, bind_position};
use crate::{
    CanonicalResourceRolesV1, ResourceRoleListsCandidateV1, ResourceRolePositionV1, ResourceRoleV1,
};
use zrm_policy::PolicyLimitsV1;
use zrm_types::ResourceId;

fn resource_id(marker: u8) -> Option<ResourceId> {
    ResourceId::try_from([marker; 32]).ok()
}

fn fixed_roles() -> Option<CanonicalResourceRolesV1> {
    let one = resource_id(1)?;
    let two = resource_id(2)?;
    let three = resource_id(3)?;
    let four = resource_id(4)?;
    CanonicalResourceRolesV1::try_new(
        ResourceRoleListsCandidateV1 {
            consumed: &[three, one],
            referenced: &[four],
            created: &[two],
        },
        PolicyLimitsV1::strict_default(),
    )
    .ok()
}

fn expected_position(query_marker: u8) -> Option<(ResourceRoleV1, u32)> {
    match query_marker {
        1 => Some((ResourceRoleV1::Consumed, 0)),
        2 => Some((ResourceRoleV1::Created, 0)),
        3 => Some((ResourceRoleV1::Consumed, 1)),
        4 => Some((ResourceRoleV1::Referenced, 0)),
        _ => None,
    }
}

fn assert_expected_position(
    actual: &Result<ResourceRolePositionV1, IntrinsicRoleBindingErrorV1>,
    expected: Option<(ResourceRoleV1, u32)>,
) {
    if let Some(expected) = expected {
        assert_eq!(
            actual
                .as_ref()
                .map(|position| (position.role(), position.ordinal())),
            Ok(expected)
        );
    } else {
        assert_eq!(
            actual,
            &Err(IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles)
        );
    }
}

fn cover_outcomes(actual: &Result<ResourceRolePositionV1, IntrinsicRoleBindingErrorV1>) {
    kani::cover!(actual.is_err());
    kani::cover!(matches!(
        actual.as_ref().map(|position| position.role()),
        Ok(ResourceRoleV1::Consumed)
    ));
    kani::cover!(matches!(
        actual.as_ref().map(|position| position.role()),
        Ok(ResourceRoleV1::Referenced)
    ));
    kani::cover!(matches!(
        actual.as_ref().map(|position| position.role()),
        Ok(ResourceRoleV1::Created)
    ));
}

#[kani::proof]
#[kani::unwind(80)]
fn symbolic_query_matches_exact_role_and_ordinal_or_absence() {
    let query_marker: u8 = kani::any();
    kani::assume((1..=5).contains(&query_marker));
    let query = match resource_id(query_marker) {
        Some(query) => query,
        None => {
            assert!(false);
            return;
        }
    };
    let roles = match fixed_roles() {
        Some(roles) => roles,
        None => {
            assert!(false);
            return;
        }
    };

    let actual = bind_position(&roles, &query);
    assert_expected_position(&actual, expected_position(query_marker));
    cover_outcomes(&actual);
}
