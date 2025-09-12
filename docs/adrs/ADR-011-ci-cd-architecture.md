# ADR-011: CI/CD Architecture for AutoGen MCP

## Status
Proposed

## Context

To ensure code quality, security, and reliability, the AutoGen MCP project implements a comprehensive CI/CD pipeline using GitHub Actions. The pipeline covers linting, formatting, type checking, unit/integration testing (with Qdrant), and a nightly summarization job. All steps are required to pass before merging to `main`.

## Decision

- **CI Workflow**: Defined in `.github/workflows/ci.yml`.
- **Lint/Format/Typecheck**: Runs `ruff`, `black --check`, and `mypy` on every push and PR.
- **Tests**: Runs `pytest` with a live Qdrant service container.
- **Nightly Summarization**: Scheduled job runs the summarizer script nightly, writing summaries to memory.
- **Branch Protection**: PRs require all checks to pass before merge (enforced via GitHub settings).
- **Poetry**: All environments and dependencies managed via Poetry.
- **Artifacts**: Test results and logs are available in GitHub Actions UI.

## Consequences

- Ensures code quality and security for every change.
- Automated summarization keeps memory up to date.
- Contributors must ensure all checks pass before merging.
- Easy to extend for additional jobs (e.g., multi-version matrix, deployment).

## References
- `.github/workflows/ci.yml`
- `src/autogen_mcp/summarizer_nightly.py`
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
