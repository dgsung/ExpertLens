# Milestone M010-7: Frontend API Integration

**Status**: DONE
**Completed**: 2026-01-02
**Commit**: bd3ca14

---

## Goal

Frontend를 API 호출 기반으로 전환

---

## Deliverables

| File | Description |
|------|-------------|
| `frontend/api.js` | API client 모듈 (신규) |
| `frontend/app.js` | fetch() API 호출로 전환 |
| `frontend/index.html` | 검색 입력 UI + 로딩 오버레이 추가 |
| `frontend/style.css` | 검색 폼 + 로딩 스타일 추가 |

---

## How to Run

```bash
# 1. Start API server
PYTHONPATH=src uvicorn expertlens.api.main:app --reload

# 2. Start frontend (separate terminal)
cd frontend
python -m http.server 8080

# 3. Open browser
open http://localhost:8080
```

---

## Features

### 1. API Client (`api.js`)

```javascript
// Check API availability
await ExpertLensAPI.isAvailable();

// Create session
const { session_id } = await ExpertLensAPI.createSession('ko');

// Run search
const session = await ExpertLensAPI.runSearch(session_id, 'query');

// Combined flow
const session = await ExpertLensAPI.search('query', 'ko');
```

### 2. Search UI

- 검색 입력창 (헤더에 위치)
- 검색 버튼 클릭 또는 Enter 키로 검색 실행
- API 서버 연결 상태에 따라 버튼 활성화/비활성화

### 3. Loading State

- 검색 중 로딩 오버레이 표시
- 진행 메시지 업데이트 ("세션 생성 중...", "검색 중...")

### 4. File Upload Fallback

- API 서버 연결 안됨 시 파일 업로드 방식 유지
- 기존 `session-*.json` 파일 로드 가능

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (index.html)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │   Search UI   │  │  Graph Panel  │  │ Detail Panel  │   │
│  │  (검색 입력)   │  │ (Cytoscape.js)│  │  (노드 상세)   │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │    api.js     │  │   graph.js    │  │    app.js     │   │
│  │ (API client)  │  │ (Graph 렌더링) │  │ (메인 로직)    │   │
│  └───────┬───────┘  └───────────────┘  └───────────────┘   │
│          │                                                   │
│          ▼                                                   │
│   fetch() API 호출                                           │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (localhost:8000)             │
├─────────────────────────────────────────────────────────────┤
│  GET /healthz         → API 상태 확인                        │
│  POST /sessions       → 세션 생성                            │
│  POST /sessions/{id}/run → 검색 실행                         │
│  GET /sessions/{id}   → 세션 조회                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Done Definition Checklist

- [x] 검색 입력 → API 호출 → 결과 표시
- [x] `POST /sessions` + `POST /sessions/{id}/run` 연동
- [x] 파일 업로드 방식 유지 (fallback)
- [x] Loading 상태 표시

---

## Test Results

| Test | Result |
|------|--------|
| API healthz check | Pass |
| POST /sessions (create) | Pass |
| POST /sessions/{id}/run | Pass (2 experts, 2 companies, 4 evidence) |
| File upload fallback | Pass (기존 기능 유지) |
| Loading overlay | Pass |
| API disconnected handling | Pass (버튼 비활성화, placeholder 메시지 변경) |

---

## Screenshots

### 1. Search UI
```
┌────────────────────────────────────────────────────┐
│ ExpertLens   [검색어 입력________] [검색]  [파일 로드] │
└────────────────────────────────────────────────────┘
```

### 2. Loading State
```
┌────────────────────────────────────────────────────┐
│                      ◌                              │
│                  검색 중...                         │
└────────────────────────────────────────────────────┘
```

---

## Risks / Follow-ups

- 실제 검색이 아닌 MockSearchProvider 사용 (M010-11에서 실제 검색 연동)
- SSE Progress Streaming은 M010-17로 이월
