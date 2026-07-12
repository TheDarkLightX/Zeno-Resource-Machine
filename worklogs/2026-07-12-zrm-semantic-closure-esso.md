# Work log — ZRM/ZRPF semantic closure with ESSO

**Date:** 2026-07-12  
**Change class:** E design package; no authority implementation  
**ZRM branch:** `agent/zrm-semantic-closure-esso-v1`  
**Stacked base:** `agent/semantic-contracts-v1` / draft PR #8  
**ESSO branch:** `agent/zrm-semantic-closure-v1`  
**ESSO draft PR:** `TheDarkLightX/ESSO#1`  
**Author:** Dana Edwards  
**Semantic drafting/modeling assistance:** OpenAI GPT-5.6 Pro

## Goal

Close as much open semantic work as could be responsibly resolved before the next ZRM and ZRPF implementation stages, then turn those decisions into bounded, replayable ESSO models and explicit refinement obligations.

The targeted questions were:

- current, predecessor, and hard-revoked policy semantics;
- exact trusted-context and stale-plan behavior;
- verifier-fact policy/release/epoch/class binding;
- exact-once retry after a lost acknowledgement;
- complete durable effect binding and crash recovery;
- admission versus postcommit recursive authority;
- ordered recursive semantic composition and tree-shape-independent semantic identity.

## Deliverables

### Draft RFCs

- `RFC-0001: Policy, Context, Fact Freshness, and Commit Authority`;
- `RFC-0002: Recursive Semantic Journal Composition`.

### Machine-readable design artifacts

- twelve ZRM semantic decisions;
- ten recursive composition decisions;
- intent-to-contract/model/mutant map;
- ZRM abstraction and refinement obligations;
- recursive composer/guest/accumulator refinement obligations.

### Review artifacts

- RFC-0001 semantic design/adversarial packet;
- RFC-0002 semantic design/adversarial packet;
- exact information-flow disclosure that the authoring track is not independent review.

### ESSO models

- policy lifecycle;
- plan freshness and admission;
- exact-once resource state;
- verifier-fact freshness and lifecycle class;
- atomic commit and recovery;
- recursive semantic composition.

### Targeted mutants

- creation under the wrong policy;
- stale plan commits;
- retry duplicates a value effect;
- Development-mode result creates a production fact;
- partial durable commit;
- recursive fold omits the middle leaf.

## Semantic decisions

### Policy

- Exactly one non-revoked current creation policy exists per resource kind.
- Created resources use the exact current policy identity.
- An accepted predecessor validates existing resources for permitted read/consume roles only.
- Predecessor disposition does not confer creation, mint, burn, reward, transformation, or verifier fallback authority.
- Hard revocation removes every normal use under that policy at the new authenticated snapshot.
- Hard revocation may strand active resources; recovery requires a separate governed rule.
- Rollback is a new policy update and state version, never reuse of an old snapshot tuple.

### Context, facts, and plans

- All uncommitted authority is exact-context-bound.
- Policy, state, epoch, ordering, crypto-suite, accumulator, or release changes stale old facts and plans.
- Production facts come only from governed Production-mode policies.
- Facts bind exact lifecycle class, parent, claim, child statement, output, policy snapshot, validation context, program/key, and release.
- Admission binds the exact `JournalDraft`; postcommit aggregation binds an `AcceptedJournal`; neither can substitute for the other.

### Commit and retry

- Finalization derives one complete bounded effect descriptor covering resources, nullifiers, replay records, rewards/escrow, outbox, audit, and write bytes.
- A future accepted-journal version must commit the complete effects root and counts before complete recursive composition can be claimed.
- New commit linearizes on one comparison of state root, state version, and validation-context hash, followed by one atomic write.
- Exact durable retry returns `AlreadyCommitted` and does not reapply effects.
- Same transition identity with different journal/effects is a replay conflict.
- Recovery yields complete pre-state or complete post-state.
- External delivery remains at-least-once unless the receiver supplies idempotency.

### Recursive composition

- Authenticated `AcceptedJournal` is the native postcommit semantic leaf.
- Semantic identity is separate from proof identity.
- Segments use dense positions and exact ordered manifest concatenation.
- State-root and state-version continuity are exact.
- Descendant uniqueness requires authenticated disjoint union, not an opaque root alone.
- Accounting, effects, messages, carry, and DA must each have complete explicit composition rules.
- Aggregation creates no hidden ZRM effect.
- Composition is partial associative for the same ordered valid leaves and is noncommutative.
- The first reference composer uses explicit bounded witnesses before optimized accumulators.

