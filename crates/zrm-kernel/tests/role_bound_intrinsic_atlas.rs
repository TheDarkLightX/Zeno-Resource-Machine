//! Exhaustive small-universe oracle for body-to-role binding.

use zrm_codec::ResourceWireV1;
use zrm_kernel::{
    CanonicalResourceRolesV1, IntrinsicResourceErrorV1, IntrinsicResourceV1,
    IntrinsicRoleBindingErrorV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRoleV1,
};
use zrm_policy::PolicyLimitsV1;
use zrm_types::ResourceId;

const UNIVERSE_SIZE: usize = 4;
const ASSIGNMENT_COUNT: u16 = 256;

#[derive(Debug)]
enum AtlasError {
    Intrinsic,
    Partition,
    Binding,
}

impl From<IntrinsicResourceErrorV1> for AtlasError {
    fn from(_: IntrinsicResourceErrorV1) -> Self {
        Self::Intrinsic
    }
}

impl From<ResourceRolePartitionErrorV1> for AtlasError {
    fn from(_: ResourceRolePartitionErrorV1) -> Self {
        Self::Partition
    }
}

fn resource(marker: u8) -> Result<IntrinsicResourceV1, IntrinsicResourceErrorV1> {
    IntrinsicResourceV1::try_from(ResourceWireV1 {
        machine_id: [1; 32],
        domain_id: [2; 32],
        application_id: [3; 32],
        resource_kind_id: [4; 32],
        resource_logic_id: [5; 32],
        logic_profile_id: [6; 32],
        resource_kind_policy_id: [7; 32],
        unit_id: [8; 32],
        quantity_atoms: u128::from(marker),
        label_root: [10; 32],
        value_root: [11; 32],
        controller_root: [12; 32],
        policy_root: [13; 32],
        provenance_root: [14; 32],
        nonce: [marker; 32],
        created_epoch: 1,
        expiry_epoch: Some(1),
        flags: 0,
    })
}

fn assignment_digit(assignment: u16, index: usize) -> u8 {
    let [_, assignment] = assignment.to_be_bytes();
    match index {
        0 => assignment & 0b0000_0011,
        1 => (assignment >> 2) & 0b0000_0011,
        2 => (assignment >> 4) & 0b0000_0011,
        3 => (assignment >> 6) & 0b0000_0011,
        _ => 0,
    }
}

fn expected_role(digit: u8) -> Option<ResourceRoleV1> {
    match digit {
        1 => Some(ResourceRoleV1::Consumed),
        2 => Some(ResourceRoleV1::Referenced),
        3 => Some(ResourceRoleV1::Created),
        _ => None,
    }
}

fn expected_ordinal(
    resources: &[IntrinsicResourceV1; UNIVERSE_SIZE],
    assignment: u16,
    target_index: usize,
    target_role: ResourceRoleV1,
) -> Option<u32> {
    let target_id = resources.get(target_index)?.resource_id();
    resources
        .iter()
        .enumerate()
        .filter(|(index, resource)| {
            expected_role(assignment_digit(assignment, *index)) == Some(target_role)
                && resource.resource_id() < target_id
        })
        .count()
        .try_into()
        .ok()
}

fn assigned_ids(
    resources: &[IntrinsicResourceV1; UNIVERSE_SIZE],
    assignment: u16,
    role: ResourceRoleV1,
) -> Vec<ResourceId> {
    resources
        .iter()
        .enumerate()
        .filter_map(|(index, resource)| {
            (expected_role(assignment_digit(assignment, index)) == Some(role))
                .then_some(resource.resource_id())
        })
        .rev()
        .collect()
}

#[test]
fn every_small_assignment_matches_independent_binding_oracle() -> Result<(), AtlasError> {
    let resources = [resource(21)?, resource(22)?, resource(23)?, resource(24)?];
    let outsider = resource(99)?;
    for assignment in 0..ASSIGNMENT_COUNT {
        let consumed = assigned_ids(&resources, assignment, ResourceRoleV1::Consumed);
        let referenced = assigned_ids(&resources, assignment, ResourceRoleV1::Referenced);
        let created = assigned_ids(&resources, assignment, ResourceRoleV1::Created);
        let roles = CanonicalResourceRolesV1::try_new(
            ResourceRoleListsCandidateV1 {
                consumed: &consumed,
                referenced: &referenced,
                created: &created,
            },
            PolicyLimitsV1::strict_default(),
        )?;

        for (target_index, target) in resources.iter().enumerate() {
            let actual = roles.bind_intrinsic(target);
            if let Some(role) = expected_role(assignment_digit(assignment, target_index)) {
                let bound = actual.map_err(|_| AtlasError::Binding)?;
                assert_eq!(bound.resource_id(), target.resource_id());
                assert_eq!(bound.role(), role);
                assert_eq!(
                    Some(bound.ordinal()),
                    expected_ordinal(&resources, assignment, target_index, role)
                );
            } else {
                assert_eq!(
                    actual,
                    Err(IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles)
                );
            }
        }
        assert_eq!(
            roles.bind_intrinsic(&outsider),
            Err(IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles)
        );
    }
    Ok(())
}
