#![no_main]

use libfuzzer_sys::fuzz_target;
use zrm_kernel::{
    CanonicalResourceRolesV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRoleV1,
};
use zrm_policy::{PolicyLimitsCandidateV1, PolicyLimitsV1};
use zrm_types::ResourceId;

const HEADER_BYTES: usize = 12;
const RESOURCE_ID_BYTES: usize = 32;
const MAX_ROLE_INPUTS: usize = 257;

struct ResourceRolesFuzzInput {
    limits: PolicyLimitsV1,
    consumed: Vec<ResourceId>,
    referenced: Vec<ResourceId>,
    created: Vec<ResourceId>,
}

impl ResourceRolesFuzzInput {
    fn candidate(&self) -> ResourceRoleListsCandidateV1<'_> {
        ResourceRoleListsCandidateV1 {
            consumed: &self.consumed,
            referenced: &self.referenced,
            created: &self.created,
        }
    }
}

fn read_u16(data: &[u8], offset: usize) -> Option<u16> {
    let end = offset.checked_add(2)?;
    let bytes: [u8; 2] = data.get(offset..end)?.try_into().ok()?;
    Some(u16::from_be_bytes(bytes))
}

fn take_prefix<'a>(remaining: &mut &'a [u8], length: usize) -> Option<&'a [u8]> {
    let prefix = remaining.get(..length)?;
    let suffix = remaining.get(length..)?;
    *remaining = suffix;
    Some(prefix)
}

fn parse_ids(remaining: &mut &[u8], count: usize) -> Option<Vec<ResourceId>> {
    let byte_length = count.checked_mul(RESOURCE_ID_BYTES)?;
    let bytes = take_prefix(remaining, byte_length)?;
    let mut identifiers = Vec::new();
    identifiers.try_reserve_exact(count).ok()?;
    for chunk in bytes.chunks_exact(RESOURCE_ID_BYTES) {
        let candidate: [u8; RESOURCE_ID_BYTES] = chunk.try_into().ok()?;
        identifiers.push(ResourceId::try_from(candidate).ok()?);
    }
    Some(identifiers)
}

fn parse_input(data: &[u8]) -> Option<ResourceRolesFuzzInput> {
    // Arbitrary u16 limit mutations usually exceed the v1 policy ceilings.
    // The committed structured corpus anchors zero, exact-limit, and
    // over-limit profiles so mutations continue to reach semantic branches.
    let consumed_limit = read_u16(data, 0)?;
    let referenced_limit = read_u16(data, 2)?;
    let created_limit = read_u16(data, 4)?;
    let consumed_count = usize::from(read_u16(data, 6)?);
    let referenced_count = usize::from(read_u16(data, 8)?);
    let created_count = usize::from(read_u16(data, 10)?);
    let counts = [consumed_count, referenced_count, created_count];
    if counts.into_iter().any(|count| count > MAX_ROLE_INPUTS) {
        return None;
    }

    let total_count = counts
        .iter()
        .try_fold(0_usize, |total, count| total.checked_add(*count))?;
    let payload_bytes = total_count.checked_mul(RESOURCE_ID_BYTES)?;
    if data.len() != HEADER_BYTES.checked_add(payload_bytes)? {
        return None;
    }

    let mut limits_candidate: PolicyLimitsCandidateV1 =
        PolicyLimitsV1::strict_default().as_candidate();
    limits_candidate.max_consumed_resources = consumed_limit;
    limits_candidate.max_referenced_resources = referenced_limit;
    limits_candidate.max_created_resources = created_limit;
    let limits = PolicyLimitsV1::try_from(limits_candidate).ok()?;

    let mut remaining = data.get(HEADER_BYTES..)?;
    let consumed = parse_ids(&mut remaining, consumed_count)?;
    let referenced = parse_ids(&mut remaining, referenced_count)?;
    let created = parse_ids(&mut remaining, created_count)?;
    if !remaining.is_empty() {
        return None;
    }
    Some(ResourceRolesFuzzInput {
        limits,
        consumed,
        referenced,
        created,
    })
}

fn first_count_error(input: &ResourceRolesFuzzInput) -> Option<ResourceRolePartitionErrorV1> {
    let role_counts = [
        (
            ResourceRoleV1::Consumed,
            input.consumed.len(),
            input.limits.max_consumed_resources(),
        ),
        (
            ResourceRoleV1::Referenced,
            input.referenced.len(),
            input.limits.max_referenced_resources(),
        ),
        (
            ResourceRoleV1::Created,
            input.created.len(),
            input.limits.max_created_resources(),
        ),
    ];
    role_counts
        .into_iter()
        .find(|(_, actual, maximum)| *actual > usize::from(*maximum))
        .map(
            |(role, _, maximum)| ResourceRolePartitionErrorV1::CountLimitExceeded { role, maximum },
        )
}

fn has_unsorted_duplicate(resources: &[ResourceId]) -> bool {
    resources.iter().enumerate().any(|(position, resource_id)| {
        resources
            .iter()
            .skip(position.saturating_add(1))
            .any(|candidate| candidate == resource_id)
    })
}

fn first_duplicate_error(input: &ResourceRolesFuzzInput) -> Option<ResourceRolePartitionErrorV1> {
    let roles = [
        (ResourceRoleV1::Consumed, input.consumed.as_slice()),
        (ResourceRoleV1::Referenced, input.referenced.as_slice()),
        (ResourceRoleV1::Created, input.created.as_slice()),
    ];
    roles
        .into_iter()
        .find(|(_, resources)| has_unsorted_duplicate(resources))
        .map(|(role, _)| ResourceRolePartitionErrorV1::DuplicateResourceId { role })
}

