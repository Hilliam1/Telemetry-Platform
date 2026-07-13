# Contributing

This repository is structured like an engineering project. Contributions should keep the code, documentation, and architecture easy to understand for future maintainers.

## Standards

- Keep secrets out of Git.
- Use `.env.example` for configuration examples.
- Keep generated files, caches, logs, and local state files untracked.
- Prefer small, focused commits.
- Document major design decisions in `docs/adr/`.
- Update the README or docs when behavior changes.

## Branch Strategy

- `main` contains stable project work.
- Feature work should happen in short-lived branches.
- Pull requests should explain the reason for the change and how it was tested.

## Testing Expectations

Future test coverage should include:

- Collector parsing tests
- API endpoint tests
- Database insert tests
- Event normalization tests
- Integration tests for common deployment paths

