//! Public CBC-003 resource-role partition regression tests.

use zrm_kernel::{
    CanonicalResourceRolesV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRoleV1,
};
use zrm_policy::{PolicyLimitsCandidateV1, PolicyLimitsV1, PolicyValidationErrorV1};
use zrm_types::{ResourceId, ZeroValueError};

#[derive(Debug)]
enum ResourceRoleTestError {
    ZeroValue(ZeroValueError),
    Policy(PolicyValidationErrorV1),
    Partition(ResourceRolePartitionErrorV1),
    MissingPosition(ResourceRoleV1),
}

impl From<ZeroValueError> for ResourceRoleTestError {
    fn from(error: ZeroValueError) -> Self {
        Self::ZeroValue(error)
    }
}

impl From<PolicyValidationErrorV1> for ResourceRoleTestError {
    fn from(error: PolicyValidationErrorV1) -> Self {
        Self::Policy(error)
    }
}

impl From<ResourceRolePartitionErrorV1> for ResourceRoleTestError {
    fn from(error: ResourceRolePartitionErrorV1) -> Self {
        Self::Partition(error)
    }
}

impl core::fmt::Display for ResourceRoleTestError {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::ZeroValue(error) => write!(formatter, "invalid identifier fixture: {error}"),
            Self::Policy(error) => write!(formatter, "invalid limit fixture: {error}"),
            Self::Partition(error) => write!(formatter, "unexpected partition reject: {error:?}"),
            Self::MissingPosition(role) => write!(formatter, "missing {role:?} test position"),
        }
    }
}

impl std::error::Error for ResourceRoleTestError {}

type TestResult = Result<(), ResourceRoleTestError>;

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

fn limits_with_counts(
    consumed: u16,
    referenced: u16,
    created: u16,
) -> Result<PolicyLimitsV1, PolicyValidationErrorV1> {
    let mut candidate: PolicyLimitsCandidateV1 = PolicyLimitsV1::strict_default().as_candidate();
    candidate.max_consumed_resources = consumed;
    candidate.max_referenced_resources = referenced;
    candidate.max_created_resources = created;
    PolicyLimitsV1::try_from(candidate)
}

fn candidate<'a>(
    consumed: &'a [ResourceId],
    referenced: &'a [ResourceId],
    created: &'a [ResourceId],
) -> ResourceRoleListsCandidateV1<'a> {
    ResourceRoleListsCandidateV1 {
        consumed,
        referenced,
        created,
    }
}

fn assert_count_error(
    result: &Result<CanonicalResourceRolesV1, ResourceRolePartitionErrorV1>,
    role: ResourceRoleV1,
    maximum: u16,
) {
    assert_eq!(
        result,
        &Err(ResourceRolePartitionErrorV1::CountLimitExceeded { role, maximum })
    );
}

#[test]
fn accepts_empty_roles_under_zero_limits() -> TestResult {
    let roles =
        CanonicalResourceRolesV1::try_new(candidate(&[], &[], &[]), limits_with_counts(0, 0, 0)?)?;
    assert!(roles.consumed().is_empty());
    assert!(roles.referenced().is_empty());
    assert!(roles.created().is_empty());
    assert_eq!(roles.consumed_count(), 0);
    assert_eq!(roles.referenced_count(), 0);
    assert_eq!(roles.created_count(), 0);
    Ok(())
}

#[test]
fn every_role_accepts_its_limit_and_rejects_limit_plus_one() -> TestResult {
    let consumed = resource_ids(1, 2)?;
    let referenced = resource_ids(10, 2)?;
    let created = resource_ids(20, 2)?;
    let over_consumed = resource_ids(1, 3)?;
    let over_referenced = resource_ids(10, 3)?;
    let over_created = resource_ids(20, 3)?;
    let limits = limits_with_counts(2, 2, 2)?;

    let roles =
        CanonicalResourceRolesV1::try_new(candidate(&consumed, &referenced, &created), limits)?;
    assert_eq!(roles.consumed_count(), 2);
    assert_eq!(roles.referenced_count(), 2);
    assert_eq!(roles.created_count(), 2);

    assert_count_error(
        &CanonicalResourceRolesV1::try_new(candidate(&over_consumed, &[], &[]), limits),
        ResourceRoleV1::Consumed,
        2,
    );
    assert_count_error(
        &CanonicalResourceRolesV1::try_new(candidate(&[], &over_referenced, &[]), limits),
        ResourceRoleV1::Referenced,
        2,
    );
    assert_count_error(
        &CanonicalResourceRolesV1::try_new(candidate(&[], &[], &over_created), limits),
        ResourceRoleV1::Created,
        2,
    );
    Ok(())
}

