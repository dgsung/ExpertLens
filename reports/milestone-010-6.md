# Milestone M010-6: Run Endpoint + Core Orchestrator

**Status**: DONE
**Completed**: 2026-01-02
**Commit**: e2304ca

---

## Goal

검색 실행 API + core 로직 연동

---

## Deliverables

| File | Description |
|------|-------------|
| `src/expertlens/api/routes/sessions.py` | Added POST /sessions/{id}/run endpoint |
| `src/expertlens/api/schemas.py` | Added RunSessionRequest schema |
| `src/expertlens/core/orchestrator.py` | Added run_session() method |

---

## How to Run

```bash
# Start API server
PYTHONPATH=src uvicorn expertlens.api.main:app --reload

# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"language": "ko"}'

# Run search
curl -X POST http://localhost:8000/sessions/{session_id}/run \
  -H "Content-Type: application/json" \
  -d '{"query": "배터리 전문가"}'
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions/{id}/run` | Execute search and update session |

### POST /sessions/{id}/run

**Request**:
```json
{
  "query": "배터리 전문가"
}
```

**Response** (200 OK):
```json
{
  "session_id": "8430b2df-b283-49a9-b904-5562b096b46c",
  "language": "ko",
  "query": "배터리 전문가",
  "queries": [{"query": "배터리 전문가", "added_at": "..."}],
  "experts": [...],
  "companies": [...],
  "evidence": [...]
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Session not found: non-existent"
}
```

---

## Architecture

```
POST /sessions/{id}/run
         │
         ▼
┌─────────────────────────┐
│  sessions.py (API)      │
│  - Validate session     │
│  - Call orchestrator    │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  orchestrator.py (Core) │
│  - run_session()        │
│  - MockSearchProvider   │
│  - Merge results        │
│  - Write file           │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  out/session-*.json     │
│  reports/run-*.md       │
└─────────────────────────┘
```

---

## Core Function

```python
def run_session(self, session: Session, query: str) -> Session:
    """Execute a search and update an existing session."""
    # 1. Execute mock search
    # 2. Update session with new query
    # 3. Merge new results (avoid duplicates)
    # 4. Write updated session JSON
    # 5. Create run report
    return session
```

---

## Done Definition Checklist

- [x] `POST /sessions/{id}/run` → 검색 실행 후 Session JSON 반환
- [x] `core.run_session(session_id, query)` 순수 함수 구현
- [x] LLM 추출 + Identity Resolution 연동 (Mock 사용)
- [x] 파일 출력 유지 (`out/session-*.json`)

---

## Test Results

| Test | Result |
|------|--------|
| POST /sessions (create) | Pass |
| POST /sessions/{id}/run | Pass (2 experts, 2 companies, 4 evidence) |
| Session file written | Pass (out/session-*.json exists) |
| 404 for non-existent | Pass |
| OpenAPI spec | Pass (/sessions/{session_id}/run registered) |

---

## Risks / Follow-ups

- 현재 MockSearchProvider 사용 (실제 검색은 vNext)
- M010-7에서 Frontend API 연동 필요
