//! Pure structural transition validation for the Zeno Resource Machine.
//!
//! The current `WP3a` slice canonicalizes bounded, inert resource identifiers
//! into disjoint role lists. It establishes no resource-body, transition,
//! membership, proof, state, or commit authority.

#![no_std]
#![forbid(unsafe_code)]

extern crate alloc;

#[cfg(test)]
extern crate std;

mod resource_roles;

pub use resource_roles::{
    CanonicalResourceRolesV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRolePositionV1, ResourceRoleV1,
};
