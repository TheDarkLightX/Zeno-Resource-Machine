# ZRM frontier research v2

This directory is a revision-bound, non-authoritative research packet for ZRM
at commit `a4d2868d92807947cbad5f0d7fd828b74ae1368c`. It synthesizes ARM RISC Zero,
recursive-proof, concurrency, authenticated-state, privacy, authorization, and
evidence-assurance literature into falsifiable ZRM architecture hypotheses.

The central result is a two-plane design:

- a proof-neutral semantic plane defines exact ZRM meaning over accepted
  journals, typed effects, accounting rows, state/context paths, and durability;
- replaceable evidence backends authenticate those relations but never define
  economic identity or create commit authority.

The highest-leverage concrete correction is accounting-specific. Checked
bounded signed addition can have different *definedness* under different proof
trees. The Lean packet exhibits the counterexample and proves that monotone
debit/credit limbs have identical result and definedness under both three-leaf
parenthesizations.

## Packet map

- [`breakthroughs.md`](breakthroughs.md) — architecture synthesis, literature
  comparison, evidence, and recommended next obligations.
- [`hypotheses.json`](hypotheses.json) — 24 ranked hypotheses with status,
  falsifier, sources, experiments, and formal obligations.
- [`knowledge_graph.json`](knowledge_graph.json) — cross-run knowledge graph
  linking sources, experiments, risks, breakthroughs, dependencies, and
  decisions.
- [`source_ledger.json`](source_ledger.json) — revision-recorded source ledger;
  mutable documentation pages are explicitly retrieval-dated rather than
  represented as immutable snapshots.
- [`experiments.json`](experiments.json) — executed and specified experiments;
  a specified experiment is never represented as passed.
- [`esso_campaigns.json`](esso_campaigns.json) — bounded state-machine and
  mutant campaigns.
- [`morph_reformulations.json`](morph_reformulations.json) — explicit design
  reformulations and strict replay requirements.
- [`research_kernel_report.md`](research_kernel_report.md) — three compounding
  MCP runs, observed kernel limits, and a proposed evidence force multiplier.
- [`pr_roadmap.md`](pr_roadmap.md) — independently reviewable follow-up PRs.
- [`evidence/`](evidence/) — deterministic model, Lean, ESSO, and Research
  Kernel execution records with scope and nonclaims.

Executable models live in:

- `reference_models/zrm_composition_frontier_v2.py`
- `reference_models/deterministic_authenticated_batch_v1.py`

Formal design evidence lives in:

- `formal/lean/arm_zrm_frontier_v2`

## Evidence summary

| Evidence | Result | Scope |
|---|---:|---|
| Composition frontier | 1,056 schedule checks | 12 tiny programs, 8 states |
| Declared fact-complete dependency model | 0 false-safe checks | bounded model; declarations are trusted |
| Write-only dependency mutant | 168 false-safe checks | bounded model only |
| Deterministic authenticated batch | 16/16 executions refine serial order | 8 states, 2 schedules |
| Authenticated program-read substitutions | 4/4 reject | point and one range shape; not general access-completeness proof |
| Omitted decision-dependency mutants | 2/2 legacy roots collide; 0/2 complete roots collide | nullifier guard and candidate invariant reads |
| Nullifier-only batch mutant | 4/8 invariant violations | bounded reserve states |
| Lean | local 7-job Lake build passed | four abstract modules; checker performs source scan only |
| ESSO | external run observed 8/8 inductive; 14/14 mutants killed | non-replayable context; excluded from gates |
| Research Kernel | 3 compounding runs | discovery index, not authority |

## Status

This PR does not change RFC status, normative protocol bytes, the conformance
matrix, Rust authority code, release status, or production readiness. Research
claims remain scoped to their source, model, proof, and experiment records.
