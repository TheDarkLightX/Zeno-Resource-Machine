//! Bounded, untrusted verifier inputs for the Zeno Resource Machine.
//!
//! This first WP5 slice establishes only a protocol-ceiling byte-copy boundary.
//! It creates no verified fact, authenticates no policy-selected limit, and
//! performs no cryptographic or policy decision.

#![no_std]
#![forbid(unsafe_code)]

extern crate alloc;

mod artifact;

pub use artifact::{ArtifactErrorV1, BoundedArtifactV1};
