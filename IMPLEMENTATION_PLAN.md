# AutoGen + Qdrant + VS Code MCP — Implementation Plan (Poetry)

This plan tracks progress step-by-step, using Poetry for the Python environment and a strict branch → commit → test → your manual test → fix → merge-to-main cadence. Check off each box as we complete items.

Notes
- Environment manager: Poetry (Python 3.11+ recommended)
- Vector DB: Qdrant (Docker)
- Embeddings: FastEmbed (local) initially
- LLM: Cloud (Gemini) for testing; set via environment variables (never store secrets)
- Editor: VS Code; agents write to the open workspace
- Git policy: per-agent/per-step branches, PRs, required checks

Conventions
- Branch name per step: `feature/<step-number>-<slug>`
- Conventional commits referencing step: `feat(scope): summary [#step-N]`
- Artifacts and decisions are written to memory and documented via ADRs in `docs/adrs/`

---

## Prerequisites
- [ ] Poetry installed and configured
- [ ] Docker available to run Qdrant locally
- [x] GitHub remote set up with push access
- [ ] VS Code installed with Python, Docker extensions (optional)
- [ ] Cloud LLM credentials configured via environment variables (secrets not committed)

---

## Repeatable workflow per step
- [ ] Create branch: `feature/<step-number>-<slug>`
- [ ] Implement only the scope for this step
- [ ] Commit and push (include step reference in commit message)
- [ ] Run local automated tests (lint, typecheck, unit/integration as applicable)
- [ ] You perform manual testing; provide feedback
- [ ] Address feedback with additional commits; push
- [ ] Open PR, ensure CI passes; merge to `main`; push `main`
- [ ] Record artifacts (commit SHAs, PR URLs, CI run IDs) in memory and ADRs

---

## Step 1 — Bootstrap repository and governance (Poetry-aware)
- Branch: `feature/01-bootstrap`
- Scope:
  - [ ] Initialize repo structure (src/, tests/, docs/, .github/)
  - [x] Add LICENSE, README, CODEOWNERS, pull request template
  - [x] Add .gitignore (Python/Poetry/VS Code)
  - [x] Configure default branch `main` and GitHub remote
  - [x] Document Poetry usage in README (install, env, run tests)
- Acceptance:
  - [ ] Clean initial repo; README outlines goals/architecture/workflow and Poetry usage
  - [ ] CODEOWNERS and basic contribution rules present
- Tests:
  - [ ] Lint/format placeholder runs
  - [ ] README links resolve
- Artifacts to memory:
  - [ ] ADR-000: Tech stack and governance choices

## Step 2 — Project scaffold and tooling (Poetry)
- Branch: `feature/02-scaffold-tooling`
- Scope:
  - [x] Create `pyproject.toml` (Poetry) with deps: ruff, black, mypy, pytest, pre-commit
  - [x] Set up `src/` layout with minimal CLI entry (e.g., `autogen_mcp/cli.py`)
  - [x] Configure pre-commit hooks (black, ruff, end-of-file-fixer, trailing-whitespace)
  - [x] Basic pytest structure in `tests/` and typechecking config
- Acceptance:
  - [x] Poetry install succeeds; `pytest` runs and passes
  - [x] Ruff/Black/Mypy clean on scaffold
  - [x] Pre-commit prevents formatting/lint violations locally
- Tests:
  - [x] Unit: trivial test passes
  - [x] Lint: ruff clean
  - [x] Typecheck: mypy clean
- Artifacts:
  - [ ] ADR-001: Tooling decisions and versions

## Step 3 — Qdrant setup and schema
- Branch: `feature/03-qdrant-schema`
- Scope:
  - [x] `docker-compose.yml` for Qdrant local
  - [x] Python Qdrant client wrapper (health, list, create, upsert, search)
  - [ ] Define multi-scope memory model: global/project/agent/thread/objectives/artifacts
  - [ ] Per-project collections naming convention
- Acceptance:
  - [x] Qdrant starts and health endpoint responds
  - [ ] Collections created with required payload schema
  - [x] Wrapper can upsert/query a simple record
