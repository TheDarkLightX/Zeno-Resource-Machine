# Policy activation, reconfiguration, revocation, and history

**Status:** research input for `ZRM-TASK-001`; non-normative; no implementation, conformance, release, or production claim

**Author:** Dana Edwards  
**Drafting and research assistance:** GPT-5.6

## Research question

What is the smallest composable policy-lifecycle state machine that lets ZRM publish immutable policy content without activating it; select exactly one creation policy, or explicitly suspend creation, for every recognized resource kind; preserve selected predecessors for existing resources without allowing them to create; hard-revoke one activation without resurrecting byte-identical policy content; and prevent rollback, fast-forward, equivocation, replay, and ambiguous partial updates?

The review uses primary academic literature. No cited system is treated as a drop-in ZRM design.

## Literature synthesis

### Declarative authorization: SecPAL

Becker, Fournet, and Gordon separate changing authorization policy from application implementation and evaluate requests against a current policy database. They also give their core language a terminating, sound, and complete semantics under stated restrictions.

**Adopt:** applications do not decide which policy is current. Lifecycle semantics must be independently executable and reviewable.

**Do not import directly:** ZRM does not need SecPAL's complete logic language in the activation kernel. The lifecycle object should remain a small closed algebra whose result can feed richer policy evaluation.

Primary source: Moritz Y. Becker, Cedric Fournet, and Andrew D. Gordon, *SecPAL: Design and Semantics of a Decentralized Authorization Language*, Microsoft Research Technical Report MSR-TR-2006-120, revised 2007. Official publication: https://www.microsoft.com/en-us/research/publication/secpal-design-and-semantics-of-a-decentralized-authorization-language/

### Responsibility separation and revocation: TUF

Cappos et al. divide software-update trust among roles, separate update content from timeliness and repository consistency, and distinguish explicit revocation from expiry-based invalidation.

**Adopt:** policy-content publication and activation are different responsibilities. Hard revocation is an explicit governed transition. Expiry remains an additional check, not a substitute for immediate revocation.

**Do not import directly:** TUF secures software distribution. ZRM needs a proof-system-neutral resource-policy lifecycle and must not equate a signing role with semantic policy authority.

Primary source: Justin Cappos, Justin Samuel, Scott Baker, and John H. Hartman, *Survivable Key Compromise in Software Update Systems*, ACM CCS 2010. Official paper: https://theupdateframework.io/papers/survivable-key-compromise-ccs2010.pdf

### Context-bound credentials: Macaroons

Macaroons attenuate delegated authority through caveats. Their revocation discussion uses short lifetimes, state checks, whitelists or blacklists, expiry, and epoch counters; third-party discharges are bound to their authorizing credential.

**Adopt:** a resource or fact derived from policy must remain bound to the exact activation and fresh snapshot that gave it meaning.

**Do not import directly:** caveats do not decide which policy activation is current, predecessor, or revoked. ZRM must establish that governed state first.

Primary source: Arnar Birgisson et al., *Macaroons: Cookies with Contextual Caveats for Decentralized Authorization in the Cloud*, NDSS 2014. Official paper: https://www.ndss-symposium.org/wp-content/uploads/2017/09/04_3_1.pdf

### Reconfiguration authority: Vertical Paxos

Lamport, Malkhi, and Zhou separate ordinary state-machine agreement from an auxiliary configuration master that facilitates reconfiguration.

**Adopt:** changing the governed policy snapshot is a governance operation, not an ordinary resource transition. The semantic kernel consumes a resolved snapshot but does not reconfigure it.

**Do not import directly:** this task specifies a sequential lifecycle object, not consensus or a configuration-master implementation.

Primary source: Leslie Lamport, Dahlia Malkhi, and Lidong Zhou, *Vertical Paxos and Primary-Backup Replication*, 2009, corrected 2019. Official paper: https://lamport.azurewebsites.net/pubs/vertical-paxos.pdf

### Linearizable object boundaries: Herlihy and Wing

Linearizability gives concurrent objects a legal sequential meaning and is local, allowing objects to be implemented and verified independently.

**Adopt:** policy activation is specified first as a total sequential object. A durable implementation can later refine it with one linearization point over the composite machine head. Rejection is an exact no-op.

Primary source: Maurice P. Herlihy and Jeannette M. Wing, *Linearizability: A Correctness Condition for Concurrent Objects*, ACM TOPLAS 12(3), 1990. Official paper: https://cs.brown.edu/~mph/HerlihyW90/p463-herlihy.pdf

### Rollback and fast-forward resistance: Mercury

Mercury detects rollback by comparing newly received versions with previous state and identifies the dual fast-forward attack, where a compromised source advances versions arbitrarily to create denial of service.

**Adopt:** a policy snapshot version is derived rather than caller-selected. Every success produces exactly `old_version + 1`, and the exact parent snapshot identity is checked in addition to the scalar version.

