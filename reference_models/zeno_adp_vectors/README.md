# Zeno-ADP quotient cross-check

`reference_models/bounded_explorer.py` ports `state_discovery::RawModel::quotient` from
[Zeno-ADP](https://github.com/TheDarkLightX/Zeno-ADP) 0.8.0 to the Python standard
library. This directory holds the Rust program that asks Zeno-ADP itself for the answers.
`reference_models/tests/test_bounded_explorer.py` requires the port to match every one.

The vectors in `vectors_0_8_0.json` cover:

- 120 seeded random tables, with merges, unreachable states and several probes;
- the four correct RFC-0001 commit-path instances. Their tables are recorded by SHA-256,
  and the test recomputes them from the model.

```sh
python3 reference_models/zeno_adp_vectors/regenerate.py --check
```

**Rebuilding.** Regeneration builds the program with Cargo and needs network access to fetch
`zeno-adp = "=0.8.0"` from crates.io. Its transitive dependencies are `num-bigint`,
`num-integer`, `num-traits` and `autocfg`, as pinned by `Cargo.lock`.

If the repository's pinned toolchain is unavailable, set `RUSTUP_TOOLCHAIN` to an installed
one. The committed vectors were built with stable rustc 1.97.0 because 1.87.0 could not be
installed in the authoring environment.

**Scope.** This program is development tooling. It is not a workspace member, no ZRM crate
depends on it, and CI does not build it.
