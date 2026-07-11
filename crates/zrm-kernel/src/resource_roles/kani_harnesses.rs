//! Bounded model checks for the production resource-role constructor.

use super::{
    CanonicalResourceRolesV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRoleV1,
};
use zrm_policy::PolicyLimitsV1;
use zrm_types::ResourceId;

mod collision;
mod count;
mod duplicate;

fn resource_id(marker: u8) -> Option<ResourceId> {
    ResourceId::try_from([marker; 32]).ok()
}

fn symbolic_resource_id(maximum: u8) -> Option<ResourceId> {
    let marker: u8 = kani::any();
    kani::assume(marker >= 1);
    kani::assume(marker <= maximum);
    resource_id(marker)
}

fn symbolic_role() -> ResourceRoleV1 {
    let selector: u8 = kani::any();
    kani::assume(selector <= 2);
    if selector == 0 {
        ResourceRoleV1::Consumed
    } else if selector == 1 {
        ResourceRoleV1::Referenced
    } else {
        ResourceRoleV1::Created
    }
}
