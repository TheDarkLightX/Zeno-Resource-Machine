//! Reference cryptographic framing for the Zeno Resource Machine.
//!
//! This crate will expose only closed, versioned protocol hash operations. It
//! does not accept caller-selected authority domains or runtime hash suites.
//!
//! Resource identifiers are derived only at the canonical codec boundary. The
//! former raw-slice operation is intentionally absent from this public API:
//!
//! ```compile_fail
//! use zrm_crypto::derive_resource_id_from_canonical_wire;
//!
//! let malformed_same_length_bytes = [0_u8; 595];
//! let _ = derive_resource_id_from_canonical_wire(&malformed_same_length_bytes);
//! ```

#![no_std]

#[cfg(test)]
extern crate std;

use core::fmt;

use sha2::{Digest, Sha256};
use zrm_types::{CryptoSuiteId, DomainId, MachineId, Nullifier, ResourceId, ZeroValueError};

const SHA256_SUITE_DOMAIN: &[u8] = b"zrm.crypto_suite.sha256.v1";
const TRANSPARENT_NULLIFIER_V1_DOMAIN: &[u8] = b"zrm.nullifier.transparent.v1";
const TRANSPARENT_NULLIFIER_PAYLOAD_BYTES: u32 = 96;

/// Normative bytes of `SHA256_REFERENCE_V1_ID`.
pub const SHA256_REFERENCE_V1_ID_BYTES: [u8; 32] = [
    0x99, 0xf6, 0xdd, 0x08, 0x23, 0xf8, 0x5c, 0xa7, 0x0e, 0xd6, 0xd9, 0x1b, 0xd0, 0x0f, 0x50, 0xdc,
    0x63, 0xfd, 0xb5, 0xde, 0xc3, 0xd9, 0xfc, 0x72, 0x12, 0xb9, 0xef, 0xf2, 0x7e, 0x3b, 0x13, 0x91,
];

/// Failure while framing or converting a closed protocol hash operation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HashConstructionError {
    /// A resource wire length was neither 595 nor 603 bytes.
    ///
    /// Retained so callers matching the pre-alpha error enum do not need an
    /// unrelated migration when raw resource hashing leaves this crate.
    InvalidResourceWireLength(usize),
    /// A host length did not fit the protocol's explicit `u16` or `u32` frame.
    LengthOverflow,
    /// The digest was all zero, which protocol identifier types prohibit.
    AllZeroDigest,
}

impl fmt::Display for HashConstructionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidResourceWireLength(length) => {
                write!(
                    formatter,
                    "invalid canonical ResourceWireV1 length: {length}"
                )
            }
            Self::LengthOverflow => {
                formatter.write_str("hash frame length exceeds its explicit width")
            }
            Self::AllZeroDigest => {
                formatter.write_str("protocol hash produced a prohibited all-zero digest")
            }
        }
    }
}

fn start_framed_hash(domain: &[u8], payload_length: u32) -> Result<Sha256, HashConstructionError> {
    let domain_length =
        u16::try_from(domain.len()).map_err(|_| HashConstructionError::LengthOverflow)?;
    let mut hasher = Sha256::new();
    hasher.update(domain_length.to_be_bytes());
    hasher.update(domain);
    hasher.update(payload_length.to_be_bytes());
    Ok(hasher)
}

fn finish_hash(hasher: Sha256) -> [u8; 32] {
    hasher.finalize().into()
}

fn map_zero_digest(_: ZeroValueError) -> HashConstructionError {
    HashConstructionError::AllZeroDigest
}

/// Derives the schema-fixed SHA-256 reference-suite identifier.
///
/// # Errors
///
/// Fails closed if framing exceeds its explicit width or SHA-256 returns the
/// prohibited all-zero digest.
pub fn sha256_reference_suite_id() -> Result<CryptoSuiteId, HashConstructionError> {
    let hasher = start_framed_hash(SHA256_SUITE_DOMAIN, 0)?;
    CryptoSuiteId::try_from(finish_hash(hasher)).map_err(map_zero_digest)
}

/// Derives the transparent v0.1 nullifier for one machine/domain/resource.
///
/// This deterministic profile provides replay protection and no privacy.
///
/// # Errors
///
/// Fails closed if hash framing overflows or the digest is all zero.
pub fn derive_transparent_nullifier_v1(
    machine_id: MachineId,
    domain_id: DomainId,
    resource_id: ResourceId,
) -> Result<Nullifier, HashConstructionError> {
    let mut hasher = start_framed_hash(
        TRANSPARENT_NULLIFIER_V1_DOMAIN,
        TRANSPARENT_NULLIFIER_PAYLOAD_BYTES,
    )?;
    hasher.update(machine_id.as_bytes());
    hasher.update(domain_id.as_bytes());
    hasher.update(resource_id.as_bytes());
    Nullifier::try_from(finish_hash(hasher)).map_err(map_zero_digest)
}

#[cfg(test)]
mod tests {
    use super::{
        HashConstructionError, SHA256_REFERENCE_V1_ID_BYTES, derive_transparent_nullifier_v1,
        sha256_reference_suite_id,
    };
    use zrm_types::{CryptoSuiteId, DomainId, MachineId, ResourceId, ZeroValueError};

    #[test]
    fn sha256_reference_suite_id_matches_normative_vector() {
        let expected = CryptoSuiteId::try_from(SHA256_REFERENCE_V1_ID_BYTES);
        assert_eq!(
            sha256_reference_suite_id(),
            expected.map_err(|_| HashConstructionError::AllZeroDigest)
        );
    }

    #[test]
    fn hash_construction_errors_have_stable_diagnostics() {
        assert_eq!(
            std::format!("{}", HashConstructionError::InvalidResourceWireLength(7)),
            "invalid canonical ResourceWireV1 length: 7"
        );
        assert_eq!(
            std::format!("{}", HashConstructionError::LengthOverflow),
            "hash frame length exceeds its explicit width"
        );
        assert_eq!(
            std::format!("{}", HashConstructionError::AllZeroDigest),
            "protocol hash produced a prohibited all-zero digest"
        );
    }

    #[test]
    fn transparent_nullifier_changes_across_machine_domain_and_resource()
    -> Result<(), ZeroValueError> {
        let machine_a = MachineId::try_from([1; 32])?;
        let machine_b = MachineId::try_from([2; 32])?;
        let domain_a = DomainId::try_from([3; 32])?;
        let domain_b = DomainId::try_from([4; 32])?;
        let resource_a = ResourceId::try_from([5; 32])?;
        let resource_b = ResourceId::try_from([6; 32])?;

        let first = derive_transparent_nullifier_v1(machine_a, domain_a, resource_a);
        let machine_changed = derive_transparent_nullifier_v1(machine_b, domain_a, resource_a);
        let domain_changed = derive_transparent_nullifier_v1(machine_a, domain_b, resource_a);
        let resource_changed = derive_transparent_nullifier_v1(machine_a, domain_a, resource_b);
        assert!(first.is_ok());
        assert_ne!(first, machine_changed);
        assert_ne!(first, domain_changed);
        assert_ne!(first, resource_changed);
        Ok(())
    }
}
