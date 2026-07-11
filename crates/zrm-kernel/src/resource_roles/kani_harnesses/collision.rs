//! Collision precedence over one symbolic identifier per role.

use super::{
    CanonicalResourceRolesV1, PolicyLimitsV1, ResourceId, ResourceRoleListsCandidateV1,
    ResourceRolePartitionErrorV1, ResourceRoleV1, symbolic_resource_id,
};

fn collision_oracle(
    consumed: ResourceId,
    referenced: ResourceId,
    created: ResourceId,
) -> Result<(), ResourceRolePartitionErrorV1> {
    if consumed == referenced {
        return Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Referenced,
        });
    }
    if consumed == created {
        return Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Created,
        });
    }
    if referenced == created {
        return Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Referenced,
            second_role: ResourceRoleV1::Created,
        });
    }
    Ok(())
}

fn assert_success(
    roles: &CanonicalResourceRolesV1,
    consumed: ResourceId,
    referenced: ResourceId,
    created: ResourceId,
) {
    assert_eq!(roles.consumed(), &[consumed]);
    assert_eq!(roles.referenced(), &[referenced]);
    assert_eq!(roles.created(), &[created]);
    assert_eq!(roles.consumed_count(), 1);
    assert_eq!(roles.referenced_count(), 1);
    assert_eq!(roles.created_count(), 1);
}

#[kani::proof]
#[kani::unwind(40)]
fn one_per_role_matches_collision_precedence() {
    let Some(consumed) = symbolic_resource_id(3) else {
        return;
    };
    let Some(referenced) = symbolic_resource_id(3) else {
        return;
    };
    let Some(created) = symbolic_resource_id(3) else {
        return;
    };
    let actual = CanonicalResourceRolesV1::try_new(
        ResourceRoleListsCandidateV1 {
            consumed: &[consumed],
            referenced: &[referenced],
            created: &[created],
        },
        PolicyLimitsV1::strict_default(),
    );
    assert_eq!(
        actual.as_ref().map(|_| ()).map_err(|error| *error),
        collision_oracle(consumed, referenced, created)
    );
    if let Ok(roles) = &actual {
        assert_success(roles, consumed, referenced, created);
    }
    cover_outcomes(&actual);
}

fn cover_outcomes(actual: &Result<CanonicalResourceRolesV1, ResourceRolePartitionErrorV1>) {
    kani::cover!(actual.is_ok());
    kani::cover!(matches!(
        actual,
        Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Referenced
        })
    ));
    kani::cover!(matches!(
        actual,
        Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Created
        })
    ));
    kani::cover!(matches!(
        actual,
        Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Referenced,
            second_role: ResourceRoleV1::Created
        })
    ));
}
