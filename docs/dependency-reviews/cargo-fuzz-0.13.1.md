# Tooling review: cargo-fuzz 0.13.1

Purpose: build and execute the isolated `libfuzzer-sys` malformed-input target with deterministic committed seeds.

Scope: developer, PR-smoke, nightly, and release assurance only. The tool does not enter shipped ZRM crates or semantic protocol artifacts.

Version: exact tool version `0.13.1`, installed with its published lockfile. Fuzz builds use exact toolchain `nightly-2025-03-02`.

Authority and determinism: discovery runs are non-authoritative. Fixed corpus seeds and promoted regression tests are replayable; coverage evolution can vary with libFuzzer scheduling even under a fixed seed.

Native/build surface: cargo-fuzz drives compiler instrumentation and the native libFuzzer closure documented in `libfuzzer-sys-0.4.13.md`. It may write corpus and crash artifacts only within the fuzz workspace.

Removal plan: replace with another reviewed coverage-guided driver while preserving corpus replay, duration gates, and minimized-regression promotion.
