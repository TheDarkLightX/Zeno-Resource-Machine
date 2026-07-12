//! Count-bound precedence over disjoint singleton role lists.

use super::{
    CanonicalResourceRolesV1, PolicyLimitsV1, ResourceId, ResourceRoleListsCandidateV1,
    ResourceRolePartitionErrorV1, ResourceRoleV1, symbolic_resource_id,
};

type OnePerRole = ([ResourceId; 1], [ResourceId; 1], [ResourceId; 1]);
type RoleCountLimits = (u16, u16, u16);

fn symbolic_disjoint_one_per_role() -> Option<OnePerRole> {
    let consumed_id = symbolic_resource_id(3)?;
    let referenced_id = symbolic_resource_id(3)?;
    let created_id = symbolic_resource_id(3)?;
    kani::assume(consumed_id != referenced_id);
    kani::assume(consumed_id != created_id);
    kani::assume(referenced_id != created_id);
    Some(([consumed_id], [referenced_id], [created_id]))
}

fn symbolic_count_limits() -> RoleCountLimits {
    let consumed: u16 = kani::any();
    let referenced: u16 = kani::any();
    let created: u16 = kani::any();
    kani::assume(consumed <= 1);
    kani::assume(referenced <= 1);
    kani::assume(created <= 1);
    (consumed, referenced, created)
}

fn limits_with_counts(counts: RoleCountLimits) -> Option<PolicyLimitsV1> {
    let mut candidate = PolicyLimitsV1::strict_default().as_candidate();
    candidate.max_consumed_resources = counts.0;
    candidate.max_referenced_resources = counts.1;
    candidate.max_created_resources = counts.2;
    PolicyLimitsV1::try_from(candidate).ok()
}

#[kani::proof]
#[kani::unwind(40)]
fn one_per_role_matches_count_precedence() {
    let Some((consumed, referenced, created)) = symbolic_disjoint_one_per_role() else {
        return;
    };
    let counts = symbolic_count_limits();
    let Some(limits) = limits_with_counts(counts) else {
        return;
    };
    let actual = CanonicalResourceRolesV1::try_new(
        ResourceRoleListsCandidateV1 {
            consumed: &consumed,
            referenced: &referenced,
            created: &created,
        },
        limits,
    );
    assert_eq!(
        actual.as_ref().map(|_| ()).map_err(|error| *error),
        count_oracle(counts.0, counts.1, counts.2)
    );
    kani::cover!(actual.is_ok());
    cover_outcomes(&actual);
}

fn cover_outcomes(actual: &Result<CanonicalResourceRolesV1, ResourceRolePartitionErrorV1>) {
    kani::cover!(matches!(
        actual,
        Err(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Consumed,
            ..
        })
    ));
    kani::cover!(matches!(
        actual,
        Err(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Referenced,
            ..
        })
    ));
    kani::cover!(matches!(
        actual,
        Err(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Created,
            ..
        })
    ));
}

fn count_oracle(
    consumed_limit: u16,
    referenced_limit: u16,
    created_limit: u16,
) -> Result<(), ResourceRolePartitionErrorV1> {
    if consumed_limit == 0 {
        return Err(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Consumed,
            maximum: 0,
        });
    }
    if referenced_limit == 0 {
        return Err(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Referenced,
            maximum: 0,
        });
    }
    if created_limit == 0 {
        return Err(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Created,
            maximum: 0,
        });
    }
    Ok(())
}
