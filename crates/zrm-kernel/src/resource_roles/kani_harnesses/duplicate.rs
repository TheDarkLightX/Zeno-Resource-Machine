//! Exact duplicate rejection for one symbolic selected role.

use super::super::validate_duplicates;
use super::{ResourceRolePartitionErrorV1, ResourceRoleV1, resource_id, symbolic_role};

#[kani::proof]
#[kani::unwind(34)]
fn selected_role_duplicate_validator_rejects_fixed_id() {
    let role = symbolic_role();
    let Some(resource_id) = resource_id(1) else {
        return;
    };
    let resources = [resource_id, resource_id];
    let actual = validate_duplicates(&resources, role);
    assert_eq!(
        actual,
        Err(ResourceRolePartitionErrorV1::DuplicateResourceId { role })
    );
    kani::cover!(role == ResourceRoleV1::Consumed);
    kani::cover!(role == ResourceRoleV1::Referenced);
    kani::cover!(role == ResourceRoleV1::Created);
}
