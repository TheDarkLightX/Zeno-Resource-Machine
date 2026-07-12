//! Allocation-path regressions that require private helper access.

use super::{
    ResourceRolePartitionErrorV1, ResourceRoleV1, reserve_role_capacity, validate_role_count,
};

#[test]
fn capacity_overflow_returns_exact_role_without_allocating() {
    assert_eq!(
        reserve_role_capacity(ResourceRoleV1::Referenced, usize::MAX),
        Err(ResourceRolePartitionErrorV1::CapacityUnavailable {
            role: ResourceRoleV1::Referenced,
        })
    );
}

#[test]
fn platform_width_count_overflow_returns_normalized_role_error() {
    assert_eq!(
        validate_role_count(usize::MAX, ResourceRoleV1::Created, 256),
        Err(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Created,
            maximum: 256,
        })
    );
}
