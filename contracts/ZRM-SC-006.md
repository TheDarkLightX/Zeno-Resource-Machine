# ZRM-SC-006 — Governed verifier registry and sealed facts

> **Derived review oracle.** `SPECIFICATION.md` and approved RFCs remain normative. This contract MUST NOT broaden their accepted behavior. Ambiguity fails closed.

## Authority granted

Only the governed verifier registry may create:

- `VerifiedLogicFact`;
- `VerifiedControllerFact`;
- `VerifiedTransformationFact`;
- `VerifiedDaFact`;
- `VerifiedExternalAttestationFact`, where an active profile defines it;
- `VerifiedAdmissionFact`;
- profile-specific postcommit aggregation or anchor facts.

Each capability establishes only the exact relation and bindings named by its governed verifier policy.

## Inputs

### Untrusted

- artifact bytes;
- remote verifier responses;
- caller-supplied verifier/policy objects;
- claimed public output;
- process exit status or metadata.

### Governed

- authenticated verifier registry;
- canonical verifier policy contents;
- active/revocation state;
- pinned verifier/program/key/release identity;
- machine policy and cost model;
- coverage and non-claim profile artifacts.

### Derived

- exact canonical verifier statement;
- bounded artifact and output;
- verified backend result;
- sealed fact capability.

## Preconditions and invariants

1. The registry resolves a requested `VerifierPolicyId` to one exact governed policy. Request data does not supply authoritative policy contents.
2. `VerifierPolicyId` is content-derived and/or authenticated by registry membership such that the same ID cannot denote different security-relevant contents.
3. The policy is active, unrevoked, in-window, and authorized by the current machine policy.
4. Authority-bearing production paths accept only `proof_mode = Production`.
5. Registry selection exactly binds machine, domain, backend family, verifier ID, program/key digest, release identity, artifact codec, statement schema, output/journal schema, proof parameters, coverage, non-claims, TCB, cost model, and input/output/artifact bounds.
6. Structural “candidate compatibility” checks are not admission authority. APIs that inspect untrusted candidates are named and typed as structural checks.
7. Artifact, input, output, and depth limits are enforced before backend work or allocation.
8. The backend verifies the exact expected statement. The registry independently checks exact output and policy bindings before constructing a fact.
9. A remote verifier response remains untrusted until locally authenticated.
10. Registered backends are sealed and reviewed; arbitrary downstream crates cannot register runtime callbacks or mint facts.
11. Facts have private constructors and fields, no `Deserialize`, no `Default`, no conversion from `bool`, and no unchecked public constructor.
12. Precommit facts bind final `StatementHash`, exact claim hash and child statement hash, expected output, policy, and validity window.
13. Admission facts bind exact `JournalDraftHash`, expected program/key/policy/profile/release, reservation, and plan context.
14. Postcommit aggregation facts bind exact accepted-journal bytes/hashes and ordered manifest; they cannot retroactively authorize a transition.
15. Missing verifier, timeout, crash, malformed output, unsupported mode, stale/revoked policy, or solver `UNKNOWN` fails closed.

## Required postconditions

A sealed fact uniquely identifies:

- its lifecycle class;
- parent statement or journal;
- exact claim and statement;
- verifier policy and release;
- authenticated output;
- validity/freshness scope.

The fact cannot be reused for another transition, role, ordinal, resource, application, epoch, policy, program, or output.

## Forbidden states and mandatory counterexamples

| Counterexample | Required result |
| --- | --- |
| Expected policy ID copied onto a policy with different program digest | Rejection |
| `Test` or `Development` policy on production path | Rejection |
| Correct backend family but wrong verifier release | Rejection |
| Proof valid for another resource role or ordinal | Rejection |
| Backend returns correct-looking output for wrong statement | Rejection |
| Revoked policy | Rejection |
| Successful subprocess exit with malformed/mismatched output | Rejection |
| Remote service says `verified=true` | No authority |
| Arbitrary crate constructs or deserializes a fact | Compile-time/API impossibility |
| Postcommit aggregation receipt passed as admission | Type and policy rejection |

## Required evidence

- policy-content substitution tests;
- wrong program/key/release/profile/statement/output/role/ordinal tests;
- stale/revoked/mode-downgrade tests;
- malformed, timeout, crash, unavailable-tool tests;
- capability-forgery compile-fail tests;
- backend-registration sealing tests;
- mutation tests for every binding check;
- replayable verifier vectors and TCB record;
- explicit coverage/non-claim artifacts.

## Non-claims

A valid proof establishes only the governed relation. It does not imply application truth, physical-world truth, privacy, availability, finality, or commit.

## Specification anchors

Sections 5.3, 19, 20, 22, 24.4, 30, 31, and 32.