**ZRM improvement:** removing the next-version input makes version-bomb states unrepresentable at the authority API instead of merely detectable later.

Primary source: Trishank Karthik Kuppusamy, Vladimir Diaz, and Justin Cappos, *Mercury: Bandwidth-Effective Prevention of Rollback Attacks Against Community Repositories*, USENIX ATC 2017. Official paper: https://www.usenix.org/system/files/conference/atc17/atc17-kuppusamy.pdf

### Chained authenticated snapshots: CONIKS

CONIKS signs authenticated directory snapshots and includes the previous snapshot hash, committing each snapshot to a linear history. Auditors compare histories to detect equivocation.

**Adopt:** each policy snapshot binds its exact parent. A production profile may externally audit or anchor that chain.

**Do not overclaim:** a parent hash alone cannot stop a malicious authority from showing different chains to isolated parties. ZRM needs a consensus, transparency, or anchor profile before claiming global non-equivocation.

Primary source: Marcela S. Melara et al., *CONIKS: Bringing Key Transparency to End Users*, USENIX Security 2015. Official paper: https://www.usenix.org/system/files/conference/usenixsecurity15/sec15-paper-melara.pdf

### Irreversible state protocols: Iris

Iris supports state protocols that express irreversibility and ownership of transition rights.

**Adopt:** hard revocation is a monotonic tombstone on one activation instance. Reinstating identical content creates a new activation identity instead of reversing the tombstone. Governance authorization remains a separate capability.

**Do not import directly:** the executable artifact is Python, not an Iris or Coq proof. Exact Lean and ESSO obligations are stated separately.

Primary source: Ralf Jung et al., *Iris: Monoids and Invariants as an Orthogonal Basis for Concurrent Reasoning*, POPL 2015. Official paper: https://iris-project.org/pdfs/2015-popl-iris1-final.pdf

## Derived architecture

### Separate three identities

```text
PolicyContentId
    complete immutable policy content

PolicyActivationId
    one governed activation instance of that content

PolicySnapshotId
    one ordered governed policy snapshot
```

A content identifier answers what the policy is. An activation identifier answers which governed activation authorized a resource or fact. A snapshot identifier answers under which ordered configuration that activation was meaningful.

Conflating content and activation creates a resurrection bug: if hard-revoked content is later reinstated byte-for-byte, a content-only capability cannot distinguish the revoked activation from the new one.

### Store minimal lifecycle state and derive disposition

Store only:

```text
ActivationStatus = Usable | HardRevoked
CreationSelection(kind) = Enabled(activation) | Suspended
```

Derive:

```text
HardRevoked                     -> HardRevoked
Usable and selected             -> CurrentCreation
Usable and not selected         -> AcceptedPredecessor
```

This makes “selected but predecessor” and “current but not selected” unrepresentable.

### Use a closed command algebra

```text
RegisterPolicyContent
ActivatePolicy
SuspendCreation
HardRevokePredecessor
```

Content registration is inert. Replacing or suspending a current activation explicitly chooses whether the old instance remains an accepted predecessor or becomes hard-revoked. A standalone revocation may target only an unselected predecessor; revoking current authority must be atomic with replacement or suspension.

### Bind activation identity to the exact command

The candidate activation identity binds machine, domain, parent snapshot, exact governance command digest, content identity, resource kind, and per-kind generation. The exact command digest makes retirement semantics part of activation provenance instead of recovering them indirectly from an operation label.

### Exact history and replay

Every success derives:

```text
next_version = current_version + 1
next_parent_snapshot = current_snapshot
next_snapshot = Commit(complete next payload)
```

One operation ID binds one exact command digest:

- same operation ID and digest: `AlreadyApplied`, no effects;
- same operation ID and different digest: reject equivocation;
- new operation against stale parent or version: reject, no effects.

Exact replay is classified before stale-parent rejection so lost-ack recovery still works after later progress.

## Improvements over a straightforward design

1. No duplicated current/disposition state.
2. No caller-provided next version.
3. No content-wide resurrection after revocation.
4. No implicit predecessor semantics during replacement.
5. No selected-and-revoked intermediate state.
6. No absence-as-suspension ambiguity.
7. No replay/staleness conflation.
8. Activation provenance binds the exact governance command digest.
9. No false claim that local parent chaining prevents global equivocation.

## Decisions still required

Before `ZRM-TASK-001` can complete, maintainers and independent reviewers must decide the three-identity model; derived disposition; explicit enabled-or-suspended rows; terminal activation-instance revocation; fresh activation identity on reactivation; exact successor versions and parent binding; atomic current revocation; canonical bytes and domains for content, command, activation, replay, and snapshots; governance authorization; and any external non-equivocation/finality profile.

## Non-claims

This review does not approve RFC-0001, define canonical bytes, authenticate governance, prove cryptographic collision resistance, implement persistence, establish consensus, prevent global equivocation, or authorize production use.
