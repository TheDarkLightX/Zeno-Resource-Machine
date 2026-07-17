# Ordered PR roadmap

Every PR below is independently reviewable and keeps current ZRM authority
unchanged until its own RFC and implementation gates are approved.

## PR 1 — frontier research packet (this PR)

Add the revision-bound source ledger, hypotheses, knowledge graph, executable
bounded models, Lean design proofs, a non-gating external ESSO observation,
Research Kernel report, checker, and exact nonclaims. No Rust or normative RFC
change.

Gate: all packet references and hashes validate, the full Python reference
suite passes, and the Lean source scan is clean. The recorded seven-job Lean
build is local validation until CI independently rebuilds the pinned package.
The external ESSO observation is not replayable from this repository, lacks the
required receipt fields, and is therefore context only rather than gate
evidence.

## PR 2 — accounting aggregate RFC

Propose `AccountingAggregateRowV1 { dimension, debit_total, credit_total }`,
monotone bounds, exact row coverage, boundary net projection, and external
no-op admission. Preserve the current RFC-0002 authority status until approval.

Gate: arbitrary-tree Lean theorem, bounded ESSO mutants, canonical byte vectors,
and a Rust refinement plan.

## PR 3 — proof-neutral semantic segment RFC

Define nonempty ordered manifest, `SemanticSegmentSummaryV1`, separate set,
trace, typed-map, and path roots, semantic/proof identities, and exact append
refinement. Define `ConditionalReceipt`, `ResolvedReceipt`, `DeferredAccumulator`,
`DecidedProof`, and `VerifiedPostcommitAggregationFact` type states.

Gate: every Catalan tree agrees; every omission, duplicate, permutation, gap,
overlap, proof-zero, release, and context substitution rejects.

## PR 4 — context bridge RFC and oracle

Define ordinary context preservation and a governed bridge for policy, verifier,
registry, cost, proof-adapter, or catalog upgrades. Bind activation, predecessor,
successor, replay, and fact invalidation.

Gate: Lean indexed-path proof plus ESSO ordinary-drift, ungoverned-bridge,
old-fact, wrong-predecessor, and bridge-replay mutants.

## PR 5 — authenticated-state logical port

Add non-authoritative interfaces and a sorted-map oracle for sealed point,
complete range, exact update, and history facts. Proof bytes remain outside
semantic identity; profiles bind namespaces, roots, encodings, and bounds.

Gate: two independent adapters refine one logical oracle; all proof/profile,
old-root, omission, extra-write, and range-phantom substitutions reject.

## PR 6 — deterministic batch profile

Specify canonical preset order, exact read dependencies, deterministic
reexecution or rejection, sequential root chain, non-authoritative concurrency
certificate, private commit plan, and atomic batch outcome.

Gate: all schedules refine the sequential oracle; crash injection yields only
pre-state or full authorized post-batch state; worker timing never changes public
rejection or journal order.

## PR 7 — private logic and policy receipt prototypes

Prototype a common outer receipt ABI, typed registry forest, semantic/cost
classes, leakage budget, private policy receipt, scope nullifier, and explicit
revocation/context-bridge binding. Do not claim privacy from proof size alone.

Gate: field, size, timing, root, error, registry, revocation, cost, subject,
scope, and context substitution corpus.

## PR 8 — state/history sibling commitment RFC

Define acyclic `MachineStateRoot`, `JournalHash`, `HistoryLeaf`, append-only
`HistoryRoot`, and `StateHeadRoot` siblings advanced atomically. Define the
independent checkpoint/finality anchor needed to detect rollback and forks.

Gate: cycle, fork, rollback, prefix, anchor, split-commit, and retry mutants.

## PR 9 — proof backend adapters and benchmark

Implement the same proof-neutral composer first in a minimal RISC Zero guest and
then in two folding prototypes: HyperNova-style per-kind routing and ProtoStar-
style selector routing. Keep `fold_one`, `fold_many`, `decide`, and `compress`
distinct. Defer ProtoGalaxy and CycleFold until justified by measurements.

Gate: exact child claim and context, no unresolved assumptions, all accumulators
decided, proof size independent of step count, declared growth with action-kind
count, and comparative prover/verifier/memory/cost data.

## PR 10 — reconstructive research evidence kernel

Start with canonical EventV2 bytes and schemas, then transactional event source,
deterministic reducer/export/replay, EvidenceReceiptV1, four-valued
PromotionReceiptV1, Lean/ESSO/Morph adapters, reproducible verifier builds, and
signed transparency checkpoints. Retire dual-authority JSONL only after exact
migration replay.

Gate: mutation, crash, cross-language, receipt substitution, SCC, descendant
invalidation, Lean adversarial, reproducible-build, rollback, and split-view
campaigns from `research_kernel_report.md`.

## Separate maintenance work

The existing policy-activation oracle branch should be rebased and repaired in
its own PR rather than duplicated here. Its current CI and semantic feedback
should be addressed independently of this research packet.