- Tests:
  - [x] Integration: compose up, create collections, upsert/query per scope
  - [x] Error handling: unavailable Qdrant surfaces clear errors (status text logged)
- Artifacts:
  - [ ] ADR-002: Memory schema and naming conventions

## Step 4 — Embeddings integration (dense)
- Branch: `feature/04-embeddings-dense`
- Scope:
  - [x] Integrate FastEmbed (local)
  - [x] Encoder service abstraction
  - [ ] Health checks for encoder service
  - [x] Store vectors alongside payload in Qdrant
- Acceptance:
  - [ ] `encode(text)` returns deterministic vector shape
  - [x] Vector search retrieves similar items (roundtrip test)
  - [ ] Health endpoint returns OK
- Tests:
  - [ ] Unit: encoder determinism
  - [x] Integration: encode-store-query roundtrip
  - [ ] Perf: simple timing budget locally
- Artifacts:
  - [ ] ADR-003: Embeddings provider and parameters

## Step 5 — Hybrid search (dense + sparse)
- Branch: `feature/05-hybrid-search`
- Scope:
  - [x] Sparse TF-IDF index
  - [x] Hybrid fusion (Reciprocal Rank Fusion)
  - [ ] Tiered search order: thread → project → objectives → agent → global
- Acceptance:
  - [ ] `search(query, scopes, k)` returns results with scores and scope metadata
  - [x] Cases where sparse wins and dense wins; fusion improves top-k (integration test)
- Tests:
  - [x] Unit: fusion math and ties
  - [x] Integration: index build + hybrid search on sample corpus
  - [ ] Edge: empty corpus, long query, stop words
- Artifacts:
  - [ ] ADR-004: Retrieval and fusion strategy

## Step 6 — Memory write policies and summarization
- Branch: `feature/06-write-policy`
- Scope:
  - [ ] Per-turn write hooks (decisions/snippets/artifacts)
  - [x] Thread summarization after N turns (naive local) + [ ] nightly summarizer
  - [ ] Per-project collections enforcement and pruning
- Acceptance:
  - [x] `memory.write(event)` persists to correct scope
  - [x] Summarization creates linked summaries (summary event with references)
- Tests:
  - [ ] Unit: policy rule enforcement
  - [ ] Integration: 30-turn simulation → summary exists with references
  - [ ] Pruning: low-importance items flagged/archived
- Artifacts:
  - [ ] ADR-005: Write policy and thresholds

## Step 7 — AutoGen agents scaffolding
- Branch: `feature/07-agents-gemini-integration`
- Scope:
  - [x] Define agents: Agile, Planner, Architect, Coder, Reviewer, Tester, DevOps, Doc
  - [x] Role prompts and defaults (temperature=0 for code/review)
  - [x] max_rounds/timeouts per role
  - [x] Orchestrator to instantiate agents per project
- Acceptance:
  - [x] CLI dry-run with mocked LLM (canned responses)
  - [x] Agents perform tiered reads and per-turn writes
- Tests:
  - [x] Unit: role configs load and validate
  - [x] Integration: orchestrator runs 2–3 rounds with stubs
  - [x] Edge: timeouts, cancellation
- Artifacts:
  - [x] ADR-006: Agent roles and guardrails

## Step 8 — VS Code MCP server integration
- Branch: `feature/08-mcp-server`
- Scope:
  - [x] MCP server running in workspace folder
  - [x] Commands: start/stop orchestration, memory.search, objective.add
  - [x] Minimal VS Code interface wiring
- Acceptance:
  - [x] From VS Code, start a short session; files written to workspace
  - [x] Commands return structured JSON and handle errors
- Tests:
  - [x] Manual: invoke commands, verify effects
  - [x] Integration: MCP endpoints → expected responses
- Artifacts:
  - [x] ADR-007: MCP endpoints and commands

## Step 9 — Git branching and artifacts
- Branch: `feature/09-git-workflow`
- Scope:
  - [x] Automation for per-agent branch creation and commit/push
  - [x] PR creation with templates and checklists
  - [x] Store commit SHAs, PR URLs, CI run IDs in memory
