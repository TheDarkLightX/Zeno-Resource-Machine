# Branch and release protection plan

The repository host must apply these controls to `main`:

- require pull requests and dismiss stale approvals;
- require the `quality`, `assurance`, `fuzz-smoke`, and `supply-chain` CI jobs;
- require CODEOWNER review for governed paths;
- require at least one approval from a non-author for Class C changes;
- require two distinct non-author approvals for Class D/E changes, including an
  authority-boundary reviewer;
- dismiss an approval when the approved head changes and require approval of
  the most recent reviewable push;
- block force pushes and branch deletion;
- require linear history;
- restrict direct pushes to maintainers;
- require conversation resolution;
- require signed or verified commits for release branches where supported.

Release environments must require maintainer approval. Private vulnerability reporting must be enabled in repository security settings.

These are host-side controls. Their presence must be verified through repository settings or API evidence before WP0 is described as fully implemented.

The checked-in `CODEOWNERS` file currently names one account. It provides path
ownership routing but cannot, by itself, prove independent semantic or
authority review. Class D/E promotion remains blocked until a second qualified
identity or team exists, the live rules require distinct approvals, and dated
repository-settings or API evidence confirms that maintainers cannot bypass
those rules. Static configuration and AI review receipts do not satisfy this
host-control requirement.
