# ExpertLens — Claude Code Operating Manual
Version: 1.2.1
Last Updated: 2026-01-02
Owner: Donggi Sung
Change Notes:
- v1.2.1: Restructured for readability (no semantic changes)
- v1.2.0: Adopted Cytoscape.js as v1 Graph UI library
- v1.1.0: Added v1 Pilot Constraints section (DB/backend/frontend framework restrictions)
- v1.0.0: Initial operating manual

---

## 1. Document Roles

### SSOT (Single Source of Truth)
- **Progress tracker**: `specs/010-expertlens/tasks.md` (SSOT)
- requirements.md and design.md define intent/architecture
- tasks.md defines executable milestones

### Canonical Spec Files
| File | Purpose |
|------|---------|
| `specs/010-expertlens/requirements.md` | Product requirements |
| `specs/010-expertlens/design.md` | Implementation design |
| `specs/010-expertlens/tasks.md` | Milestones & progress |

---

## 2. Core Principles (Non-negotiables)

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Explainability-by-default** | All Expert/Company/Contact traceable to Evidence URLs. No invented facts. |
| 2 | **Company scope is variable** | Required / bonus / irrelevant (not fixed) |
| 3 | **Orthogonal signals** | Credibility and contactability tracked separately |
| 4 | **Incremental discovery** | Work in milestones; each produces demoable increment + report |

---

## 3. v1 Pilot Constraints (Mandatory)

The following constraints are **MANDATORY** for v1. Violation requires explicit owner approval.

### 3.1 No Database (v1)
- Do NOT use SQLite, PostgreSQL, or any database.
- All data stored as JSON files in `out/` directory.

**Standard outputs**:
| Output | Path |
|--------|------|
| Session JSON | `out/session-<session_id>.json` |
| Evidence JSON | `out/evidence/<evidence_id>.json` (optional) |
| Run Report | `reports/run-<timestamp>.md` |

### 3.2 No Backend Framework (v1)
- Do NOT use FastAPI, Express, Flask, or any HTTP server framework.
- Python orchestrator runs as **CLI only**.
- Entry point: `python -m expertlens <command>`
- Input via CLI arguments; output via file artifacts.

### 3.3 No Frontend Framework (v1)
- Do NOT use React, Vue, Svelte, Next.js, Angular, or any frontend framework.
- Frontend is a **static HTML viewer** (`frontend/index.html`).
- Vanilla JavaScript only. No build step.
- Viewer reads `out/session-*.json` files.

### 3.4 Graph UI: Cytoscape.js Only (v1)
- v1 Graph UI uses **Cytoscape.js** only.
- Do NOT use D3.js, force-graph, vis.js, or other graph libraries in v1.
- Load via CDN: `https://unpkg.com/cytoscape@latest/dist/cytoscape.min.js`
- Alternative graph libraries deferred to vNext.

### 3.5 Changing These Constraints
To modify any constraint:
1. Discuss with owner (Donggi Sung)
2. Document rationale in requirements.md
3. Update all affected spec files
4. Get explicit approval before implementation

---

## 4. Workflow Rules

### 4.1 Document Versioning (Required)
Every spec file MUST include a header block:
```
Version: X.Y.Z
Last Updated: YYYY-MM-DD
Change Notes: short bullet list
```

**Versioning rule**:
| Change Type | Version Bump |
|-------------|--------------|
| Core principles/architecture direction | MAJOR |
| Feature scope/flow changes | MINOR |
| Clarification/typos/reformatting | PATCH |

### 4.2 Planner Auto-Sync (Critical)
The planner MUST continuously keep tasks.md aligned with requirements/design:

**On every planning request**:
1. Read requirements.md and design.md
2. Inspect recent changes: `git diff -- specs/010-expertlens`
3. Update tasks.md accordingly:
   - Add new milestones/tasks when new requirements appear
   - Adjust acceptance criteria/tests/deliverables when specs change
   - Mark out-of-scope explicitly if removed

**Rule**: If a new requirement implies work not in tasks.md, create tasks immediately (do not wait).

### 4.3 Milestone Discipline (Execution Gate)
For each milestone:
1. Implement ONLY the milestone scope from tasks.md
2. Run tests (or document why tests are not available)
3. Produce report: `reports/milestone-<id>.md`
4. Only then commit

### 4.4 Git Rules
| Rule | Description |
|------|-------------|
| Commit format | `milestone(<id>): <short summary>` |
| Commit gate | Only commit when tests pass (unless tasks.md allows otherwise) |

---

## 5. Reporting Format (Required)

Every milestone report MUST include:
- Goal (1–2 sentences)
- Completed tasks
- How to run/demo (commands)
- Test results (pass/fail + key logs)
- Notable changes (files/modules)
- Risks / follow-ups
- Link to updated tasks.md milestone section

---

## 6. Safety

- Never read, print, or commit secrets (.env, credentials, API keys).
- If a feature requires secrets, stop and propose a safe approach.

---

## 7. Commands

| Command | Description |
|---------|-------------|
| `pytest tests/` | Run tests |
| `python -m expertlens search "<query>" --lang ko` | CLI search |
| `python -m http.server -d frontend 8080` | Viewer server |
| (TBD) | Lint/Format |
