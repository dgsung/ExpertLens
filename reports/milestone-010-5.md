# Milestone M010-5: Sessions API

**Status**: DONE
**Completed**: 2026-01-02
**Commit**: aa66a7f

---

## Goal

세션 생성/조회 API 구현

---

## Deliverables

| File | Description |
|------|-------------|
| `src/expertlens/api/schemas.py` | API request/response Pydantic models |
| `src/expertlens/api/routes/sessions.py` | Sessions API endpoints |
| `src/expertlens/core/session_manager.py` | Session CRUD operations |

---

## How to Run

```bash
# Start API server
PYTHONPATH=src uvicorn expertlens.api.main:app --reload

# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"language": "ko"}'

# Get session
curl http://localhost:8000/sessions/{session_id}

# List sessions
curl http://localhost:8000/sessions
```

---

## API Endpoints

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| POST | `/sessions` | Create new session | `{"session_id": "uuid"}` |
| GET | `/sessions/{id}` | Get session by ID | Full Session JSON |
| GET | `/sessions` | List all session IDs | `["uuid1", "uuid2", ...]` |

### POST /sessions

**Request**:
```json
{
  "language": "ko"
}
```

**Response** (201 Created):
```json
{
  "session_id": "3898f87d-6aea-455a-b195-7f9a66ec4961"
}
```

### GET /sessions/{id}

**Response** (200 OK):
```json
{
  "session_id": "3898f87d-6aea-455a-b195-7f9a66ec4961",
  "language": "ko",
  "query": "",
  "queries": [],
  "created_at": "2026-01-02T15:03:49.418231Z",
  "updated_at": "2026-01-02T15:03:49.418231Z",
  "experts": [],
  "companies": [],
  "evidence": []
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Session not found: non-existent-id"
}
```

---

## Architecture

```
src/expertlens/
├── api/
│   ├── schemas.py           # NEW: API request/response models
│   ├── main.py              # Updated: include sessions router
│   └── routes/
│       └── sessions.py      # NEW: POST/GET /sessions
└── core/
    ├── __init__.py          # Updated: export SessionManager
    └── session_manager.py   # NEW: Session CRUD operations
```

---

## Done Definition Checklist

- [x] `POST /sessions` → `{ session_id: string }` 반환
- [x] `GET /sessions/{id}` → Session JSON 반환
- [x] 존재하지 않는 session_id → 404 응답
- [x] Pydantic 모델로 request/response 정의

---

## Test Results

| Test | Result |
|------|--------|
| POST /sessions | Pass (201, returns session_id) |
| GET /sessions/{id} | Pass (200, returns full session) |
| GET /sessions/{non-existent} | Pass (404, error message) |
| GET /sessions (list) | Pass (returns session IDs array) |
| OpenAPI spec | Pass (all paths registered) |

---

## Risks / Follow-ups

- M010-6에서 `POST /sessions/{id}/run` 구현 필요
- Session에 query 추가 로직은 run endpoint에서 처리
