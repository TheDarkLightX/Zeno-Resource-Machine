//! Bounded canonical partitioning of inert resource identifiers.

use alloc::vec::Vec;

use zrm_policy::PolicyLimitsV1;
use zrm_types::ResourceId;

/// One structural role assigned to a resource identifier.
///
/// This enum has no canonical wire representation in `WP3a`. It identifies an
/// in-memory role only and grants no resource or transition authority.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ResourceRoleV1 {
    /// The transition proposes to consume the resource.
    Consumed,
    /// The transition proposes to read the resource without consuming it.
    Referenced,
    /// The transition proposes to create the resource.
    Created,
}

/// Borrowed, non-authoritative resource-role list candidates.
///
/// Input order, duplication, and cross-role relationships are untrusted. The
/// constructor reads these slices without changing them.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ResourceRoleListsCandidateV1<'a> {
    /// Resource identifiers proposed for the consumed role.
    pub consumed: &'a [ResourceId],
    /// Resource identifiers proposed for the referenced role.
    pub referenced: &'a [ResourceId],
    /// Resource identifiers proposed for the created role.
    pub created: &'a [ResourceId],
}

/// Noncanonical failure from resource-role partitioning.
///
/// This diagnostic type intentionally has no stable reject code or wire ABI.
/// It omits resource identifiers and platform-width counts. Structural error
/// precedence is deterministic; capacity availability depends on the host.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ResourceRolePartitionErrorV1 {
    /// A role count exceeds its validated policy limit.
    CountLimitExceeded {
        /// First over-limit role in consumed, referenced, created precedence.
        role: ResourceRoleV1,
        /// Validated policy limit for the role.
        maximum: u16,
    },
    /// Bounded storage could not be reserved for one role.
    CapacityUnavailable {
        /// Role whose fallible reservation failed.
        role: ResourceRoleV1,
    },
    /// A resource identifier occurs more than once within one role.
    DuplicateResourceId {
        /// First duplicate-bearing role in normative precedence.
        role: ResourceRoleV1,
    },
    /// A resource identifier occurs in two distinct roles.
    ResourceRoleCollision {
        /// Earlier role in normative pair precedence.
        first_role: ResourceRoleV1,
        /// Later role in normative pair precedence.
        second_role: ResourceRoleV1,
    },
}

/// Self-contained position of one identifier in a canonical role list.
///
/// Fields are derived only from a successfully constructed partition. The
/// value is structural and non-authoritative; later logic validation must bind
/// the role and ordinal through its own canonical statement.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ResourceRolePositionV1 {
    resource_id: ResourceId,
    role: ResourceRoleV1,
    ordinal: u32,
}

impl ResourceRolePositionV1 {
    /// Returns the exact resource identifier found in the partition.
    #[must_use]
    pub const fn resource_id(&self) -> ResourceId {
        self.resource_id
    }

    /// Returns the resource's structural role.
    #[must_use]
    pub const fn role(&self) -> ResourceRoleV1 {
        self.role
    }

    /// Returns the zero-based position within the canonical list for the role.
    #[must_use]
    pub const fn ordinal(&self) -> u32 {
        self.ordinal
    }
}

/// Policy-bounded, sorted, unique, pairwise-disjoint resource-role lists.
///
/// The fields are private so callers cannot manufacture structural validity.
/// This value remains inert: it authenticates no resource body, policy, state,
/// proof, transition, list root, or canonical bytes.
#[derive(Debug, Eq, PartialEq)]
pub struct CanonicalResourceRolesV1 {
    consumed: Vec<ResourceId>,
    referenced: Vec<ResourceId>,
    created: Vec<ResourceId>,
    consumed_count: u16,
    referenced_count: u16,
    created_count: u16,
}