- Acceptance:
  - [x] Branch/commit/push automated wrapper
  - [x] PRs created; checks required before merge
- Tests:
  - [x] Dry-run mode simulating git/PR ops locally
  - [x] Live test on repo (non-destructive)
- Artifacts:
  - [x] ADR-008: Git policy and artifact linkage

## Step 10 — Observability and tracing
- Branch: `feature/10-observability`
- Scope:
  - [ ] Structured logging for tool calls, memory ops, commits
  - [ ] Optional OpenTelemetry hooks
  - [ ] Correlation IDs across layers
- Acceptance:
  - [ ] Logs trace a full agent turn with timings
  - [ ] Verbosity configurable
- Tests:
  - [ ] Unit: logger adapters
  - [ ] Integration: session log inspection
- Artifacts:
  - [ ] ADR-009: Observability choices

## Step 11 — Security and data hygiene
- Branch: `feature/11-security`
- Scope:
  - [ ] Secret redaction in logs and memory
  - [ ] Outbound call/domain allowlist
  - [ ] Payload filters block secrets storage
- Acceptance:
  - [ ] Secrets never stored/logged; violations blocked with warnings
  - [ ] Allowlist enforced for tools
- Tests:
  - [ ] Unit: redaction and filters
  - [ ] Integration: attempt secret write → blocked
  - [ ] E2E: disallowed outbound call → policy error
- Artifacts:
  - [ ] ADR-010: Security posture

## Step 12 — CI/CD pipelines and schedules
- Branch: `feature/12-ci`
- Scope:
  - [ ] GitHub Actions: lint, typecheck, unit/integration
  - [ ] Qdrant service container for tests
  - [ ] Nightly summarization scheduled workflow
- Acceptance:
  - [ ] PRs require passing checks before merge
  - [ ] Nightly job runs summarizer and writes to memory
- Tests:
  - [ ] Matrix job runs on push/PR
  - [ ] Cron triggers and updates memory artifacts
- Artifacts:
  - [ ] ADR-011: CI/CD architecture

## Step 13 — Docs and minimal dashboard
- Branch: `feature/13-docs-dashboard`
- Scope:
  - [ ] Expand README and CONTRIBUTING with Poetry workflows
  - [ ] ADR index and changelog
  - [ ] Minimal CLI dashboard: objectives, todos, artifacts by scope
- Acceptance:
  - [ ] Docs guide a new contributor from clone → run
  - [ ] Dashboard shows objectives and latest artifacts
- Tests:
  - [ ] Docs lint (optional)
  - [ ] Dashboard returns expected output against seeded memory
- Artifacts:
  - [ ] ADR-012: Docs strategy and dashboard scope

---

## Status Snapshot
- [x] Step 1 — Bootstrap repository and governance
- [x] Step 2 — Project scaffold and tooling
- [x] Step 3 — Qdrant setup and schema
- [x] Step 4 — Embeddings integration (dense)
- [x] Step 5 — Hybrid search (dense + sparse)
- [ ] Step 6 — Memory write policies and summarization
- [x] Step 7 — AutoGen agents scaffolding
- [x] Step 8 — VS Code MCP server integration
- [x] Step 9 — Git branching and artifacts
- [ ] Step 10 — Observability and tracing
- [ ] Step 11 — Security and data hygiene
- [ ] Step 12 — CI/CD pipelines and schedules
- [ ] Step 13 — Docs and minimal dashboard

---

## Change log (append entries as we progress)
- 2024-06-08: Step 7 (AutoGen agents scaffolding, Gemini integration, CLI) completed and merged from 'feature/07-agents-gemini-integration'.
- 2025-09-12: Step 8 (VS Code MCP server integration) completed and merged from 'feature/08-mcp-server'.
- 2025-09-12: Step 9 (Git workflow automation, PR/commit/CI artifact linkage) completed and merged from 'feature/09-git-workflow'.
