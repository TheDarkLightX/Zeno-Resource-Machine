# RFC-NNNN: <Title>

**Status:** Draft | Review | Accepted | Rejected | Superseded
**Authors:**
**Reviewers:**
**Created:** YYYY-MM-DD
**Target version:**
**Change class:** C | D | E

## Summary

One paragraph describing the protocol or architecture decision.

## Motivation

What concrete problem or disaster state exists? Why is the current design insufficient?

## Goals

- <Goal>

## Non-goals

- <Non-goal>

## Current behavior

Describe current types, bytes, statements, authority boundaries, state, rejects, and evidence.

## Proposed semantics

Define the transition relation, invariants, preconditions, postconditions, and failure behavior.

## Typed interfaces

```text
Types, constructors, inputs, outputs, sealed capabilities, and stable rejects.
```

## Authority and trust boundary

- Untrusted inputs:
- Authenticated facts:
- Governing policy:
- Commit authority:
- Revocation/rotation:
- Trusted computing base:

## Canonical encoding and hashing

- schema/version;
- field order;
- domain strings;
- limits;
- unknown/duplicate/trailing behavior;
- vectors;
- migration.

## Accounting and resource effects

List consumed, referenced, and created resources; accounting rows; units; transformations; mint/burn/reward authority.

## State, concurrency, and atomicity

Define read/write footprint, ordering, compare-and-swap, crash points, recovery, and exact-once behavior.

## Privacy and disclosure

State public/private/committed fields, leakage, metadata, and explicit non-claims.

## Data availability and external attestations

State what is committed, what is verified, and what remains an assumption.

## Resource and performance bounds

- maximum bytes/counts/depth;
- time/cycle/memory/storage budget;
- complexity model;
- benchmark plan.

## Security analysis

| Disaster state | Defense | Residual risk | Evidence |
| --- | --- | --- | --- |
| | | | |

## Alternatives considered

Include the simplest alternative, status quo, and reason for rejection.

## Compatibility and migration

- backward compatibility;
- version negotiation;
- state migration;
- rollback;
- replay across versions;
- deprecation.

## Test and assurance plan

- unit/invariant;
- BDD;
- property/metamorphic;
- mutation;
- fuzz;
- differential;
- Miri/Loom;
- Kani;
- deductive/theorem proof;
- release replay.

## Supply-chain and release impact

Dependencies, build tools, provenance, reproducibility, SBOM/CBOM, signing, public replay.

## Claim changes

What may be claimed after implementation? What remains a non-claim?

## Rollout and rollback

## Open questions

## Decision

Filled by maintainers after review.
