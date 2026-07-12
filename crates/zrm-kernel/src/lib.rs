//! Pure resource and structural transition validation for the Zeno Resource Machine.
//!
//! `WP3a` canonicalizes bounded, inert resource identifiers into disjoint role
//! lists. `WP3b` converts a fixed-schema version-one wire candidate into a sealed
//! intrinsically valid resource body with an exactly derived identifier. These
//! stages establish no authenticated policy, transition, membership, proof,
//! state, or commit authority.

#![no_std]
#![forbid(unsafe_code)]

extern crate alloc;

#[cfg(test)]
extern crate std;

mod resource;
mod resource_roles;

pub use resource::{IntrinsicResourceErrorV1, IntrinsicResourceFieldV1, IntrinsicResourceV1};
pub use resource_roles::{
    CanonicalResourceRolesV1, ResourceRoleListsCandidateV1, ResourceRolePartitionErrorV1,
    ResourceRolePositionV1, ResourceRoleV1,
};
