# Dependency review: sha2 0.11.0

Purpose: implement the specification-fixed SHA-256 reference suite.

Why the standard library is insufficient: Rust's standard library has no SHA-256 implementation. A local cryptographic implementation would add a larger correctness and maintenance burden.

Version and features: exact version `0.11.0`, default features disabled. No allocation, OID, or zeroization feature is enabled by ZRM.

License: MIT OR Apache-2.0.

Source and maintenance: RustCrypto hashes project, published through crates.io.

Trusted-computing-base impact: `sha2` and its minimal all-target transitive closure enter the hashing TCB. The reviewed locked closure is `cfg-if 1.0.4`, `cpufeatures 0.3.0`, `libc 0.2.186`, `digest 0.11.3`, `block-buffer 0.12.1`, `crypto-common 0.2.2`, `hybrid-array 0.4.13`, and `typenum 1.20.1`. None uses a build script or proc macro in this closure. `libc` is selected by target-dependent CPU-feature detection even though it is absent from the current-host tree. No ZRM runtime dependency may enable a native backend or runtime-selected hash suite.

Unsafe and platform surface: the locked source contains unsafe blocks in `sha2`, `cpufeatures`, `block-buffer`, and `hybrid-array`. They cover architecture-specific intrinsics and feature detection plus internal buffer and array operations. ZRM does not enable optional assembly features, and this closure contains no build script or proc macro. These dependencies remain part of the hashing TCB even though ZRM's own crates forbid unsafe code. Independent fixed vectors constrain observable digest behavior. A future Miri run can exercise supported code paths, but it cannot establish the soundness of every architecture-specific path.

Determinism: the digest is deterministic over explicit bytes. ZRM supplies all domain and length framing itself.

Alternatives considered: a hand-written SHA-256 implementation and an operating-system crypto API. Both were rejected because they add cryptographic implementation risk or platform/I/O coupling.

Removal plan: replace only through a versioned cryptographic-suite RFC, independent vectors, and compatibility review.
