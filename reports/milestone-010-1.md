# Milestone M010-1: Mock Search → Session JSON

## Goal

하드코딩/mock 검색으로 session JSON 생성, pydantic schema 검증.

## Completed Tasks

- [x] `python -m expertlens search "배터리 전문가" --lang ko` 실행
- [x] `out/session-<uuid>.json` 생성됨
- [x] JSON 필드: `session_id`, `language`, `query`, `queries[]`, `created_at`, `updated_at`, `experts[]`, `evidence[]`
- [x] Mock expert 최소 2명, mock evidence 최소 3개 포함
- [x] JSON schema validation 통과 (pydantic)

## How to Run / Demo

```bash
# Run search with Korean mock data (2 experts, 4 evidence, 2 companies)
PYTHONPATH=src python -m expertlens search "배터리 전문가" --lang ko

# Run search with English mock data
PYTHONPATH=src python -m expertlens search "battery expert" --lang en

# List sessions
PYTHONPATH=src python -m expertlens list

# Run all tests
PYTHONPATH=src pytest tests/ -v
```

## Test Results

```
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-9.0.2
collected 34 items

tests/test_models.py - 14 passed
tests/test_search.py - 12 passed
tests/test_writer.py - 8 passed

============================== 34 passed in 0.22s ==============================
```

**Status**: All 34 tests passed.

## Notable Changes

### Files Created

```
src/expertlens/
├── models/
│   ├── __init__.py          # Model exports
│   ├── session.py           # Session, Query models
│   ├── expert.py            # Expert, EmploymentClaim, ContactClaim
│   ├── evidence.py          # Evidence model
│   └── company.py           # Company model
└── search/
    ├── __init__.py          # Search exports
    ├── mock.py              # MockSearchProvider (Korean/English)
    └── planner.py           # SearchPlanner stub

tests/
├── test_models.py           # 14 model tests
└── test_search.py           # 12 search tests
```

### Files Modified

```
src/expertlens/
├── orchestrator.py          # Uses MockSearchProvider + models
├── io/writer.py             # Uses Session model for JSON output
└── __main__.py              # Shows result counts
```

### Key Components

| Component | Description |
|-----------|-------------|
| `Session` | Pydantic model for session JSON |
| `Expert` | Expert with claims and evidence_ids |
| `EmploymentClaim` | Employment at company with dates |
| `ContactClaim` | Contact info (linkedin, email, etc.) |
| `Evidence` | URL source with platform and timestamp |
| `MockSearchProvider` | Returns hardcoded Korean/English mock data |

### Mock Data (Korean)

| Type | Count | Examples |
|------|-------|----------|
| Experts | 2 | 홍길동 (삼성SDI), 김철수 (LG에너지솔루션) |
| Evidence | 4 | LinkedIn profiles, news, patents |
| Companies | 2 | 삼성SDI, LG에너지솔루션 |

## Risks / Follow-ups

- Mock 데이터는 실제 검색 결과 아님 (M010-2에서 실제 URL fetch 예정)
- pydantic 의존성 추가 (`pip install pydantic` 필요)

## Link to tasks.md

[M010-1: Mock Search → Session JSON](../specs/010-expertlens/tasks.md#m010-1-mock-search--session-json)
