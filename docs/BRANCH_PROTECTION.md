# Branch and release protection plan

The repository host must apply these controls to `main`:

- require pull requests and dismiss stale approvals;
- require the `quality`, `assurance`, `fuzz-smoke`, and `supply-chain` CI jobs;
- require CODEOWNER review for governed paths;
- block force pushes and branch deletion;
- require linear history;
- restrict direct pushes to maintainers;
- require conversation resolution;
- require signed or verified commits for release branches where supported.

Release environments must require maintainer approval. Private vulnerability reporting must be enabled in repository security settings.

These are host-side controls. Their presence must be verified through repository settings or API evidence before WP0 is described as fully implemented.