impl CanonicalResourceRolesV1 {
    /// Validates bounds, partitions, copies, and sorts candidate role lists.
    ///
    /// All three counts are checked before any allocation. Storage reservation
    /// occurs only after duplicate and collision checks over the borrowed input.
    /// Reservation is fallible and bounded by the validated policy. Structural
    /// checks follow consumed, referenced, created role precedence.
    ///
    /// # Errors
    ///
    /// Returns the first count, within-role duplicate, or cross-role collision
    /// error in deterministic order. Structurally valid input can then return a
    /// role-local capacity error when the host cannot reserve bounded storage.
    ///
    /// # Complexity
    ///
    /// Time is `O(C^2 + R^2 + O^2)` and allocation is `O(C+R+O)`, where each
    /// count is at most 256 in v1. The bounded insertion sort keeps the
    /// comparison and movement path small and locally auditable.
    ///
    /// # Panics
    ///
    /// This function does not intentionally panic. Allocation failure is
    /// returned as `CapacityUnavailable` when reported by `try_reserve_exact`.
    pub fn try_new(
        candidate: ResourceRoleListsCandidateV1<'_>,
        limits: PolicyLimitsV1,
    ) -> Result<Self, ResourceRolePartitionErrorV1> {
        let counts = validate_count_bounds(candidate, limits)?;

        validate_duplicates(candidate.consumed, ResourceRoleV1::Consumed)?;
        validate_duplicates(candidate.referenced, ResourceRoleV1::Referenced)?;
        validate_duplicates(candidate.created, ResourceRoleV1::Created)?;
        validate_disjoint(
            candidate.consumed,
            candidate.referenced,
            ResourceRoleV1::Consumed,
            ResourceRoleV1::Referenced,
        )?;
        validate_disjoint(
            candidate.consumed,
            candidate.created,
            ResourceRoleV1::Consumed,
            ResourceRoleV1::Created,
        )?;
        validate_disjoint(
            candidate.referenced,
            candidate.created,
            ResourceRoleV1::Referenced,
            ResourceRoleV1::Created,
        )?;

        let consumed = copy_and_sort(ResourceRoleV1::Consumed, candidate.consumed)?;
        let referenced = copy_and_sort(ResourceRoleV1::Referenced, candidate.referenced)?;
        let created = copy_and_sort(ResourceRoleV1::Created, candidate.created)?;

        Ok(Self {
            consumed,
            referenced,
            created,
            consumed_count: counts.consumed,
            referenced_count: counts.referenced,
            created_count: counts.created,
        })
    }

    /// Returns consumed identifiers in ascending byte order.
    #[must_use]
    pub fn consumed(&self) -> &[ResourceId] {
        &self.consumed
    }

    /// Returns referenced identifiers in ascending byte order.
    #[must_use]
    pub fn referenced(&self) -> &[ResourceId] {
        &self.referenced
    }

    /// Returns created identifiers in ascending byte order.
    #[must_use]
    pub fn created(&self) -> &[ResourceId] {
        &self.created
    }

    /// Returns the consumed-resource count.
    #[must_use]
    pub const fn consumed_count(&self) -> u16 {
        self.consumed_count
    }

    /// Returns the referenced-resource count.
    #[must_use]
    pub const fn referenced_count(&self) -> u16 {
        self.referenced_count
    }

    /// Returns the created-resource count.
    #[must_use]
    pub const fn created_count(&self) -> u16 {
        self.created_count
    }

