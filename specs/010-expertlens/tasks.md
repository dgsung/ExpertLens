# Tasks / Milestones — ExpertLens
Version: 0.5.0
Last Updated: 2026-01-02
Change Notes:
- v0.5.0: Migrated v1 to FastAPI-based architecture; added M010-4~7 (API milestones)
- v0.4.0: Added Contact Evidence Policy references, M010-10 (Contact Enhancement)
- v0.3.1: Added Cytoscape.js to M010-3, added Quick Reference, restructured for consistency
- v0.2.0: Restructured milestones for v1 (CLI + file-based, no DB/framework)
- v0.1.0: Initialized milestone plan with parseable metadata fields.

---

## Overview

v1은 **FastAPI 기반** + 파일 저장 + Cytoscape.js viewer로 **설명 가능성(Explainability)** 검증에 집중한다.

```
CLI Pilot (archived)          API-based v1 (current)
M010-0 → M010-1 → M010-2 → M010-3    M010-4 → M010-5 → M010-6 → M010-7
 CLI     Mock      LLM      Static    FastAPI  Sessions  Run+Core Frontend
Scaffold Search   Extract   Viewer    Scaffold   API    Endpoint  API Int.
```

---

## Quick Reference

### v1 API Milestones (Current)

| Milestone | Status | Key Deliverable |
|-----------|--------|-----------------|
| M010-4 | DONE | FastAPI scaffold + `/healthz` 동작 |
| M010-5 | DONE | `POST /sessions`, `GET /sessions/{id}` 구현 |
| M010-6 | DONE | `POST /sessions/{id}/run` + core orchestrator 연동 |
| M010-7 | TODO | Frontend fetch() API 호출 |

### CLI Pilot (Archived)

| Milestone | Status | Key Deliverable |
|-----------|--------|-----------------|
| M010-0 | DONE | `python -m expertlens --help` 동작 |
| M010-1 | DONE | Session JSON schema validation 통과 |
| M010-2 | DONE | Expert → Claim → Evidence 역추적 가능 |
| M010-3 | DONE | 브라우저에서 Graph UI + Detail Panel 표시 |

---

## Milestone Metadata Format

각 마일스톤은 아래 형식의 parseable metadata를 포함한다:

```markdown
- **Status**: TODO | IN_PROGRESS | BLOCKED | DONE
- **Report**: reports/milestone-010-X.md
- **Commit**: (pending) | <sha>
- **Owner**: (pending) | <name>
```

---

## M010-0: CLI Scaffold + File Outputs

**Goal**: CLI entrypoint 설정, out/reports 디렉토리 구조 생성

- **Status**: DONE
- **Report**: reports/milestone-010-0.md
- **Commit**: 39ec5d5
- **Owner**: (pending)

### Deliverables

```
src/
└── expertlens/
    ├── __init__.py
    ├── __main__.py          # CLI entry point (argparse)
    ├── orchestrator.py      # Pipeline skeleton
    └── io/
        ├── __init__.py
        └── writer.py        # JSON/MD file writer
out/
└── .gitkeep
reports/
└── .gitkeep
```

### Done Definition

- [x] `python -m expertlens --help` 실행 시 도움말 출력
- [x] `python -m expertlens search "test" --lang ko` 실행 시 `out/session-<uuid>.json` 생성 (빈 skeleton)
- [x] `reports/run-<timestamp>.md` 생성 (빈 skeleton)
- [x] CLI 에러 핸들링 (잘못된 인자 시 명확한 에러 메시지)

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Manual | `--help`, `search` 명령 실행 확인 |
| Unit | `writer.py`의 파일 생성 로직 테스트 (pytest) |

### Risks / Notes

- 아직 실제 검색/추출 로직 없음 (mock only)

---

## M010-1: Mock Search → Session JSON

**Goal**: 하드코딩/mock 검색으로 session JSON 생성, schema 검증

- **Status**: DONE
- **Report**: reports/milestone-010-1.md
- **Commit**: 34a4c2e
- **Owner**: (pending)

### Deliverables

```
src/
└── expertlens/
    ├── search/
    │   ├── __init__.py
    │   ├── planner.py       # Query generation (stub)
    │   └── mock.py          # Mock search results
    ├── models/
    │   ├── __init__.py
    │   ├── session.py       # Session dataclass
    │   ├── expert.py        # Expert/Claim dataclass
    │   └── evidence.py      # Evidence dataclass
    └── io/
        └── writer.py        # Updated: full session JSON write
out/
└── session-<uuid>.json      # Generated sample
```

### Done Definition

- [x] `python -m expertlens search "배터리 전문가" --lang ko` 실행
- [x] `out/session-<uuid>.json` 생성됨
- [x] JSON 필드: `session_id`, `language`, `query`, `queries[]`, `created_at`, `updated_at`, `experts[]`, `evidence[]`
- [x] Mock expert 최소 2명, mock evidence 최소 3개 포함
- [x] JSON schema validation 통과 (jsonschema 또는 pydantic)

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Unit | Session JSON schema validation |
| Unit | `mock.py` 반환값 검증 |
| Manual | 생성된 JSON 파일 직접 확인 |

