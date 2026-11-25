# Agent Work Log: Public bounded explorer for the RFC-0001 commit path

## Task interpretation

Add non-authority tooling that explores the reference models exhaustively on small bounds,
finds shortest counterexamples, and reports the coarsest observable state. No kernel,
crate, protocol, specification-package or conformance change.

## Scope and non-goals

**In scope:**
- a standard-library bounded explorer;
- one composed reduced-bound model of the RFC-0001 commit path, with the intent map's
  commit-path mutants;
- a replayable evidence record;
- a Zeno-ADP cross-check of the quotient port.

**Non-goals:**
- approving RFC-0001;
- modeling policy creation, fact freshness or recursive composition;
- Rust implementation, canonical bytes, CBC or package-manifest changes.

## Files and specifications inspected

**Repository documents:**
- `AGENTS.md`, `README.md`, `QUALITY_GATES.md`, `IMPLEMENTATION_PLAN.md`;
- `SPECIFICATION.md` (structure only).

**RFC-0001:**
- sections 8 to 12;
- the assurance plan and the formal obligations.

**Semantic-closure package:**
- `formal/state-machine/semantic_closure_v1/README.md`;
- `abstraction_and_refinement_obligations.md`;
- `intent_map.json`.

**Other material:**
- `reviews/RFC-0001-semantic-design-packet.md`;
- the existing reference models and their tests;
- the CI workflow and the repository gate scripts.

## Change class

Class B: non-authority tooling. Nothing here is imported by a crate or can affect accepted
state.

## Affected invariants

None changed. The model states twelve invariants drawn from RFC-0001's formal-obligation
names and the intent map. Each is checked on every reachable state or transition of the
correct model.

## Affected CBC obligations

None. `CONFORMANCE_MATRIX.json` is unchanged.

## Disaster states

The following are modeled as mutants and exercised:
- stale-plan commit;
- policy update reusing the machine root;
- replay lookup outside the commit boundary;
- duplicate retry effect;
- unknown outcome reported as rejection;
- resolution reapplying an effect;
- partial durable commit.

## Authority boundary

Unchanged. The tooling runs only in tests and by hand. It is not referenced by
`crates/`, and its outputs are evidence, not authority.

## Semantic change declaration

- Authority affected: none
- Attacker-controlled fields: none
- Governed fields: none
- New valid states: none
- New invalid states: none
- Cryptographic bindings changed: none
- Replay/freshness implications: none
- Resource-bound implications: none
- Upgrade/revocation implications: none
- Failure behavior and precedence: the explorer fails closed with `BoundExceeded` above its
  state limit

## Independent tracks

**Implementation and oracle:** the model and its tests were written by the same agent. The
expected shortest trace and the instances killed for every mutant were predicted by hand
from the model rules before the first exploration run. The exploration confirmed every
prediction, including the `retry_duplicates_effect` survivor. The scenario tests were
written afterwards.

**Formal-assurance track:** the Zeno-ADP 0.8.0 quotient serves as an independent oracle for
the quotient port.

**Adversarial review:** none yet. This is required from a reviewer.

## Proposed design

### Design-choice review

- **Design forces:** public replay with the standard library; deterministic shortest traces;
  a minimal observable state count that a reviewer can check.
- **Pattern selected:** none beyond a frozen `Model` value with function fields.
- **Invalid states prevented:** duplicate alphabets, outcomes and invariant names are
  rejected. A quotient certificate is replayed against its raw table.
- **Extension point:** another reference model supplies a new `Model`.
- **Alternatives rejected:**
  - TLA+ or Alloy, which would add a tool dependency and stay unreplayable without it;
  - separate per-model files mirroring the internal model names, which would invite
    confusion with the internal artifacts.
- **Pattern-specific failure modes:** a model whose `step` is nondeterministic. States must
  be hashable values, and the tests re-run the exploration for byte-identical output.
- **Enforcement and tests:** `reference_models/tests/test_bounded_explorer.py` and
  `test_rfc0001_commit_path_v1.py`.
- **Technical AI-review status:** author self-review only.

## Alternatives considered

- Modeling each internal model separately: rejected, because the obligations document asks
  for a composed reduced-bound model.
- Adding the generator as a Git dependency: rejected, because the hygiene gate forbids
  unreviewed Git dependencies. The crates.io release is exact-pinned instead.

## Test-first plan

Hand-derived scenarios came first:
- exact retry;
- consumed-plan retry;
- conflict versus stale;
- stale rejection;
- crash and lost acknowledgement;
- read-only observations;
- the expected shortest trace for each single-caller mutant.

Exploration, quotient and evidence checks came after.

## Implementation summary

**`bounded_explorer.py`:**
- breadth-first exploration with exact state merging;
- shortest state and edge counterexamples, checked independently by `replay`;
- the coarsest observable quotient with separating probes, ported from Zeno-ADP 0.8.0;
- a report of fields the quotient cannot see.

**`rfc0001_commit_path_v1.py`:** the composed model with two second-caller variants, two
plan readings and seven mutants.

**`rfc0001_commit_path_explorer.py`:** the evidence record and `--check`.

## Files changed