    /// Finds an identifier and returns its exact role and derived ordinal.
    ///
    /// The lookup performs at most three bounded linear scans and has no side
    /// effects. Absence returns `None`. Because role lists are disjoint, at most
    /// one result can exist.
    #[must_use]
    pub fn position_of(&self, resource_id: &ResourceId) -> Option<ResourceRolePositionV1> {
        position_in(ResourceRoleV1::Consumed, &self.consumed, resource_id)
            .or_else(|| position_in(ResourceRoleV1::Referenced, &self.referenced, resource_id))
            .or_else(|| position_in(ResourceRoleV1::Created, &self.created, resource_id))
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ResourceRoleCountsV1 {
    consumed: u16,
    referenced: u16,
    created: u16,
}

fn validate_count_bounds(
    candidate: ResourceRoleListsCandidateV1<'_>,
    limits: PolicyLimitsV1,
) -> Result<ResourceRoleCountsV1, ResourceRolePartitionErrorV1> {
    let consumed = validate_role_count(
        candidate.consumed.len(),
        ResourceRoleV1::Consumed,
        limits.max_consumed_resources(),
    )?;
    let referenced = validate_role_count(
        candidate.referenced.len(),
        ResourceRoleV1::Referenced,
        limits.max_referenced_resources(),
    )?;
    let created = validate_role_count(
        candidate.created.len(),
        ResourceRoleV1::Created,
        limits.max_created_resources(),
    )?;
    Ok(ResourceRoleCountsV1 {
        consumed,
        referenced,
        created,
    })
}

fn validate_role_count(
    actual: usize,
    role: ResourceRoleV1,
    maximum: u16,
) -> Result<u16, ResourceRolePartitionErrorV1> {
    let normalized = u16::try_from(actual)
        .map_err(|_| ResourceRolePartitionErrorV1::CountLimitExceeded { role, maximum })?;
    if normalized > maximum {
        return Err(ResourceRolePartitionErrorV1::CountLimitExceeded { role, maximum });
    }
    Ok(normalized)
}

fn copy_and_sort(
    role: ResourceRoleV1,
    candidates: &[ResourceId],
) -> Result<Vec<ResourceId>, ResourceRolePartitionErrorV1> {
    let mut canonical = reserve_role_capacity(role, candidates.len())?;
    for resource_id in candidates {
        let position = insertion_position(&canonical, resource_id);
        canonical.insert(position, *resource_id);
    }
    Ok(canonical)
}

fn insertion_position(resources: &[ResourceId], resource_id: &ResourceId) -> usize {
    // Every private role scan receives a list already bounded to at most 256
    // entries, so this `u16` counter cannot reach its saturation point.
    let mut position = 0_u16;
    while let Some(current) = resources.get(usize::from(position)) {
        if current.cmp(resource_id).is_gt() {
            break;
        }
        position = position.saturating_add(1);
    }
    usize::from(position)
}

fn reserve_role_capacity(
    role: ResourceRoleV1,
    count: usize,
) -> Result<Vec<ResourceId>, ResourceRolePartitionErrorV1> {
    let mut resources = Vec::new();
    resources
        .try_reserve_exact(count)
        .map_err(|_| ResourceRolePartitionErrorV1::CapacityUnavailable { role })?;
    Ok(resources)
}

fn validate_duplicates(
    resources: &[ResourceId],
    role: ResourceRoleV1,
) -> Result<(), ResourceRolePartitionErrorV1> {
    let mut remaining = resources;
    while let Some((resource_id, tail)) = remaining.split_first() {
        if tail.contains(resource_id) {
            return Err(ResourceRolePartitionErrorV1::DuplicateResourceId { role });
        }
        remaining = tail;
    }
    Ok(())
}

fn validate_disjoint(
    first: &[ResourceId],
    second: &[ResourceId],
    first_role: ResourceRoleV1,
    second_role: ResourceRoleV1,
) -> Result<(), ResourceRolePartitionErrorV1> {
    for resource_id in first {
        if second.contains(resource_id) {
            return Err(ResourceRolePartitionErrorV1::ResourceRoleCollision {
                first_role,
                second_role,
            });
        }
    }
    Ok(())
}

fn position_in(
    role: ResourceRoleV1,
    resources: &[ResourceId],
    resource_id: &ResourceId,
) -> Option<ResourceRolePositionV1> {
    // Successful construction bounds the list to 256, so conversion from this
    // counter to the public `u32` ordinal is exact.
    let mut ordinal = 0_u16;
    while let Some(canonical_id) = resources.get(usize::from(ordinal)).copied() {
        if canonical_id == *resource_id {
            return Some(ResourceRolePositionV1 {
                resource_id: canonical_id,
                role,
                ordinal: u32::from(ordinal),
            });
        }
        ordinal = ordinal.saturating_add(1);
    }
    None
}

#[cfg(test)]
mod tests;

#[cfg(kani)]
mod kani_harnesses;
