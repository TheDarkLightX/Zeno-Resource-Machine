//! Structural binding between an intrinsic resource body and canonical placement.

use core::fmt;

use crate::{
    CanonicalResourceRolesV1, IntrinsicResourceV1, ResourceRolePositionV1, ResourceRoleV1,
};
use zrm_types::ResourceId;

/// Local failure while binding an intrinsic resource to canonical roles.
///
/// This error has no canonical bytes or stable reject code. It identifies only
/// the local `WP3c` boundary and discloses no resource identifier.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IntrinsicRoleBindingErrorV1 {
    /// The intrinsic resource's derived identifier is absent from all roles.
    ResourceAbsentFromRoles,
}

impl fmt::Display for IntrinsicRoleBindingErrorV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ResourceAbsentFromRoles => {
                formatter.write_str("intrinsic resource is absent from canonical roles")
            }
        }
    }
}

/// A sealed intrinsic resource with its exact canonical role and ordinal.
///
/// The private fields bind the complete intrinsic body, its internally derived
/// [`ResourceId`], and the position derived from a validated
/// [`CanonicalResourceRolesV1`]. Callers cannot inject a different position
/// independently of the supplied partition:
///
/// ```compile_fail
/// use zrm_kernel::{
///     IntrinsicResourceV1, ResourceRolePositionV1,
///     RoleBoundIntrinsicResourceV1,
/// };
///
/// fn forge(
///     resource: IntrinsicResourceV1,
///     position: ResourceRolePositionV1,
/// ) {
///     // error[E0451]: fields of `RoleBoundIntrinsicResourceV1` are private.
///     let _forged = RoleBoundIntrinsicResourceV1 { resource, position };
/// }
/// ```
///
/// The partition remains caller-proposed and unauthenticated. This value proves
/// consistency within that partition, with no policy, complete body coverage,
/// membership, freshness, logic, transition, proof, state, or commit fact.
/// Separation of different resource bodies relies on the schema-fixed SHA-256
/// resource-ID derivation and its collision-resistance assumption.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[must_use = "a role-bound resource has no effect unless its result is used"]
pub struct RoleBoundIntrinsicResourceV1 {
    resource: IntrinsicResourceV1,
    position: ResourceRolePositionV1,
}

impl RoleBoundIntrinsicResourceV1 {
    /// Returns the exact intrinsic resource body used during binding.
    pub const fn resource(&self) -> &IntrinsicResourceV1 {
        &self.resource
    }

    /// Returns the identifier derived from the complete intrinsic body.
    #[must_use]
    pub const fn resource_id(&self) -> ResourceId {
        self.resource.resource_id()
    }

    /// Returns the canonical structural role derived from the partition.
    #[must_use]
    pub const fn role(&self) -> ResourceRoleV1 {
        self.position.role()
    }

    /// Returns the canonical zero-based ordinal derived from the partition.
    #[must_use]
    pub const fn ordinal(&self) -> u32 {
        self.position.ordinal()
    }

    /// Returns the self-contained structural position.
    #[must_use]
    pub const fn position(&self) -> ResourceRolePositionV1 {
        self.position
    }
}

impl CanonicalResourceRolesV1 {
    /// Binds an intrinsic body to its exact derived identifier, role, and ordinal.
    ///
    /// The lookup key is always [`IntrinsicResourceV1::resource_id`]. Callers
    /// cannot provide an alternative identifier, role, or ordinal independently
    /// of the supplied canonical partition. The partition itself remains
    /// caller-proposed and unauthenticated.
    ///
    /// # Errors
    ///
    /// Returns [`IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles`] when
    /// the derived identifier does not occur in the canonical partition.
    ///
    /// # Complexity and side effects
    ///
    /// This operation performs at most three bounded linear scans over lists
    /// containing at most 256 identifiers each. It allocates no memory,
    /// performs no I/O or hashing, and mutates neither input nor global state.
    ///
    /// # Panics
    ///
    /// This operation has no intentional panic path.
    pub fn bind_intrinsic(
        &self,
        resource: &IntrinsicResourceV1,
    ) -> Result<RoleBoundIntrinsicResourceV1, IntrinsicRoleBindingErrorV1> {
        let position = bind_position(self, &resource.resource_id())?;
        Ok(RoleBoundIntrinsicResourceV1 {
            resource: *resource,
            position,
        })
    }
}

fn bind_position(
    roles: &CanonicalResourceRolesV1,
    resource_id: &ResourceId,
) -> Result<ResourceRolePositionV1, IntrinsicRoleBindingErrorV1> {
    roles
        .position_of(resource_id)
        .ok_or(IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles)
}

#[cfg(kani)]
mod kani_harnesses;

#[cfg(test)]
mod tests;
