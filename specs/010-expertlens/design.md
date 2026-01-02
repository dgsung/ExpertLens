# ExpertLens Design Specification
Version: 0.5.0
Last Updated: 2026-01-02
Change Notes:
- v0.5.0: Migrated v1 backend to FastAPI (thin wrapper over core)
- v0.4.0: Added Contact Evidence Strategy (platform rules, Claim vs Candidate)
- v0.3.1: Restructured for readability (no semantic changes)
- v0.3.0: Added Cytoscape.js as v1 Graph UI library
- v0.2.0: Refactored for v1 (CLI + file-based)
- v0.1.0: Initial version

---

## 1. System Overview

### 1.1 Architecture (v1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Frontend Viewer (Cytoscape.js)                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  frontend/index.html + app.js + graph.js + style.css         │   │
│  │  Graph: Cytoscape.js (CDN)                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │ fetch() API calls
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI (thin wrapper)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  POST /sessions  │  POST /sessions/{id}/run  │  GET /sessions │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                    │                                │
│                           core.run_session()                        │
│                                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Core Orchestrator                          │   │
│  │  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐  │   │
│  │  │  Search   │  │  Evidence  │  │ Identity │  │ File I/O │  │   │
│  │  │  Planner  │  │  Fetcher   │  │Resolution│  │  (JSON)  │  │   │
│  │  └───────────┘  └────────────┘  └──────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                │                                    │                │
│                ▼                                    ▼                │
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
```

### 1.2 Core Principle
> LLM handles interpretation/extraction only.
> Flow control, decisions, and storage are handled by Core Orchestrator.
> FastAPI is thin wrapper over core — no business logic in API routes.

---

## 2. End-to-End Flow

| Step | Action | Output |
|------|--------|--------|
| 1 | API Request (`POST /sessions`) | `session_id` |
| 2 | API Request (`POST /sessions/{id}/run`) | trigger orchestrator |
| 3 | Clarification (LLM) | `PreferenceStack` |
| 4 | Search (DuckDuckGo) | `URL[]` |
| 5 | Evidence Fetch | `Evidence[]` |
| 6 | LLM Extraction | `PersonCandidate[]`, `StagingClaim[]` |
| 7 | Identity Resolution | `ResolutionDecision[]` |
| 8 | File Write | `out/session-*.json`, `reports/run-*.md` |
| 9 | API Response | Session JSON |
| 10 | Viewer | Graph UI + Detail Panel |

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

#### 3.3.1 Contact Evidence Strategy

**원칙**: 공개 범위에서 최대 수집, URL 확인 가능할 때만 Claim 생성

**플랫폼별 허용 규칙**:

| Platform | 허용 조건 | 결과 |
|----------|-----------|------|
| 회사/연구소 공식 사이트 | 공개 Leadership/People/Contact 페이지 | **ContactClaim** |
| 개인 웹사이트/블로그 | 공개 Contact/About 페이지 | **ContactClaim** |
| Conference/Speaker 페이지 | 공개 프로필 | **ContactClaim** |
| GitHub | public email 노출 | **ContactClaim** |
| Google Scholar / ResearchGate | 공개 프로필 | **ContactClaim** |
| Medium / Substack | 공개 연락 채널 | **ContactClaim** |
| LinkedIn | 공개 프로필 + 명시적 연락 채널 | **ContactClaim** |
| X (Twitter) / Facebook / Instagram | 명시적 연락 채널 있을 때만 | **ContactClaim** |
| ZoomInfo / Apollo / Lusha | 로그인 없이 노출 + URL 확인 가능 | **ContactClaim** |
| ZoomInfo / Apollo / Lusha | 로그인/유료 벽 필요 | **ContactCandidate** |
| ZoomInfo / Apollo / Lusha | 로그인 필수 + URL 노출 불가 | **수집 제외** |

**발견 방식**:
- DuckDuckGo 검색으로 공개 인덱싱 페이지 발견: 허용
- 로그인/유료 페이지 우회 시도: 금지

**UI 라벨링**:

| 유형 | 라벨 | 설명 |
|------|------|------|
| ContactClaim | "공개 확인됨" | 공개 페이지에서 확인된 연락 채널 |
| ContactCandidate | "외부 DB/간접 신호" | 외부 데이터베이스 또는 간접적 신호 |

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

## 5. API Layer (FastAPI)

### 5.1 Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/sessions` | Create new session | `{ language: string }` | `{ session_id: string }` |
| GET | `/sessions/{id}` | Get session status | - | `Session` |
| POST | `/sessions/{id}/run` | Run search | `{ query: string }` | `Session` |
| GET | `/sessions/{id}/stream` | SSE progress | - | `Event stream` |
| GET | `/healthz` | Health check | - | `{ status: "ok" }` |

### 5.2 Core Module

**Entry Point**: `core.run_session(session_id, query) -> SessionResult`

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

### 5.4 CLI (Legacy)

CLI는 개발/디버깅용으로 유지:

```bash
# Direct core invocation (for debugging)
python -m expertlens search "배터리 전문가" --lang ko
```

---

## 6. Non-goals / Deferred

| Item | Deferred To |
|------|-------------|
| Neo4j AuraDB | vNext |
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
