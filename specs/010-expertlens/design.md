# ExpertLens Design Specification
Version: 0.3.1
Last Updated: 2026-01-02
Change Notes:
- v0.3.1: Restructured for readability (no semantic changes)
- v0.3.0: Added Cytoscape.js as v1 Graph UI library
- v0.2.0: Refactored for v1 (CLI + file-based)
- v0.1.0: Initial version

---

## 1. System Overview

### 1.1 Architecture (v1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CLI Orchestrator                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 python -m expertlens <cmd>                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │              │              │               │             │
│         ▼              ▼              ▼               ▼             │
│  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐    │
│  │  Search   │  │  Evidence  │  │ Identity │  │ File Writer  │    │
│  │  Planner  │  │  Fetcher   │  │Resolution│  │  (JSON)      │    │
│  └───────────┘  └────────────┘  └──────────┘  └──────────────┘    │
│         │                                            │              │
│         ▼                                            ▼              │
│  ┌───────────────────────┐              ┌──────────────────────┐   │
│  │ DuckDuckGo Adapter    │              │  out/session-*.json  │   │
│  └───────────────────────┘              └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       LLM (External)                                 │
│  ┌───────────────────┐  ┌───────────────────┐                       │
│  │Requirement Clarifier│  │Evidence Extractor │                       │
│  └───────────────────┘  └───────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Frontend Viewer (Cytoscape.js)                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  frontend/index.html + app.js + graph.js + style.css         │   │
│  │  Graph: Cytoscape.js (CDN)                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Principle
> LLM handles interpretation/extraction only.
> Flow control, decisions, and storage are handled by CLI orchestrator.

---

## 2. End-to-End Flow

| Step | Action | Output |
|------|--------|--------|
| 1 | CLI Input | `session_id` |
| 2 | Clarification (LLM) | `PreferenceStack` |
| 3 | Search (DuckDuckGo) | `URL[]` |
| 4 | Evidence Fetch | `Evidence[]` |
| 5 | LLM Extraction | `PersonCandidate[]`, `StagingClaim[]` |
| 6 | Identity Resolution | `ResolutionDecision[]` |
| 7 | File Write | `out/session-*.json`, `reports/run-*.md` |
| 8 | Viewer | Graph UI + Detail Panel |

---

## 3. Data Contracts

### 3.1 Session JSON Schema

```json
{
  "session_id": "uuid",
  "language": "ko",
  "query": "배터리 소재 전문가",
  "queries": [{ "query": "...", "added_at": "ISO8601" }],
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "experts": [{
    "expert_id": "uuid",
    "canonical_name": "홍길동",
    "claims": [{
      "claim_type": "employment",
      "company": "삼성SDI",
      "company_id": "uuid",
      "role": "수석연구원",
      "evidence_id": "uuid"
    }],
    "evidence_ids": ["uuid"]
  }],
  "companies": [{
    "company_id": "uuid",
    "name": "삼성SDI",
    "domain": "samsungsdi.com",
    "region": "KR"
  }],
  "evidence": [{
    "evidence_id": "uuid",
    "url": "https://...",
    "platform": "linkedin",
    "retrieved_at": "ISO8601"
  }]
}
```

### 3.2 Entity Schemas

**Expert**:
| Field | Type |
|-------|------|
| expert_id | UUID |
| canonical_name | string |
| created_at | ISO8601 |
| updated_at | ISO8601 |

**Company**:
| Field | Type |
|-------|------|
| company_id | UUID |
| name | string |
| domain | string? |
| region | string? |

**Evidence**:
| Field | Type |
|-------|------|
| evidence_id | UUID |
| url | string |
| platform | string |
| retrieved_at | ISO8601 |

### 3.3 Claims (v1: 3 types)

**EmploymentClaim**: Expert ↔ Company (role, dates, evidence)
**ContactClaim**: Expert ↔ ContactPoint (status, evidence)
**MergeDecision**: Identity resolution audit log

### 3.4 Cytoscape.js Graph Format

```javascript
// Conversion: Session JSON → Cytoscape elements
{
  nodes: [
    { data: { id: "expert-1", label: "홍길동", type: "expert", evidenceCount: 3 } },
    { data: { id: "company-1", label: "삼성SDI", type: "company" } }
  ],
  edges: [
    { data: { source: "expert-1", target: "company-1", label: "수석연구원" } }
  ]
}
```

---

## 4. Frontend Architecture

### 4.1 File Structure

```
frontend/
├── index.html    # Main page (loads Cytoscape.js via CDN)
├── app.js        # Vanilla JS application
├── graph.js      # Cytoscape.js graph rendering
└── style.css     # Styling
```

### 4.2 Graph UI (Cytoscape.js)

**Constraint**: v1 uses Cytoscape.js **only**.

**Load Method**:
```html
<script src="https://unpkg.com/cytoscape@latest/dist/cytoscape.min.js"></script>
```

**Node Styling**:
| Type | Shape | Color | Size |
|------|-------|-------|------|
| Expert | Circle | `#4A90D9` | Maps to `evidenceCount` |
| Company | Rectangle | `#7B68EE` | Fixed |

**Interactions**:
- Node click → Update Detail Panel
- Zoom/Pan enabled
- Layout: `cose` (force-directed)

### 4.3 Detail Panel

Displays on node selection:
- Expert name
- Claims list (Employment, Contact)
- Evidence URLs (clickable, opens new tab)

---

## 5. Orchestrator (CLI)

### 5.1 Commands

```bash
# New session search
python -m expertlens search "배터리 전문가" --lang ko

# Add query to existing session
python -m expertlens session <id> --add-query "삼성SDI 경력자"

# List sessions
python -m expertlens list

# Help
python -m expertlens --help
```

### 5.2 Components

| Component | Responsibility | I/O |
|-----------|---------------|-----|
| **Search Planner** | Query generation | PreferenceStack → SearchQuery[] |
| **DuckDuckGo Adapter** | URL collection | SearchQuery → URL[] |
| **Evidence Fetcher** | Content extraction | URL[] → Evidence[] |
| **Evidence Extractor** (LLM) | Person/Claim extraction | Evidence → PersonCandidate[], Claim[] |
| **Identity Resolver** | Deduplication | PersonCandidate → ResolutionDecision |
| **File Writer** | JSON/MD output | Session → files |

### 5.3 Identity Resolution

**Blocking Keys**: LinkedIn URL, Email, Phone, Name+Company, Name+Education, Personal Site

**Thresholds**:
| Score | Action |
|-------|--------|
| ≥ 0.90 | Attach to existing Expert |
| 0.75–0.90 | Review (v1: treat as new) |
| < 0.75 | Create new Expert |

---

## 6. Non-goals / Deferred

| Item | Deferred To |
|------|-------------|
| Neo4j AuraDB | vNext |
| FastAPI Backend | vNext |
| React Frontend | vNext |
| WebSocket (real-time) | vNext |
| D3.js / force-graph | vNext |

---

## Appendix: Dev Environment

| Item | Technology |
|------|------------|
| Dev | Local + GitHub Codespaces |
| LLM | Hugging Face Inference API |
| Search | DuckDuckGo HTML |
| API | No-key open APIs only |
| Storage | JSON files |
| Frontend | Static HTML + Vanilla JS |
| Graph | **Cytoscape.js (CDN)** |
