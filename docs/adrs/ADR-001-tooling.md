# ADR-001: Tooling Decisions and Versions

## Status
Proposed

## Context

To ensure a consistent, modern, and reproducible development environment, the AutoGen MCP project standardizes on a set of Python tooling and workflows. This ADR documents the main tools, their purpose, and key configuration/versioning decisions.

## Decision

- **Poetry**: Used for Python dependency management and virtual environments. Chosen for its lockfile, reproducibility, and ease of use.
- **pytest**: Main test runner for unit, integration, and E2E tests. Chosen for its flexibility and ecosystem.
- **ruff**: Linter for fast, opinionated code linting. Enforced via pre-commit and CI.
- **black**: Code formatter for consistent Python style. Enforced via pre-commit and CI.
- **mypy**: Static type checker for Python. Ensures type safety and early error detection.
- **pre-commit**: Manages and runs hooks for linting, formatting, and other checks before commits.
- **Docker Compose**: Used for running Qdrant and other services locally for integration tests.
- **GitHub Actions**: CI/CD pipeline for lint, typecheck, tests, and scheduled jobs.

### Key Configuration
- Python version: 3.11+ (see `pyproject.toml`)
- All tools are configured in `pyproject.toml` or `.pre-commit-config.yaml`.
- CI runs all checks on push/PR; PRs require passing checks before merge.
- Developers must install pre-commit hooks locally (`poetry run pre-commit install`).

## Consequences
- Consistent development and CI environment for all contributors.
- Automated enforcement of code quality and style.
- Easy onboarding for new contributors.

## References
- `pyproject.toml`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `README.md`, `CONTRIBUTING.md`
