//! Strict canonical codecs for the Zeno Resource Machine.
//!
//! Decoded wire values remain inert data until later semantic constructors
//! validate policy, state, and authority invariants.
//!
//! Raw byte slices cannot be converted into a typed resource identifier by a
//! supported hashing API. Callers must first construct a structurally
//! canonical [`ResourceWireV1`] and use [`ResourceWireV1::resource_id`].

#![no_std]

#[cfg(test)]
extern crate std;

extern crate alloc;

mod cursor;
mod error;
mod resource_wire_v1;

#[cfg(kani)]
mod kani_harnesses;

pub use error::{ResourceIdDerivationError, ResourceWireDecodeError, ResourceWireEncodeError};
pub use resource_wire_v1::{ResourceWireV1, decode_resource_wire_v1};
