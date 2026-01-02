# Tasks / Milestones — ExpertLens
Version: 0.4.0
Last Updated: 2026-01-02
Change Notes:
- v0.4.0: Added Contact Evidence Policy references, M010-10 (Contact Enhancement)
- v0.3.1: Added Cytoscape.js to M010-3, added Quick Reference, restructured for consistency
- v0.2.0: Restructured milestones for v1 (CLI + file-based, no DB/framework)
- v0.1.0: Initialized milestone plan with parseable metadata fields.

---

## Overview

v1은 CLI + 파일 기반 + 정적 viewer로 **설명 가능성(Explainability)** 검증에 집중한다.

```
M010-0 → M010-1 → M010-2 → M010-3
 CLI     Mock      LLM      Static
Scaffold Search   Extract   Viewer
                            + Graph
```

---

## Quick Reference

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

## Dependencies

```
M010-0 ──► M010-1 ──► M010-2
                        │
                        ▼
                     M010-3
```

| From | To | Dependency |
|------|----|------------|
| M010-0 | M010-1 | CLI 기반. 이후 모든 마일스톤의 전제조건 |
| M010-1 | M010-2 | Mock 데이터로 JSON schema 확정 |
| M010-2 | M010-3 | 실제 LLM 추출. M010-1의 schema 기반 |
| M010-1/2 | M010-3 | Viewer. JSON 파일 사용 |

---

## vNext Milestones (Deferred)

아래 마일스톤은 v1 완료 후 진행:

| ID | 제목 | 설명 |
|----|------|------|
| M010-4 | DuckDuckGo Search Integration | 실제 DDG 검색 연동 |
| M010-5 | Identity Resolution Enhancement | Blocking keys + scoring |
| M010-6 | Advanced Graph UI | D3.js, force-graph 대안 |
| M010-7 | Neo4j Integration | Graph DB 저장 |
| M010-8 | FastAPI Backend | REST API |
| M010-9 | React Frontend | Interactive UI |
| M010-10 | Contact Evidence Enhancement | ZoomInfo/Apollo/Lusha 연동, Claim/Candidate 분기 자동화 |
