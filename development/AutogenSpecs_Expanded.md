# Expanded Autogen Agent & Memory Integration Specs

This document expands on the initial specification for integrating AutoGen into VSCode with Qdrant-based memory and agile multi-agent workflows. It reflects requirements we already discussed and adds clarifications and details that were not explicitly noted but are essential for a complete setup.

---

## Memory Scopes and Structure
Qdrant will be used as a single memory fabric with multi-scope payload fields. The scopes include:

- **Global**: coding standards, security rules, reusable solutions.
- **Project**: architecture decisions (ADRs), APIs, dataset notes, known issues.
- **Agent**: preferences, style, skills, capabilities.
- **Thread**: conversations, micro-decisions, TODOs.
- **Objectives/Progress**: sprint goals, OKRs, milestones, status updates.
- **Artifacts**: commits, PRs, build tags, test reports.

---

## Retrieval and Write Policy
Agents must:

- Search tiered (thread → project → objectives → agent → global) before work.
- Write results after each turn (decision, snippet, artifact links).
- Summarize long threads every 20–30 turns.
- Maintain per-project collections while also leveraging the global memory.
- Use hybrid search (dense embeddings + sparse BM25/TF-IDF) for code/text.

---

## Agent Lifecycle and Roles
Agents will be created dynamically as needed for each project. Roles include:

- **Agile/ScrumMaster agent**: orchestrates planning, reviews, retrospectives.
- **Planner**: breaks down epics into tasks with acceptance criteria.
- **Architect**: designs system structure and validates interfaces.
- **Coder**: implements code in dedicated feature branches.
- **Reviewer**: enforces standards and Definition of Done.
- **Tester**: validates merges into main branch before approval.
- **DevOps**: builds, containers, CI/CD pipeline.
- **Doc**: updates README, API docs, changelog.
- **Optional UX agent**: wireframes and flows.

---

## Version Control Workflow
- Each agent works in its own branch.
- The Agile agent commits and pushes the working branch.
- The Tester validates merges into main before approval.
- Only after tests pass does the main branch get updated.
- Artifacts (commits, PRs, build reports) are stored in memory as references.

---

## LLM Configuration
- Default: one cloud model (Gemini for testing).
- Offline models supported (Ollama, LM Studio, vLLM) but not used in development initially.
- Determinism enforced with `temperature=0` for code and review agents.
- Timeouts and `max_rounds` configured per agent.
- Embeddings for Qdrant memory are separate from chat models (FastEmbed or local embedding models).

---

## VSCode Integration
- The AutoGen MCP server runs inside the folder opened in VSCode.
- Agents write code directly into this folder.
- Interface for controlling AutoGen and interacting with agents is native VSCode.
- Repo growth, branch creation, and GitHub commits are visible directly in VSCode.

---

## Additional Considerations
- **Security**: store only references to secrets, not raw values.
- **Observability**: log tool calls, memory searches, and commit actions.
- **Objectives & progress updates** written into memory to allow sprint tracking.
- **Automatic nightly summarization** and pruning of low-importance memory items.
- Potential **dashboard (CLI or web)** for visualizing memory state (objectives, todos, artifacts).
