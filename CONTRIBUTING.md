# Contributing

Thanks for contributing! This project uses Poetry for dependency and environment management.

## Getting started

1. Install Poetry: https://python-poetry.org/docs/
2. Use Python 3.11+
3. After cloning, run:
   - `poetry install`
   - `poetry run pytest`

## Branching and commits

- Create a feature branch per step: `feature/<step-number>-<slug>`
- Use conventional commits, reference step: `feat(scope): summary [#step-N]`

## Pre-commit

We use pre-commit to enforce formatting and linting. After we add tooling in Step 2:
- `poetry run pre-commit install`

## PRs

- Open a PR against `main`
- Ensure all checks pass
- Use the PR template and complete the acceptance checklist