### Risks / Notes

- Mock 데이터는 실제 검색 결과 아님 (하드코딩)
- Evidence URL은 placeholder (예: `https://example.com/evidence/1`)

---

## M010-2: Minimal Extraction + Evidence Traceability

**Goal**: LLM 추출 (Claim 3종) 구현, evidence URL 역추적 확인

- **Status**: DONE
- **Report**: reports/milestone-010-2.md
- **Commit**: d359f7f
- **Owner**: (pending)

### Deliverables

```
src/
└── expertlens/
    ├── llm/
    │   ├── __init__.py
    │   ├── client.py        # LLM API client (HuggingFace)
    │   └── extractor.py     # Evidence → PersonCandidate + Claims
    ├── identity/
    │   ├── __init__.py
    │   └── resolver.py      # Simple identity resolution
    └── evidence/
        ├── __init__.py
        └── fetcher.py       # URL fetch + content extraction
out/
├── session-<uuid>.json      # With real extracted data
└── evidence/
    └── <evidence_id>.json   # Optional: individual evidence
```

### Done Definition

- [x] 실제 URL에서 콘텐츠 fetch (최소 1개 테스트 URL)
- [x] LLM으로 PersonCandidate 추출
- [x] EmploymentClaim, ContactClaim 생성
- [x] Expert.claims[].evidence_id → Evidence.url 연결 확인 가능
- [x] `reports/run-<timestamp>.md`에 추출 결과 요약 포함

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Manual | JSON에서 Expert → Claim → Evidence 역추적 확인 |
| Unit | `extractor.py` 프롬프트 출력 파싱 테스트 |
| Integration | 1개 URL fetch → extract → JSON 저장 E2E |

### Risks / Notes

- LLM API 호출 필요 (HuggingFace Inference API)
- Rate limit 주의
- 추출 품질은 프롬프트 튜닝 필요 (별도 iteration)
- **Contact Evidence Policy**: requirements.md 2.1절, design.md 3.3.1절 참조
  - ContactClaim: 공개 URL 확인 가능 시만 생성
  - ContactCandidate: 간접 신호/외부 DB 출처

---

## M010-3: Frontend Viewer + Graph UI (Cytoscape.js)

**Goal**: 정적 HTML viewer로 Graph UI, 리스트/디테일/세션 전환 구현

- **Status**: DONE
- **Report**: reports/milestone-010-3.md
- **Commit**: 537125c
- **Owner**: (pending)

### Deliverables

```
frontend/
├── index.html               # Main page (loads Cytoscape.js via CDN)
├── app.js                   # Vanilla JS application
├── graph.js                 # Cytoscape.js graph rendering
└── style.css                # Basic styling
```

### Done Definition

**Graph UI (Cytoscape.js)**:
- [x] Expert 노드: 원형, `#4A90D9`, 크기는 evidenceCount에 비례
- [x] Company 노드: 사각형, `#7B68EE`, 고정 크기
- [x] Employment 엣지: Expert ↔ Company 연결
- [x] 노드 클릭 → Detail Panel 업데이트
- [x] Zoom/Pan 활성화
- [x] `cose` 레이아웃 (force-directed)

**Detail Panel**:
- [x] Expert 이름/정보 표시
- [x] Claims 목록 (Employment/Contact)
- [x] Evidence URL 링크 (클릭 시 새 탭)

**Session Management**:
- [x] File input으로 `session-*.json` 로드
- [ ] ~~또는 URL parameter로 파일 경로 지정~~ (v1 scope out)

**General**:
- [x] `frontend/index.html`을 브라우저에서 열면 UI 표시
- [x] Mobile-friendly 반응형 레이아웃 (min-width: 768px)

### Cytoscape.js Integration

```html
<!-- CDN Load -->
<script src="https://unpkg.com/cytoscape@latest/dist/cytoscape.min.js"></script>
```

```javascript
// graph.js - Session JSON → Cytoscape elements 변환
function sessionToElements(session) {
  const nodes = [];
  const edges = [];

  session.experts.forEach(expert => {
    nodes.push({
      data: {
        id: `expert-${expert.expert_id}`,
        label: expert.canonical_name,
        type: 'expert',
        evidenceCount: expert.evidence_ids.length
      }
    });
  });

  // ... companies, edges
  return { nodes, edges };
}
```

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Manual | 브라우저에서 Graph UI 기능 테스트 |
| Manual | 노드 클릭 → Detail Panel 동기화 확인 |
| Manual | 다양한 session JSON 파일로 테스트 |
| Visual | 스크린샷 캡처 (Graph + Detail Panel) |

### Risks / Notes

- Vanilla JS만 사용 (React/Vue 금지)
- 파일 로컬 로드 시 CORS 이슈 → Live Server 또는 `python -m http.server` 사용
- **Cytoscape.js only** — D3.js, force-graph, vis.js는 vNext로 이월

---

## M010-4: FastAPI Scaffold

**Goal**: FastAPI 프로젝트 구조 설정, healthz 엔드포인트

