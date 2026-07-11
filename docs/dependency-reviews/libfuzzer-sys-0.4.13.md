# Tooling dependency review: libfuzzer-sys 0.4.13

Purpose: provide the isolated `cargo-fuzz` target for malformed `ResourceWireV1` inputs.

Scope: fuzz workspace only. It is excluded from the semantic Cargo workspace and cannot enter shipped ZRM libraries.

Version and features: exact version `0.4.13`, default libFuzzer linkage.

License: MIT OR Apache-2.0 plus NCSA components.

Locked closure: `arbitrary 1.4.2`, `cc 1.2.66`, `find-msvc-tools 0.1.9`, `jobserver 0.1.35`, `getrandom 0.4.3`, `cfg-if 1.0.4`, `libc 0.2.186`, `r-efi 6.0.0`, and `shlex 2.0.1`, plus the runtime ZRM closure documented separately.

Native/build surface: Cargo metadata reports `custom-build` targets for `libfuzzer-sys 0.4.13`, `getrandom 0.4.3`, and `libc 0.2.186` in the fuzz closure. `libfuzzer-sys` uses its build script and `cc` to build and link LLVM libFuzzer support. `cc`, `find-msvc-tools`, `jobserver`, and `shlex` participate in native build orchestration; `getrandom`, `libc`, and `r-efi` add platform-specific tooling paths. The build scripts remain executable tooling TCB even when a target-specific branch is not exercised. This surface is accepted only in the isolated offline/CI fuzz workspace.

Determinism: fuzz discovery is not semantic authority. Fixed seeds and committed minimized regressions provide replayability.

Alternatives considered: handwritten random mutation and a custom harness. `cargo-fuzz` was selected because it is the standard Rust coverage-guided integration and keeps the native surface outside runtime crates.

Removal plan: the target can be replaced by another reviewed coverage-guided harness without changing protocol bytes or runtime APIs.