- `.gitignore`: ignores the generator's build directory
- `evidence/README.md`: adds a paragraph on the new record
- `evidence/rfc0001-commit-path-exploration-v1.json`: new
- `reference_models/RFC0001_COMMIT_PATH_V1_ORACLE.md`: new
- `reference_models/bounded_explorer.py`: new
- `reference_models/rfc0001_commit_path_explorer.py`: new
- `reference_models/rfc0001_commit_path_v1.py`: new
- `reference_models/tests/test_bounded_explorer.py`: new
- `reference_models/tests/test_rfc0001_commit_path_v1.py`: new
- `reference_models/zeno_adp_vectors/`: new; contains `Cargo.toml`, `Cargo.lock`,
  `src/main.rs`, `regenerate.py`, `README.md` and `vectors_0_8_0.json`
- `worklogs/2026-11-25-rfc0001-commit-path-explorer.md`: this log

## Typed statements and APIs changed

None in any crate.

## Tests added or changed

Two new unittest modules in `reference_models/tests`. No existing test is changed.

## Mutants killed or surviving

| Mutant | Instances killed |
| --- | --- |
| `stale_plan_commits` | 4/4 |
| `policy_change_reuses_machine_root` | 4/4 |
| `replay_lookup_outside_commit_boundary` | 4/4 |
| `retry_duplicates_effect` | 3/4 |
| `unknown_reported_as_rejected` | 4/4 |
| `resolution_reapplies_effect` | 4/4 |
| `partial_durable_commit` | 4/4 |

`retry_duplicates_effect` survives the conflicting / consumed instance, which has no path
to the exact-match branch. The oracle document explains why.

## Formal/model evidence

The evidence is bounded exhaustive exploration of four instances. There is no theorem
proving, Kani or Lean work.

## Canonical hashes and vectors changed

No protocol vectors changed. There are new tooling vectors for the quotient cross-check.

## Dependencies changed

The dev-only generator depends on `zeno-adp =0.8.0` from crates.io, with transitive
`num-bigint`, `num-integer`, `num-traits` and `autocfg`, pinned by its own `Cargo.lock`.

**Dependency record:**
- **Purpose:** an independent oracle for the quotient port.
- **Why the standard library is insufficient:** an oracle must be a separate implementation.
- **Native surface:** no unsafe code or native code is added to ZRM. `num-traits` and
  `num-integer` have `autocfg` build scripts.
- **Licenses:** MIT or Apache-2.0.
- **Determinism:** the integer outputs are deterministic.
- **no_std:** not applicable.
- **Removal plan:** delete the directory. The committed vectors then remain as fixed
  expectations.

No workspace manifest or lockfile changed.

## Performance and resource-bound impact

- Exploration is bounded at 50,000 states per instance; the largest has 19,349.
- The full reference-model suite takes about 18 seconds on Python 3.12.

## Commands executed

| Command | Result | Evidence/artifact |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s reference_models/tests` | 71 tests OK | console |
| `python3 -m reference_models.rfc0001_commit_path_explorer --check` | evidence matches | `evidence/rfc0001-commit-path-exploration-v1.json` |
| `RUSTUP_TOOLCHAIN=stable python3 reference_models/zeno_adp_vectors/regenerate.py --check` | vectors match | `reference_models/zeno_adp_vectors/vectors_0_8_0.json` |
| `python3 tools/check_repository_hygiene.py` | passed | console |
| `python3 tools/check_conformance.py` | passed, 46 obligations | console |
| `python3 tools/check_delegation_plan.py` | passed | console |
| `python3 tools/check_package_manifest.py` | passed | console |
| `RUSTUP_TOOLCHAIN=stable python3 tools/check_complexity.py --report target/complexity-report.json` | passed | console |
| `RUSTUP_TOOLCHAIN=stable python3 tools/check_code_quality.py --report target/code-quality-report.json` | passed | console |
| `python3 -m unittest discover -s tools/tests` | OK | console |
| `python3 tools/check_architecture.py` | NOT RUN to completion | see below |

`check_architecture.py` invokes `cargo +1.87.0 rustdoc` on the policy crate. Toolchain
1.87.0 could not be downloaded in the authoring environment, so the gate is unsatisfied
locally. This change touches no crate, and hosted CI runs the gate.

Cargo format, Clippy, tests, Kani, Miri, fuzz and coverage were not run. They cover
`crates/` and `fuzz/`, which this change does not touch.

## Self-review

- [x] no unrelated changes
- [x] no weakened tests or claims
- [x] no raw data promoted to authority
- [x] reject-is-no-op preserved (the model checks it; no implementation changed)
- [x] arithmetic and bounds checked (state limit, fail closed)
- [x] canonical bytes/vectors updated if needed (none needed)
- [x] docs/matrix updated (docs only; matrix unaffected)
- [x] dependency impact reviewed
- [x] remaining uncertainty disclosed

## Remaining gaps and non-claims

- The bounded model is not an unbounded proof.
- The model is one reading of a draft RFC. The open point on plan ownership after
  `OutcomeUnknown` is explored under both readings and needs a maintainer decision.
- The model is not the internal models and replays none of their evidence.
- The generator was built with stable 1.97.0, not the pinned 1.87.0.
- Policy-creation, fact-freshness and recursive intents remain unmodeled here.

## Human review required

- **Specified behaviors confirmed:** the model's reading of RFC-0001 sections 10 to 12.
- **Exact assurance results:** the tables above.
- **CBC obligations covered:** none claimed.
- **Remaining gaps and non-claims:** as listed above.
- **Required reviewers/roles:** a semantic owner, for the plan-ownership question.
- **Review focus:** whether each modeled classification and environment choice matches the
  intended semantics.
- **Promotion blocked until:** not applicable. This is evidence only.
