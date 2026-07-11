//! Independent exhaustive reject-order oracle for CBC-003.

use zrm_kernel::{
    CanonicalResourceRolesV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRoleV1,
};
use zrm_policy::{PolicyLimitsV1, PolicyValidationErrorV1};
use zrm_types::{ResourceId, ZeroValueError};

#[derive(Debug)]
enum AtlasError {
    ZeroValue(ZeroValueError),
    Policy(PolicyValidationErrorV1),
    Partition(ResourceRolePartitionErrorV1),
}

impl From<ZeroValueError> for AtlasError {
    fn from(error: ZeroValueError) -> Self {
        Self::ZeroValue(error)
    }
}

impl From<PolicyValidationErrorV1> for AtlasError {
    fn from(error: PolicyValidationErrorV1) -> Self {
        Self::Policy(error)
    }
}

impl From<ResourceRolePartitionErrorV1> for AtlasError {
    fn from(error: ResourceRolePartitionErrorV1) -> Self {
        Self::Partition(error)
    }
}

impl core::fmt::Display for AtlasError {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::ZeroValue(error) => write!(formatter, "invalid identifier fixture: {error}"),
            Self::Policy(error) => write!(formatter, "invalid limit fixture: {error}"),
            Self::Partition(error) => write!(formatter, "unexpected partition reject: {error:?}"),
        }
    }
}

impl std::error::Error for AtlasError {}

type AtlasResult = Result<(), AtlasError>;

fn resource_id(value: u16) -> Result<ResourceId, ZeroValueError> {
    let [high, low] = value.to_be_bytes();
    ResourceId::try_from([
        high, low, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0,
    ])
}

fn resource_ids(first: u16, count: u16) -> Result<Vec<ResourceId>, ZeroValueError> {
    std::iter::successors(Some(first), |value| value.checked_add(1))
        .take(usize::from(count))
        .map(resource_id)
        .collect()
}

fn limits(maximum: u16) -> Result<PolicyLimitsV1, PolicyValidationErrorV1> {
    let mut candidate = PolicyLimitsV1::strict_default().as_candidate();
    candidate.max_consumed_resources = maximum;
    candidate.max_referenced_resources = maximum;
    candidate.max_created_resources = maximum;
    PolicyLimitsV1::try_from(candidate)
}

fn sequences(a: ResourceId, b: ResourceId) -> [Vec<ResourceId>; 8] {
    [
        vec![],
        vec![a],
        vec![b],
        vec![a, a],
        vec![a, b],
        vec![b, a],
        vec![b, b],
        vec![a, b, a],
    ]
}

fn has_duplicate(resources: &[ResourceId]) -> bool {
    resources.iter().any(|resource_id| {
        resources
            .iter()
            .filter(|candidate| *candidate == resource_id)
            .count()
            > 1
    })
}

fn intersects(first: &[ResourceId], second: &[ResourceId]) -> bool {
    first.iter().any(|resource_id| second.contains(resource_id))
}

fn exact_oracle(
    consumed: &[ResourceId],
    referenced: &[ResourceId],
    created: &[ResourceId],
    maximum: u16,
) -> Option<ResourceRolePartitionErrorV1> {
    if consumed.len() > usize::from(maximum) {
        return Some(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Consumed,
            maximum,
        });
    }
    if referenced.len() > usize::from(maximum) {
        return Some(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Referenced,
            maximum,
        });
    }
    if created.len() > usize::from(maximum) {
        return Some(ResourceRolePartitionErrorV1::CountLimitExceeded {
            role: ResourceRoleV1::Created,
            maximum,
        });
    }
    if has_duplicate(consumed) {
        return Some(ResourceRolePartitionErrorV1::DuplicateResourceId {
            role: ResourceRoleV1::Consumed,
        });
    }
    if has_duplicate(referenced) {
        return Some(ResourceRolePartitionErrorV1::DuplicateResourceId {
            role: ResourceRoleV1::Referenced,
        });
    }
    if has_duplicate(created) {
        return Some(ResourceRolePartitionErrorV1::DuplicateResourceId {
            role: ResourceRoleV1::Created,
        });
    }
    if intersects(consumed, referenced) {
        return Some(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Referenced,
        });
    }
    if intersects(consumed, created) {
        return Some(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Created,
        });
    }
    if intersects(referenced, created) {
        return Some(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Referenced,
            second_role: ResourceRoleV1::Created,
        });
    }
    None
}

