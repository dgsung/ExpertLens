# Milestone M010-4: FastAPI Scaffold

**Status**: DONE
**Completed**: 2026-01-02
**Commit**: 5b61d87

---

## Goal

FastAPI 프로젝트 구조 설정 및 healthz 엔드포인트 구현

---

## Deliverables

| File | Description |
|------|-------------|
| `src/expertlens/api/__init__.py` | API module init |
| `src/expertlens/api/main.py` | FastAPI application with CORS |
| `src/expertlens/api/routes/__init__.py` | Routes module init |
| `src/expertlens/api/routes/health.py` | Health check endpoint |
| `src/expertlens/core/__init__.py` | Core module init |
| `src/expertlens/core/orchestrator.py` | Core orchestrator (moved from root) |
| `requirements.txt` | Project dependencies |

---

## How to Run

```bash
# Start API server
PYTHONPATH=src uvicorn expertlens.api.main:app --reload

# Test endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/
curl http://localhost:8000/docs  # OpenAPI UI

# CLI still works (backward compatible)
PYTHONPATH=src python -m expertlens --help
```

---

## API Endpoints

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/` | `{"name": "ExpertLens API", "version": "0.1.0", "docs": "/docs"}` |
| GET | `/healthz` | `{"status": "ok"}` |
| GET | `/docs` | OpenAPI Swagger UI |
| GET | `/openapi.json` | OpenAPI spec |

---

## Architecture

```
src/expertlens/
├── api/                    # NEW: API layer
│   ├── __init__.py
│   ├── main.py             # FastAPI app + CORS
│   └── routes/
│       ├── __init__.py
│       └── health.py       # /healthz endpoint
├── core/                   # NEW: Core business logic
│   ├── __init__.py
│   └── orchestrator.py     # Moved from root
├── orchestrator.py         # Re-exports from core (backward compat)
└── ...                     # Existing modules unchanged
```

---

## CORS Configuration

Frontend origins allowed:
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- `http://localhost:3000`
- `http://127.0.0.1:3000`

---

## Done Definition Checklist

- [x] `uvicorn expertlens.api.main:app` 실행 가능
- [x] `GET /healthz` → `{ "status": "ok" }` 응답
- [x] OpenAPI docs 자동 생성 (`/docs`)
- [x] CORS 설정 (frontend 호출 허용)

---

## Test Results

| Test | Result |
|------|--------|
| Server startup | Pass |
| GET /healthz | Pass (`{"status":"ok"}`) |
| GET / | Pass (`{"name":"ExpertLens API",...}`) |
| OpenAPI spec | Pass (paths: `/healthz`, `/`) |
| CLI backward compat | Pass (`--help` works) |

---

## Risks / Follow-ups

- M010-5에서 Sessions API 구현 필요
- M010-6에서 Run endpoint + core 연동 필요
- Frontend는 M010-7에서 API 호출로 전환

---

## Dependencies Added

```
# requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
httpx>=0.26.0
```