#[test]
fn count_reject_precedence_is_consumed_then_referenced_then_created() -> TestResult {
    let over = resource_ids(1, 2)?;
    let limits = limits_with_counts(1, 1, 1)?;
    assert_count_error(
        &CanonicalResourceRolesV1::try_new(candidate(&over, &over, &over), limits),
        ResourceRoleV1::Consumed,
        1,
    );
    assert_count_error(
        &CanonicalResourceRolesV1::try_new(candidate(&[], &over, &over), limits),
        ResourceRoleV1::Referenced,
        1,
    );
    assert_count_error(
        &CanonicalResourceRolesV1::try_new(candidate(&[], &[], &over), limits),
        ResourceRoleV1::Created,
        1,
    );
    Ok(())
}

#[test]
fn duplicate_reject_precedence_is_consumed_then_referenced_then_created() -> TestResult {
    let one = resource_id(1)?;
    let two = resource_id(2)?;
    let three = resource_id(3)?;
    let consumed = [one, one];
    let referenced = [two, two];
    let created = [three, three];
    let limits = limits_with_counts(2, 2, 2)?;

    assert_eq!(
        CanonicalResourceRolesV1::try_new(candidate(&consumed, &referenced, &created), limits),
        Err(ResourceRolePartitionErrorV1::DuplicateResourceId {
            role: ResourceRoleV1::Consumed,
        })
    );
    assert_eq!(
        CanonicalResourceRolesV1::try_new(candidate(&[], &referenced, &created), limits),
        Err(ResourceRolePartitionErrorV1::DuplicateResourceId {
            role: ResourceRoleV1::Referenced,
        })
    );
    assert_eq!(
        CanonicalResourceRolesV1::try_new(candidate(&[], &[], &created), limits),
        Err(ResourceRolePartitionErrorV1::DuplicateResourceId {
            role: ResourceRoleV1::Created,
        })
    );
    Ok(())
}

#[test]
fn collision_reject_precedence_is_consumed_referenced_then_consumed_created_then_referenced_created()
-> TestResult {
    let one = resource_id(1)?;
    let two = resource_id(2)?;
    let limits = limits_with_counts(2, 2, 2)?;
    assert_eq!(
        CanonicalResourceRolesV1::try_new(candidate(&[one], &[one], &[one]), limits),
        Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Referenced,
        })
    );
    assert_eq!(
        CanonicalResourceRolesV1::try_new(candidate(&[one], &[two], &[one, two]), limits),
        Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Consumed,
            second_role: ResourceRoleV1::Created,
        })
    );
    assert_eq!(
        CanonicalResourceRolesV1::try_new(candidate(&[one], &[two], &[two]), limits),
        Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
            first_role: ResourceRoleV1::Referenced,
            second_role: ResourceRoleV1::Created,
        })
    );
    Ok(())
}

#[test]
fn duplicates_precede_cross_role_collisions() -> TestResult {
    let one = resource_id(1)?;
    let duplicated = [one, one];
    assert_eq!(
        CanonicalResourceRolesV1::try_new(
            candidate(&duplicated, &[one], &[one]),
            limits_with_counts(2, 2, 2)?,
        ),
        Err(ResourceRolePartitionErrorV1::DuplicateResourceId {
            role: ResourceRoleV1::Consumed,
        })
    );
    Ok(())
}

#[test]
fn canonicalizes_each_role_without_mutating_inputs() -> TestResult {
    let one = resource_id(1)?;
    let two = resource_id(2)?;
    let three = resource_id(3)?;
    let four = resource_id(4)?;
    let five = resource_id(5)?;
    let six = resource_id(6)?;
    let consumed = [three, one, two];
    let referenced = [five, four];
    let created = [six];
    let original_consumed = consumed;
    let original_referenced = referenced;
    let original_created = created;

    let roles = CanonicalResourceRolesV1::try_new(
        candidate(&consumed, &referenced, &created),
        limits_with_counts(3, 2, 1)?,
    )?;
    assert_eq!(roles.consumed(), &[one, two, three]);
    assert_eq!(roles.referenced(), &[four, five]);
    assert_eq!(roles.created(), &[six]);
    assert_eq!(consumed, original_consumed);
    assert_eq!(referenced, original_referenced);
    assert_eq!(created, original_created);
    Ok(())
}