fn assert_sequence_atlas(maximum: u16) -> AtlasResult {
    let a = resource_id(1)?;
    let b = resource_id(2)?;
    let sequences = sequences(a, b);
    let limits = limits(maximum)?;
    for consumed in &sequences {
        for referenced in &sequences {
            for created in &sequences {
                let expected = exact_oracle(consumed, referenced, created, maximum);
                let actual = CanonicalResourceRolesV1::try_new(
                    ResourceRoleListsCandidateV1 {
                        consumed,
                        referenced,
                        created,
                    },
                    limits,
                )
                .err();
                assert_eq!(actual, expected);
            }
        }
    }
    Ok(())
}

fn candidate_for_role(
    role: ResourceRoleV1,
    resources: &[ResourceId],
) -> ResourceRoleListsCandidateV1<'_> {
    match role {
        ResourceRoleV1::Consumed => ResourceRoleListsCandidateV1 {
            consumed: resources,
            referenced: &[],
            created: &[],
        },
        ResourceRoleV1::Referenced => ResourceRoleListsCandidateV1 {
            consumed: &[],
            referenced: resources,
            created: &[],
        },
        ResourceRoleV1::Created => ResourceRoleListsCandidateV1 {
            consumed: &[],
            referenced: &[],
            created: resources,
        },
    }
}

fn role_count(roles: &CanonicalResourceRolesV1, role: ResourceRoleV1) -> u16 {
    match role {
        ResourceRoleV1::Consumed => roles.consumed_count(),
        ResourceRoleV1::Referenced => roles.referenced_count(),
        ResourceRoleV1::Created => roles.created_count(),
    }
}

fn assert_terminal_position(
    roles: &CanonicalResourceRolesV1,
    resource_id: ResourceId,
    role: ResourceRoleV1,
) {
    assert_eq!(
        roles.position_of(&resource_id).map(|position| (
            position.resource_id(),
            position.role(),
            position.ordinal(),
        )),
        Some((resource_id, role, 255))
    );
}

#[test]
fn exhaustive_sequence_atlas_matches_exact_count_first_precedence() -> AtlasResult {
    assert_sequence_atlas(1)
}

#[test]
fn exhaustive_sequence_atlas_matches_exact_duplicate_and_collision_precedence() -> AtlasResult {
    assert_sequence_atlas(3)
}

#[test]
fn each_role_accepts_protocol_ceiling_and_rejects_ceiling_plus_one() -> AtlasResult {
    let maximum = PolicyLimitsV1::MAX_CONSUMED_RESOURCES;
    let unique = resource_ids(1, maximum)?;
    let repeated: Vec<ResourceId> = std::iter::repeat_n(resource_id(1)?, 257).collect();
    let limits = PolicyLimitsV1::protocol_ceiling();
    let roles = [
        ResourceRoleV1::Consumed,
        ResourceRoleV1::Referenced,
        ResourceRoleV1::Created,
    ];
    for role in roles {
        let accepted = CanonicalResourceRolesV1::try_new(candidate_for_role(role, &unique), limits);
        assert_eq!(
            accepted.as_ref().map(|value| role_count(value, role)),
            Ok(maximum)
        );
        let rejected =
            CanonicalResourceRolesV1::try_new(candidate_for_role(role, &repeated), limits);
        assert_eq!(
            rejected.err(),
            Some(ResourceRolePartitionErrorV1::CountLimitExceeded { role, maximum })
        );
    }
    Ok(())
}

#[test]
fn accepts_all_three_disjoint_roles_at_simultaneous_protocol_ceiling() -> AtlasResult {
    let consumed = resource_ids(1, 256)?;
    let referenced = resource_ids(257, 256)?;
    let created = resource_ids(513, 256)?;
    let roles = CanonicalResourceRolesV1::try_new(
        ResourceRoleListsCandidateV1 {
            consumed: &consumed,
            referenced: &referenced,
            created: &created,
        },
        PolicyLimitsV1::protocol_ceiling(),
    )?;
    assert_eq!(roles.consumed_count(), 256);
    assert_eq!(roles.referenced_count(), 256);
    assert_eq!(roles.created_count(), 256);
    assert_terminal_position(&roles, resource_id(256)?, ResourceRoleV1::Consumed);
    assert_terminal_position(&roles, resource_id(512)?, ResourceRoleV1::Referenced);
    assert_terminal_position(&roles, resource_id(768)?, ResourceRoleV1::Created);
    Ok(())
}