## ESSO workflow

The ESSO branch adds a SHA-pinned `ZRM Semantic Lab` workflow.

The bounded-oracle job:

1. installs ESSO;
2. validates every model as canonical ESSO-IR;
3. runs the fail-closed Z3 1-inductiveness gate;
4. injects each targeted disaster mutant;
5. requires a concrete `InitNotInv` or `InvNotInductive` witness for every mutant.

Parser failure, unsupported features, timeout, solver `unknown`, or generic solver error does not count as semantic mutation evidence.

The multi-solver job:

- installs CVC5;
- requires Z3 and CVC5;
- uses 30,000 ms per query;
- runs two determinism trials;
- fails on missing solver, disagreement, timeout, `unknown`, error, or positive-model counterexample.

## Final bounded results

ESSO commit: `8a38735257cb12454e3457ee59cf28bb9f970661`

Workflow run: `29186433550` — success

| Model | IR hash | Direct oracle | Z3/CVC5 |
| --- | --- | --- | --- |
| policy lifecycle | `sha256:9fbc36ed6fba5e7941bda6f50bb300f060ae307ede0ca9338997abbd2ad25a85` | 1-inductive | PASS |
| plan freshness | `sha256:8536afed0692e0214fba13a4bbf379e4c96c4259a09a150b6baba073d2362147` | 1-inductive | PASS |
| exact once | `sha256:9c97929a06272ebfaccc96e5ef1465b2cb1aaa789dfe877b57b7b7bf67b919e8` | 1-inductive | PASS |
| verifier fact freshness | `sha256:883a5cd35185dee2ed4ba44c5f8acc576cbcd9462b28296047dc8e67949d4d83` | 1-inductive | PASS |
| atomic commit recovery | `sha256:474c806539afb760cdb1dfb79c40e8d9fd1fd29a6dc64597a0d99f28a1cf9f16` | 1-inductive | PASS |
| recursive composition | `sha256:180d12605766063b7f97e51321be989442b4d9ae80fbfde5331c8c4255b69676` | 1-inductive | PASS |

Every targeted mutant produced `InvNotInductive` with a concrete action/state witness.

## Modeling discoveries

### Global enum symbol ambiguity

The initial models reused names such as `None`, `Committed`, and `Verified` across enum types. ESSO rejected the affected IRs because symbols are resolved globally. Every semantic domain was namespaced before a proof result was accepted.

### Reachability is not induction

The first plan model appeared safe on intended traces but was not 1-inductive: an arbitrary invariant state could have `PlanNone` while committed effects were visible. `PlanNoneIsPristine` was added, making the plan lifecycle state relation explicit rather than relying on reachability intuition.

### Fail-closed failure is not automatically useful evidence

The first checker treated any ESSO failure as a killed mutant. This could have allowed parser or unsupported-feature failure to masquerade as semantic evidence. The checker was tightened to require a concrete invariant counterexample.

## Evidence boundary

The ESSO models establish only the finite transition systems and exact hashes recorded in the evidence file. They do not establish:

- approval of the proposed semantics;
- correctness of the abstraction from protocol objects to model state;
- arbitrary-size or arbitrary-depth theorems;
- Rust implementation refinement;
- storage, cryptographic, proof-system, OS, compiler, or hardware correctness;
- data availability, consensus, finality, or privacy;
- exact-once external delivery;
- production readiness.

## Required next work

1. Independent semantic, authority-boundary, recursive-proof, and accumulator review.
2. Follow-up Class E canonical byte tables, domains, and independent vectors.
3. Slow reference Rust policy/state/fact/commit machine.
4. Slow explicit-vector recursive composer.
5. Differential tests from ESSO/reference models to Rust.
6. Kani, Loom, stateful fuzzing, mutation, and deterministic crash injection.
7. Parameterized formal proofs for exact-once state update, recovery, disjoint union, recursive associativity, and tree-shape independence.
8. Governed recursive guest/release and optimized accumulator profiles.

## Outcome

```text
AUTHORING_AND_BOUNDED_ORACLE_COMPLETE
INDEPENDENT_REVIEW_REQUIRED
NO_PROTOCOL_OR_PRODUCTION_AUTHORITY_CREATED
```
