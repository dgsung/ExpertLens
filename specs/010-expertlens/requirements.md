# ExpertLens Requirements
Version: 0.5.0
Last Updated: 2026-01-02
Change Notes:
- v0.5.0: Migrated v1 backend from CLI-only to FastAPI (thin wrapper over core)
- v0.4.0: Added Contact Evidence Policy (maximize collection, Claim vs Candidate)
- v0.3.1: Restructured for readability (no semantic changes)
- v0.3.0: Adopted Cytoscape.js as v1 Graph UI library
- v0.2.0: Added Pilot Delivery Mode (v1 Constraints) section
- v0.1.0: Initial version

---

## 1. Purpose & Success Criteria

### 1.1 What is ExpertLens?
Search-grounded Expert Discovery System that:
1. Structures user requirements into a Preference Stack
2. Collects evidence from public web searches
3. Normalizes experts into single Expert entities
4. Provides results via explainable UI

### 1.2 Success Criteria
- Every Expert/Company/Contact is traceable to Evidence URLs
- No invented facts without Evidence
- Users can understand *why* each expert was surfaced

---

## 2. Core Design Constraints

| Constraint | Decision |
|------------|----------|
| **Explainability** | All results must link to Evidence URLs |
| **Company Scope** | Variable: required / preferred / none |
| **Credibility vs Contactability** | Orthogonal signals (tracked separately) |
| **Contact Evidence** | Maximize collection within public scope; Claim only with URL verification |
| **Incremental Discovery** | Session-based, cumulative exploration |
| **Entity-Level ID** | Experts identified as individual persons |

### 2.1 Contact Evidence Policy

**원칙**: "최대한 찾되, 단정은 증거가 있을 때만"

**Claim vs Candidate 구분**:

| 유형 | 조건 | UI 라벨 |
|------|------|---------|
| **ContactClaim** | URL 확인 가능, 로그인 불필요 | "공개 확인됨" |
| **ContactCandidate** | 간접 신호, 약한 증거 | "외부 DB/간접 신호" |

**적극 포함 소스** (ContactClaim 생성 가능):
- 회사/연구소 공식 사이트 (Leadership, People, Contact 페이지)
- 개인 웹사이트/블로그 (Contact, About 페이지)
- Conference/Speaker 페이지
- GitHub (public email)
- Google Scholar / ResearchGate (공개 프로필)
- Medium / Substack (공개 연락 채널)
- 공개 소셜 (X, Facebook, Instagram) — 명시적 연락 채널이 있을 때만

**조건부 포함** (ZoomInfo, Apollo, Lusha):
- DuckDuckGo로 공개 인덱싱 페이지 발견: 허용
- 로그인 없이 연락 채널 명시적 노출 + URL 확인 가능: **ContactClaim 허용**
- 위 조건 미충족: **ContactCandidate only**
- 로그인/유료 벽 필요: Evidence URL 노출 금지, Claim 생성 금지

---

## 3. User Experience

### 3.1 Session Management
- Session-scoped exploration state
- Evidence/Expert accumulation across queries
- Session file switching (file-based in v1)

### 3.2 Graph UI (Cytoscape.js)
**v1 Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│                      Session Selector                        │
├─────────────────────────────┬───────────────────────────────┤
│      Graph UI               │        Detail Panel           │
│  (Cytoscape.js)             │  - Expert Info                │
│  - Expert nodes             │  - Claims (Employment/Contact)│
│  - Company nodes            │  - Evidence URLs              │
│  - Employment edges         │                               │
└─────────────────────────────┴───────────────────────────────┘
```

**v1 Graph Features**:
- Expert nodes (size reflects evidence count)
- Company nodes
- Employment edges
- Node click → Detail Panel sync

### 3.3 Detail Panel
- Expert info display
- Claims (Employment, Contact)
- Evidence URL links (clickable)

### 3.4 Language Policy
| Rule | Description |
|------|-------------|
| Input = Output | Response language matches query language |
| Session-scoped | `session.language` maintained per session |
| LLM calls | `output_language` always specified |

---

## 4. Pilot Delivery Mode (v1)

### 4.1 v1 Scope
Focus: **Explainability validation** with minimal implementation.

### 4.2 v1 Constraints

| Component | v1 Decision | vNext |
|-----------|-------------|-------|
| **Database** | None (JSON files) | SQLite/PostgreSQL |
| **Backend** | FastAPI (thin wrapper over core) | - |
| **Frontend** | Static HTML + Vanilla JS | React/Next.js |
| **Graph UI** | **Cytoscape.js only** | D3.js, force-graph |

**Backend Architecture**:
- FastAPI는 orchestrator core의 thin wrapper
- 비즈니스 로직은 `src/expertlens/core/` 모듈에만 존재
- API 라우트는 core 함수 호출만 담당

### 4.3 v1 Outputs

| Output | Path | Description |
|--------|------|-------------|
| Session JSON | `out/session-<id>.json` | Machine-readable |
| Evidence JSON | `out/evidence/<id>.json` | Optional |
| Run Report | `reports/run-<ts>.md` | Human-readable |

### 4.4 v1 Graph Library

| Library | v1 | Reason |
|---------|-----|--------|
| **Cytoscape.js** | **Yes** | Vanilla JS compatible, CDN loadable |
| D3.js | No | Low-level, steep learning curve |
| force-graph | No | WebGL complexity |
| vis.js | No | Not considered |

---

## 5. Out of Scope (vNext)

| Item | Description |
|------|-------------|
| User Auth | Per-user session isolation |
| UX Optimization | Graph stabilization, progressive rendering |
| Performance | Caching, batching, indexing |
| Review UI | Merge decision review interface |
| Export | CRM integration |
| Advanced Graph | D3.js, force-graph alternatives |
| Database | Persistent storage (SQLite/PostgreSQL) |
| Frontend Framework | React/Next.js |