- **Status**: DONE
- **Report**: reports/milestone-010-4.md
- **Commit**: 5b61d87
- **Owner**: (pending)

### Deliverables

```
src/
└── expertlens/
    ├── api/
    │   ├── __init__.py
    │   ├── main.py           # FastAPI app
    │   └── routes/
    │       ├── __init__.py
    │       └── health.py     # GET /healthz
    └── core/
        ├── __init__.py
        └── orchestrator.py   # Core logic (moved from orchestrator.py)
```

### Done Definition

- [x] `uvicorn expertlens.api.main:app` 실행 가능
- [x] `GET /healthz` → `{ "status": "ok" }` 응답
- [x] OpenAPI docs 자동 생성 (`/docs`)
- [x] CORS 설정 (frontend 호출 허용)

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Manual | `curl localhost:8000/healthz` 확인 |
| Unit | pytest + httpx TestClient |

---

## M010-5: Sessions API

**Goal**: 세션 생성/조회 API 구현

- **Status**: DONE
- **Report**: reports/milestone-010-5.md
- **Commit**: aa66a7f
- **Owner**: (pending)

### Deliverables

```
src/
└── expertlens/
    └── api/
        └── routes/
            └── sessions.py   # POST /sessions, GET /sessions/{id}
```

### Done Definition

- [x] `POST /sessions` → `{ session_id: string }` 반환
- [x] `GET /sessions/{id}` → Session JSON 반환
- [x] 존재하지 않는 session_id → 404 응답
- [x] Pydantic 모델로 request/response 정의

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Unit | 세션 생성/조회 API 테스트 |
| Integration | 세션 파일 생성 확인 |

---

## M010-6: Run Endpoint + Core Orchestrator

**Goal**: 검색 실행 API + core 로직 연동

- **Status**: DONE
- **Report**: reports/milestone-010-6.md
- **Commit**: cfa97d9
- **Owner**: (pending)

### Deliverables

```
src/
└── expertlens/
    ├── api/
    │   └── routes/
    │       └── sessions.py   # POST /sessions/{id}/run 추가
    └── core/
        └── orchestrator.py   # run_session(session_id, query) 구현
```

### Done Definition

- [x] `POST /sessions/{id}/run` → 검색 실행 후 Session JSON 반환
- [x] `core.run_session(session_id, query)` 순수 함수 구현
- [x] LLM 추출 + Identity Resolution 연동
- [x] 파일 출력 유지 (`out/session-*.json`)

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Integration | API → Core → File 저장 E2E |
| Manual | 실제 검색 쿼리로 테스트 |

---

## M010-7: Frontend API Integration

**Goal**: Frontend를 API 호출 기반으로 전환

- **Status**: TODO
- **Report**: reports/milestone-010-7.md
- **Commit**: (pending)
- **Owner**: (pending)

### Deliverables

```
frontend/
├── index.html       # Chat-like 인터페이스 추가
├── app.js           # fetch() API 호출로 전환
└── api.js           # API client 모듈 (신규)
```

### Done Definition

- [ ] 검색 입력 → API 호출 → 결과 표시
- [ ] `POST /sessions` + `POST /sessions/{id}/run` 연동
- [ ] 파일 업로드 방식 유지 (fallback)
- [ ] Loading 상태 표시

### Tests

| 테스트 종류 | 내용 |
|-------------|------|
| Manual | 브라우저에서 검색 → 그래프 표시 테스트 |
| Manual | API 서버 없을 때 파일 업로드 fallback 확인 |

---

## Dependencies

### CLI Pilot (Archived)

```
M010-0 ──► M010-1 ──► M010-2 ──► M010-3
```

### API-based v1 (Current)

```
M010-4 ──► M010-5 ──► M010-6 ──► M010-7
FastAPI    Sessions   Run+Core  Frontend
Scaffold     API      Endpoint  API Int.
```

| From | To | Dependency |
|------|----|------------|
| M010-4 | M010-5 | FastAPI 기반. Sessions API의 전제조건 |
| M010-5 | M010-6 | Sessions 생성 후 Run 가능 |
| M010-6 | M010-7 | API 동작 후 Frontend 연동 |
| M010-0~3 | M010-4~7 | CLI Pilot의 core 로직/모델 재사용 |

---

## vNext Milestones (Deferred)

아래 마일스톤은 v1 완료 후 진행:

| ID | 제목 | 설명 |
|----|------|------|
| M010-11 | DuckDuckGo Search Integration | 실제 DDG 검색 연동 |
| M010-12 | Identity Resolution Enhancement | Blocking keys + scoring |
| M010-13 | Advanced Graph UI | D3.js, force-graph 대안 |
| M010-14 | Neo4j Integration | Graph DB 저장 |
| M010-15 | React Frontend | Interactive UI |
| M010-16 | Contact Evidence Enhancement | ZoomInfo/Apollo/Lusha 연동, Claim/Candidate 분기 자동화 |
| M010-17 | SSE Progress Streaming | 실시간 진행 상황 스트리밍 |
