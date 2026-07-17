# Temporary OpenRouter access design packet

**Date:** 2026-07-16
**Class:** B, non-authority developer tooling

Goal:
Let the maintainer enter a temporary OpenRouter key outside chat, confirm that
the agent can use OpenRouter through a free model, and remove the key afterward.

Affected modules:
`tools/openrouter_temp_access.py` and its focused tests.

Exact API:
`setup` stores a hidden key in an owner-only runtime file; `status` validates
it without printing it; `probe` requests an exact marker from
`openrouter/free`; `clear` removes it.

Authority boundary:
The helper is local developer tooling. Connectivity and model output grant no
protocol, CBC, commit, merge, review, or release authority.

Invariants and disaster states:
The key is never a command argument or output, the file and directory are
owner-only, redirects reject, the request and response are bounded, the probe
has no paid-model fallback, malformed responses fail closed, and cleanup is
explicit.

Canonical/versioning impact:
None.

Tests first:
Owner-only round trip and cleanup, invalid key shape, symlink rejection, exact
free model and token cap, exact marker, and redirect rejection.

Formal/dependency/performance impact:
No formal obligation or new dependency. Python standard library only. One
64-token free-model request and a 256,000-byte response bound.

Non-claims:
The runtime file is readable by the same operating-system user and root. Free
service availability, provider behavior, retention, correctness, and future
pricing are external. This helper makes no paid request and does not yet run the
Kimi review.

## Completion evidence

Summary:
Added one temporary-key helper with `setup`, `status`, `probe`, and `clear`.

Files changed:
`tools/openrouter_temp_access.py`, its focused test module, and this worklog.

Typed statements/APIs changed:
No ZRM API. The local CLI has the four commands listed above.

Invariants/disaster states:
The key is hidden on entry, absent from arguments and output, bounded, stored
under owner-only permissions, and removable. The free probe is exact, bounded,
nonredirecting, and has no paid fallback.

Tests and commands:

- `python3 -B -m unittest tools.tests.test_openrouter_temp_access -v`: 6 passed.
- `python3 -B tools/openrouter_temp_access.py --help`: passed.
- `python3 -B tools/openrouter_temp_access.py status`: rejected as expected
  because no key has been entered.
- `python3 -B tools/check_repository_hygiene.py`: passed.
- `python3 -B tools/check_complexity.py`: passed with zero advisories.
- `python3 -B tools/check_code_quality.py`: excellent-candidate, passed.
- `git diff --check`: passed.

Mutants/formal evidence:
None required for Class B non-authority tooling.

Canonical hashes, dependencies, and protocol performance:
No changes.

Remaining gaps and non-claims:
No authenticated probe or paid request has run. The maintainer must enter the
temporary key locally; the next action is the free probe. Kimi review tooling
and any spending approval remain separate.
