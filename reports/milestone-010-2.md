# Milestone M010-2: Minimal LLM Extraction + Evidence Traceability

**Status**: DONE
**Completed**: 2026-01-02
**Commit**: d359f7f

---

## Goal

Minimal LLM extraction with HuggingFace Inference API, URL fetching with BeautifulSoup, and simple identity resolution.

---

## Deliverables

### Created Files

| File | Description |
|------|-------------|
| `src/expertlens/llm/__init__.py` | LLM module init |
| `src/expertlens/llm/client.py` | HuggingFace Inference API client |
| `src/expertlens/llm/extractor.py` | Evidence extraction with LLM prompts |
| `src/expertlens/evidence/__init__.py` | Evidence module init |
| `src/expertlens/evidence/fetcher.py` | URL fetcher with BeautifulSoup |
| `src/expertlens/identity/__init__.py` | Identity module init |
| `src/expertlens/identity/resolver.py` | Simple name-based identity resolution |
| `tests/test_llm.py` | Unit tests for LLM components (17 tests) |
| `tests/test_evidence.py` | Unit tests for evidence fetcher (13 tests) |
| `tests/test_identity.py` | Unit tests for identity resolver (10 tests) |
| `.env` | Environment file with HF_API_KEY (gitignored) |

### Modified Files

| File | Changes |
|------|---------|
| `src/expertlens/orchestrator.py` | Added `process_urls()` method, lazy-init for LLM/fetcher/resolver |
| `src/expertlens/__main__.py` | Added `extract` command for URL extraction |
| `.gitignore` | Added `.env` and `.env.*` patterns |

---

## Architecture

### LLM Integration

```
HuggingFaceClient
├── model: Mistral-7B-Instruct-v0.2 (default)
├── generate(prompt) → str
└── extract_json(prompt) → dict
```

### Evidence Flow

```
URL → EvidenceFetcher → (Evidence, content)
                            ↓
                    EvidenceExtractor
                            ↓
                PersonCandidate[] + Company[]
                            ↓
                    IdentityResolver
                            ↓
                       Expert[]
```

### Platform Detection

| Pattern | Platform |
|---------|----------|
| `linkedin.com` | linkedin |
| `twitter.com`, `x.com` | twitter |
| `youtube.com` | youtube |
| `arxiv`, `scholar` | paper |
| `patent` | patent |
| `news`, `article`, `blog` | news |
| default | web |

---

## Done Definition Checklist

- [x] HuggingFace Inference API client with JSON extraction
- [x] Evidence fetcher with BeautifulSoup content extraction
- [x] Platform detection from URL patterns
- [x] LLM-based person/company extraction with structured prompts
- [x] Simple name-based identity resolution with Korean/English support
- [x] CLI `extract` command for URL processing
- [x] Orchestrator `process_urls()` method integrating all components
- [x] Environment variable for HF_API_KEY (gitignored)
- [x] Unit tests for all new components (40 new tests)

---

## Test Results

```
tests/test_evidence.py    13 passed
tests/test_identity.py    10 passed
tests/test_llm.py         17 passed
tests/test_models.py      14 passed
tests/test_search.py      11 passed
tests/test_writer.py       8 passed
─────────────────────────────────────
Total                     73 passed
```

---

## CLI Usage

### Mock Search (existing)
```bash
python -m expertlens search "배터리 전문가" --lang ko
```

### URL Extraction (new)
```bash
python -m expertlens extract https://example.com/article --lang ko
python -m expertlens extract url1.com url2.com url3.com
```

---

## Key Components

### HuggingFaceClient

- Default model: `mistralai/Mistral-7B-Instruct-v0.2`
- API key from `HF_API_KEY` environment variable
- Handles markdown-wrapped JSON responses
- Configurable timeout (default 60s)

### EvidenceFetcher

- Uses `httpx` for HTTP requests
- BeautifulSoup for HTML parsing
- Removes script, style, nav, footer elements
- Finds main content via article/main selectors
- Returns Evidence model + extracted text

### IdentityResolver

- Case-insensitive name matching
- Unicode normalization (NFC for Korean)
- Punctuation and whitespace normalization
- Claim deduplication during merge
- Evidence ID aggregation

---

## Notes

- HuggingFace token stored in `.env` (not committed)
- Real URL fetch requires network access
- LLM extraction may fail on rate limits or model availability
- Identity resolution is simple name-matching for v1 (fuzzy matching prepared but not active)