#[test]
fn lookup_returns_exact_resource_role_and_zero_based_ordinal() -> TestResult {
    let one = resource_id(1)?;
    let two = resource_id(2)?;
    let three = resource_id(3)?;
    let four = resource_id(4)?;
    let absent = resource_id(99)?;
    let roles = CanonicalResourceRolesV1::try_new(
        candidate(&[two, one], &[three], &[four]),
        limits_with_counts(2, 1, 1)?,
    )?;

    let first = roles
        .position_of(&one)
        .ok_or(ResourceRoleTestError::MissingPosition(
            ResourceRoleV1::Consumed,
        ))?;
    assert_eq!(first.resource_id(), one);
    assert_eq!(first.role(), ResourceRoleV1::Consumed);
    assert_eq!(first.ordinal(), 0);

    let second = roles
        .position_of(&two)
        .ok_or(ResourceRoleTestError::MissingPosition(
            ResourceRoleV1::Consumed,
        ))?;
    assert_eq!(second.resource_id(), two);
    assert_eq!(second.role(), ResourceRoleV1::Consumed);
    assert_eq!(second.ordinal(), 1);

    let referenced = roles
        .position_of(&three)
        .ok_or(ResourceRoleTestError::MissingPosition(
            ResourceRoleV1::Referenced,
        ))?;
    assert_eq!(referenced.ordinal(), 0);
    let created = roles
        .position_of(&four)
        .ok_or(ResourceRoleTestError::MissingPosition(
            ResourceRoleV1::Created,
        ))?;
    assert_eq!(created.ordinal(), 0);
    assert_eq!(roles.position_of(&absent), None);
    Ok(())
}

#[test]
fn canonical_result_is_invariant_under_role_local_permutations() -> TestResult {
    let one = resource_id(1)?;
    let two = resource_id(2)?;
    let three = resource_id(3)?;
    let four = resource_id(4)?;
    let five = resource_id(5)?;
    let six = resource_id(6)?;
    let limits = limits_with_counts(3, 2, 1)?;
    let expected = CanonicalResourceRolesV1::try_new(
        candidate(&[one, two, three], &[four, five], &[six]),
        limits,
    )?;
    let permutations = [
        [one, two, three],
        [one, three, two],
        [two, one, three],
        [two, three, one],
        [three, one, two],
        [three, two, one],
    ];
    for consumed in permutations {
        let actual =
            CanonicalResourceRolesV1::try_new(candidate(&consumed, &[five, four], &[six]), limits)?;
        assert_eq!(actual, expected);
    }
    Ok(())
}

fn ids_for_mask(mask: u8, universe: &[ResourceId; 3]) -> Vec<ResourceId> {
    universe
        .iter()
        .enumerate()
        .filter_map(|(bit, resource_id)| {
            let shift = u32::try_from(bit).ok()?;
            (mask & (1_u8 << shift) != 0).then_some(*resource_id)
        })
        .rev()
        .collect()
}

#[test]
fn exhaustive_small_universe_matches_independent_set_partition_oracle() -> TestResult {
    let universe = [resource_id(1)?, resource_id(2)?, resource_id(3)?];
    let limits = limits_with_counts(3, 3, 3)?;
    for consumed_mask in 0_u8..8 {
        for referenced_mask in 0_u8..8 {
            for created_mask in 0_u8..8 {
                let consumed = ids_for_mask(consumed_mask, &universe);
                let referenced = ids_for_mask(referenced_mask, &universe);
                let created = ids_for_mask(created_mask, &universe);
                let expected_accept = consumed_mask & referenced_mask == 0
                    && consumed_mask & created_mask == 0
                    && referenced_mask & created_mask == 0;
                let actual = CanonicalResourceRolesV1::try_new(
                    candidate(&consumed, &referenced, &created),
                    limits,
                );
                assert_eq!(actual.is_ok(), expected_accept);
                if let Ok(roles) = actual {
                    assert!(roles.consumed().is_sorted());
                    assert!(roles.referenced().is_sorted());
                    assert!(roles.created().is_sorted());
                }
            }
        }
    }
    Ok(())
}
