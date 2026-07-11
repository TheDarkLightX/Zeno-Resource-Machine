# Evidence records

This directory stores replayable, scoped assurance records. Execution records are immutable snapshots: later review decisions use new records instead of rewriting the historical result. A record reports its source revision, dirty-tree status, exact tool and command, result, assumptions, exclusions, and non-claims. A record never grants production authority by itself.

The WP1 local gate replay is recorded in `wp1-local-gates-2026-07-10.json`. The completed Class C human review is recorded separately in `wp1-class-c-review-2026-07-11.json`. The unreviewed WP2 candidate replay is recorded in `wp2-local-gates-2026-07-11.json`; that record does not promote WP2. Hosted release evidence remains a separate requirement.
