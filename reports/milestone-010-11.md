# Milestone M010-11: DuckDuckGo Search Integration

**Status**: DONE
**Completed**: 2026-01-02
**Commit**: (pending)

---

## Goal

실제 DuckDuckGo 검색 연동

---

## Deliverables

| File | Description |
|------|-------------|
| `src/expertlens/search/duckduckgo.py` | DuckDuckGoSearchProvider 클래스 |
| `src/expertlens/search/__init__.py` | Export 추가 |
| `src/expertlens/core/orchestrator.py` | use_mock=False 시 DDG 사용 |
| `src/expertlens/api/schemas.py` | RunSessionRequest에 use_mock 파라미터 추가 |
| `requirements.txt` | duckduckgo-search 의존성 추가 |

---

## API Usage

```bash
# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}'

# Run with REAL DuckDuckGo search
curl -X POST http://localhost:8000/sessions/{session_id}/run \
  -H "Content-Type: application/json" \
  -d '{"query": "battery researcher", "use_mock": false}'

# Run with mock search (default)
curl -X POST http://localhost:8000/sessions/{session_id}/run \
  -H "Content-Type: application/json" \
  -d '{"query": "배터리 전문가"}'
```

---

## DuckDuckGoSearchProvider

```python
from expertlens.search import DuckDuckGoSearchProvider

provider = DuckDuckGoSearchProvider(
    language="ko",   # Search region (ko, en, ja, etc.)
    max_results=10   # Max results to return
)

# General search
evidence_list = provider.search("battery expert")

# Site-specific search
linkedin_results = provider.search_site("battery expert", "linkedin.com/in")

# Expert search (combines LinkedIn + general)
all_results = provider.search_expert("battery expert")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  POST /sessions/{id}/run                                     │
│  { "query": "...", "use_mock": false }                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator                            │
│  if use_mock:                                                │
│      MockSearchProvider → pre-built experts/companies        │
│  else:                                                       │
│      DuckDuckGoSearchProvider → Evidence (URLs only)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  DuckDuckGoSearchProvider                    │
│  - Uses duckduckgo-search library                           │
│  - Returns Evidence objects with URL, title, snippet         │
│  - Platform auto-detection (linkedin, news, patent, etc.)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Done Definition Checklist

- [x] DuckDuckGoSearchProvider 구현
- [x] duckduckgo-search 라이브러리 연동
- [x] Orchestrator에서 use_mock=False 시 DDG 사용
- [x] API에서 use_mock 파라미터 지원
- [x] 플랫폼 자동 감지 (linkedin, news, patent 등)

---

## Test Results

| Test | Result |
|------|--------|
| DuckDuckGoSearchProvider.search() | Pass (5+ results) |
| API with use_mock=false | Pass (20 URLs collected) |
| Evidence 누적 (여러 쿼리) | Pass |
| Platform detection | Pass (web, linkedin, etc.) |

---

## Limitations

1. **Rate Limiting**: DuckDuckGo may rate-limit or block requests
2. **No Expert Extraction**: Currently returns URLs only, not extracted experts
3. **Search Quality**: Results quality depends on DuckDuckGo's algorithm

---

## Follow-ups

- M010-12: Identity Resolution Enhancement
- LLM extraction from DDG search results (process_urls flow)
- Rate limiting / proxy support

---

## Sources

- [duckduckgo-search PyPI](https://pypi.org/project/duckduckgo-search/)
