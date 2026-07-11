# Tooling review: cargo-llvm-cov 0.8.5

Purpose: measure Rust source coverage using the pinned compiler's LLVM instrumentation and enforce the workspace line-coverage floor.

Scope: CI and offline assurance only. It does not enter runtime crates or protocol artifacts.

Version: exact tool version `0.8.5`, installed with its published lockfile in CI. The Rust `llvm-tools` component is installed from the exact `1.87.0` toolchain.

Limitations: coverage demonstrates execution, not correctness. Defensive all-zero SHA-256 paths, fallible allocation failures, and Kani-only harnesses may remain unreachable in ordinary tests and must be reported separately.

Removal plan: replace only with a coverage tool that preserves source-level reporting and the configured fail-closed threshold.
