# 2026-07-13 — RFC-0001 oracle and delegation spine

## Goal

Convert the remaining ZRM completion problem from an open-ended request into:

1. an executable, non-authoritative logical oracle for the RFC-0001 policy,
   context, fact, replay, admission, and durability decisions; and
2. a machine-checked dependency graph that identifies the exact frontier closure
   required before bounded Max-tier implementation delegation is safe.

## Change classification

- **Primary class:** B, non-authority reference tooling and delegation controls.
- **Normative protocol change:** none.
- **Canonical bytes or hash domains changed:** none.
- **Public implementation claims changed:** none.
- **Authority created:** none.

The Python dataclasses are intentionally forgeable inert projections. They must
not be used as a design precedent for Rust capability constructors.

## Design packet

### Affected areas

- `reference_models/`
- `docs/`
- `tools/`
- repository CI wiring

### Authority boundary

The work describes and tests authority relations but does not cross an authority
boundary. It cannot authenticate policy, mint a fact, create a `CommitPlan`, or
commit state.

### Attacker-controlled fields

The oracle treats policy candidates, resource roles, fact projections, replay
descriptors, admission projections, machine-head projections, and storage
outcome signals as attacker-controlled inert data.

### Governed fields represented but not authenticated

- validation context;
- policy snapshot hash;
- verifier policy, release, program/key, and profile;
- durable replay record and accepted journal lookup;
- storage durability knowledge.

### Invariants made executable

- one selected current policy when creation is enabled;
- no current policy when creation is suspended;
- predecessors may validate existing resources but cannot create;
- hard-revoked policies authorize no normal role;
- verifier facts bind one exact class, claim, child, context, policy, release,
  program/key, output, and validity window;
- exact and conflicting replay classification precede stale-plan rejection;
- exact replay additionally requires the durable accepted journal to match;
- local admission rejects an unexpected fact;
- required admission binds exact journal, context, policy, verifier, release,
  program/key, profile, and reserved charge;
- indeterminate durability is not a confirmed rejection; and
- a raw durable acknowledgement still requires replay authentication.

### Deliberate interpretations requiring review

- replay lookup uses `(machine_id, domain_id, transition_id)`;
- policy IDs are unique within a resource-kind lifecycle snapshot;
- enabled and suspended current-policy cardinality is exact;
- durable journal lookup inconsistency is corruption rather than idempotent
  success; and
- local oracle reasons are not frozen protocol reject codes.

These interpretations are documented for independent disposition. They do not
approve RFC-0001.

## Files

- `reference_models/rfc0001_authority_oracle_v1.py`
- `reference_models/RFC0001_AUTHORITY_ORACLE_V1.md`
- `reference_models/rfc0001_authority_oracle_v1_counterexamples.json`
- `reference_models/tests/test_rfc0001_authority_oracle_v1.py`
- `docs/zrm_completion_tasks_v1.json`
- `docs/ZRM_DELEGATION_RUNBOOK.md`
- `tools/check_completion_tasks.py`
- `tools/tests/test_completion_tasks.py`
- `.github/workflows/ci.yml`

## Evidence

Local authoring checks:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference_models/tests -v
32 tests passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -v
12 tests passed
```

The branch CI additionally runs the live-reference completion checker against the
full repository and the existing Rust, fuzz, coverage, mutation, supply-chain,
and conformance gates.

## Completion graph result

The checked graph contains 25 tasks:

```text
complete            2
external_review     2
frontier_required   7
blocked             14
ready_max            0
ready_standard       0
```

The delegation-safe threshold requires `ZRM-COMP-003` through
`ZRM-COMP-011`. It intentionally remains false. The graph cannot promote a Max
task while a dependency is incomplete, its spec is unfrozen, a semantic decision
is open, or it is Class E.

## Non-claims

- no independent semantic or authority approval;
- no canonical authority ABI;
- no authenticated policy or trusted context;
- no governed verifier registry or sealed Rust fact;
- no final transition statement, semantic kernel, journal v2, or commit plan;
- no durable runtime or crash-consistency evidence;
- no recursive integration or production readiness.

## Next critical work

1. independent RFC-0001 semantic and authority review;
2. independent RFC-0002 recursive-composition review after accepted-journal
   semantics settle;
3. authority and journal/effects canonical ABI freezes;
4. trusted policy/context, verifier/fact, resource/statement, kernel, and runtime
   interface freezes; and
5. promotion of downstream implementation tasks one at a time to `ready_max`.