fn has_unsorted_collision(first: &[ResourceId], second: &[ResourceId]) -> bool {
    first
        .iter()
        .any(|resource_id| second.iter().any(|candidate| candidate == resource_id))
}

fn first_collision_error(input: &ResourceRolesFuzzInput) -> Option<ResourceRolePartitionErrorV1> {
    let role_pairs = [
        (
            ResourceRoleV1::Consumed,
            input.consumed.as_slice(),
            ResourceRoleV1::Referenced,
            input.referenced.as_slice(),
        ),
        (
            ResourceRoleV1::Consumed,
            input.consumed.as_slice(),
            ResourceRoleV1::Created,
            input.created.as_slice(),
        ),
        (
            ResourceRoleV1::Referenced,
            input.referenced.as_slice(),
            ResourceRoleV1::Created,
            input.created.as_slice(),
        ),
    ];
    role_pairs
        .into_iter()
        .find(|(_, first, _, second)| has_unsorted_collision(first, second))
        .map(|(first_role, _, second_role, _)| {
            ResourceRolePartitionErrorV1::ResourceRoleCollision {
                first_role,
                second_role,
            }
        })
}

fn expected_partition_result(
    input: &ResourceRolesFuzzInput,
) -> Result<(), ResourceRolePartitionErrorV1> {
    first_count_error(input)
        .or_else(|| first_duplicate_error(input))
        .or_else(|| first_collision_error(input))
        .map_or(Ok(()), Err)
}

fn assert_role_properties(
    roles: &CanonicalResourceRolesV1,
    role: ResourceRoleV1,
    resources: &[ResourceId],
    count: u16,
) {
    assert_eq!(resources.len(), usize::from(count));
    assert!(resources.is_sorted());
    assert!(resources.windows(2).all(|window| {
        let [first, second] = window else {
            return false;
        };
        first != second
    }));
    for (resource_id, ordinal) in resources.iter().zip(0_u32..) {
        assert_eq!(
            roles.position_of(resource_id).map(|position| (
                position.resource_id(),
                position.role(),
                position.ordinal(),
            )),
            Some((*resource_id, role, ordinal)),
        );
    }
}

fn assert_disjoint(first: &[ResourceId], second: &[ResourceId]) {
    assert!(
        first
            .iter()
            .all(|resource_id| second.binary_search(resource_id).is_err())
    );
}

fn assert_reversal_invariance(input: &ResourceRolesFuzzInput, expected: &CanonicalResourceRolesV1) {
    let mut consumed = input.consumed.clone();
    let mut referenced = input.referenced.clone();
    let mut created = input.created.clone();
    consumed.reverse();
    referenced.reverse();
    created.reverse();
    let reversed = CanonicalResourceRolesV1::try_new(
        ResourceRoleListsCandidateV1 {
            consumed: &consumed,
            referenced: &referenced,
            created: &created,
        },
        input.limits,
    );
    assert_eq!(reversed.as_ref(), Ok(expected));
}

fn rotate_if_nontrivial(resources: &mut [ResourceId]) {
    if resources.len() > 1 {
        resources.rotate_left(1);
    }
}

fn assert_permutation_invariance(
    input: &ResourceRolesFuzzInput,
    expected: &CanonicalResourceRolesV1,
) {
    let mut consumed = input.consumed.clone();
    let mut referenced = input.referenced.clone();
    let mut created = input.created.clone();
    rotate_if_nontrivial(&mut consumed);
    rotate_if_nontrivial(&mut referenced);
    rotate_if_nontrivial(&mut created);
    let permuted = CanonicalResourceRolesV1::try_new(
        ResourceRoleListsCandidateV1 {
            consumed: &consumed,
            referenced: &referenced,
            created: &created,
        },
        input.limits,
    );
    assert_eq!(permuted.as_ref(), Ok(expected));
}

fn assert_success_properties(input: &ResourceRolesFuzzInput, roles: &CanonicalResourceRolesV1) {
    assert_role_properties(
        roles,
        ResourceRoleV1::Consumed,
        roles.consumed(),
        roles.consumed_count(),
    );
    assert_role_properties(
        roles,
        ResourceRoleV1::Referenced,
        roles.referenced(),
        roles.referenced_count(),
    );
    assert_role_properties(
        roles,
        ResourceRoleV1::Created,
        roles.created(),
        roles.created_count(),
    );
    assert_disjoint(roles.consumed(), roles.referenced());
    assert_disjoint(roles.consumed(), roles.created());
    assert_disjoint(roles.referenced(), roles.created());
    assert_reversal_invariance(input, roles);
    assert_permutation_invariance(input, roles);
}

fuzz_target!(|data: &[u8]| {
    let Some(input) = parse_input(data) else {
        return;
    };
    let first = CanonicalResourceRolesV1::try_new(input.candidate(), input.limits);
    let replay = CanonicalResourceRolesV1::try_new(input.candidate(), input.limits);
    assert_eq!(first, replay);
    let actual_partition_result = first.as_ref().map(|_| ()).map_err(|error| *error);
    assert_eq!(actual_partition_result, expected_partition_result(&input));
    if let Ok(roles) = first {
        assert_success_properties(&input, &roles);
    }
});
