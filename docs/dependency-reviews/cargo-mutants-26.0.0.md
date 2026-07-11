# Tooling review: cargo-mutants 26.0.0

Purpose: generate controlled Rust source mutations and determine whether the ordinary WP1 test suite kills them.

Scope: CI and offline assurance only. It does not enter any runtime crate, protocol bytes, or shipped library dependency closure.

Version: exact tool version `26.0.0`, installed with its published lockfile in CI.

Risk and native/build surface: the tool copies and rewrites a temporary source tree, invokes Cargo, and executes repository tests. CI grants it read/write access only to the checked-out workspace and build directories. Its output never grants semantic authority.

Exclusions: `.cargo/mutants.toml` contains reviewed equivalent-mutant and Kani-only exclusions. New exclusions require review and an evidence update.

Removal plan: replace with another reviewed mutation runner while preserving the named critical mutant map and zero-missed-candidate gate.
