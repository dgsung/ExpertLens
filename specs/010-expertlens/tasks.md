# ExpertLens Tasks

Version: 1.1.0
Last Updated: 2026-01-16
Change Notes:
- v1.1.0: i18n, 배치 LLM, Render 배포 추가. SSE 상세 설명 추가.
- v1.0.0: 피라미드 구조로 재구성. 현황 요약 추가.
- v0.6.0: Ad-hoc Tasks 섹션 추가
- v0.5.0: FastAPI 마이그레이션

---

## 한 줄 정의

**실행 현황 추적 (SSOT)** — 마일스톤 진척, 현재 작업, Ad-hoc 요청을 단일 문서로 관리.

---

## 현황 요약

| 지표 | 값 |
|------|-----|
| **v1 진행률** | 100% (12/12 마일스톤 완료) |
| **현재 진행** | 없음 (v1 완료) |
| **다음 작업** | vNext 마일스톤 중 선택 |

### v1 완료 마일스톤

| ID | 제목 | 상태 |
|----|------|------|
| M010-0 ~ M010-7 | CLI + API 기반 구축 | DONE |
| M010-11 | DuckDuckGo 검색 연동 | DONE |
| M010-12 | Identity Resolution 고도화 | DONE |

### vNext 대기

| ID | 제목 | 우선순위 |
|----|------|----------|
| M010-18 | Interview Outreach | **높음** |
| M010-17 | SSE 스트리밍 | 높음 |
| M010-16 | Contact Evidence 자동화 | 중간 |
| M010-15 | React Frontend | 중간 |
| M010-14 | Neo4j 연동 | 중간 |
| M010-13 | 고급 그래프 UI (D3.js) | 낮음 |

---

## 마일스톤 상세

### M010-0: CLI Scaffold

**Goal**: CLI 진입점, 파일 출력 구조

- **Status**: DONE
- **Commit**: 39ec5d5

| 완료 항목 |
|-----------|
| `python -m expertlens --help` 동작 |
| `out/session-*.json` 생성 |
| `reports/run-*.md` 생성 |

---

### M010-1: Mock Search → Session JSON

**Goal**: Mock 검색으로 Session JSON 생성, 스키마 검증

- **Status**: DONE
- **Commit**: 34a4c2e

| 완료 항목 |
|-----------|
| Session JSON 스키마 정의 |
| Mock expert/evidence 데이터 |
| Pydantic 검증 |

---

### M010-2: LLM Extraction + Evidence Traceability

**Goal**: LLM으로 Claim 추출, Evidence URL 역추적

- **Status**: DONE
- **Commit**: d359f7f

| 완료 항목 |
|-----------|
| HuggingFace API 연동 |
| PersonCandidate 추출 |
| EmploymentClaim, ContactClaim 생성 |
| Expert → Claim → Evidence 추적 |

---

### M010-3: Frontend Viewer (Cytoscape.js)

**Goal**: 정적 HTML 뷰어, 그래프 UI

- **Status**: DONE
- **Commit**: 537125c

| 완료 항목 |
|-----------|
| Cytoscape.js 그래프 |
| Expert/Company 노드 |
| Detail Panel |
| 파일 업로드 |

---

### M010-4: FastAPI Scaffold

**Goal**: FastAPI 프로젝트 구조, healthz

- **Status**: DONE
- **Commit**: 5b61d87

| 완료 항목 |
|-----------|
| `GET /healthz` |
| CORS 설정 |
| OpenAPI docs |

---

### M010-5: Sessions API

**Goal**: 세션 생성/조회 API

- **Status**: DONE
- **Commit**: aa66a7f

| 완료 항목 |
|-----------|
| `POST /sessions` |
| `GET /sessions/{id}` |
| 404 처리 |

---

### M010-6: Run Endpoint + Core

**Goal**: 검색 실행 API, Core 연동

- **Status**: DONE
- **Commit**: cfa97d9

| 완료 항목 |
|-----------|
| `POST /sessions/{id}/run` |
| core.run_session() |
| 파일 출력 유지 |

---

### M010-7: Frontend API Integration

**Goal**: Frontend를 API 호출 기반으로 전환

- **Status**: DONE
- **Commit**: bd3ca14

| 완료 항목 |
|-----------|
| fetch() API 호출 |
| Loading 상태 |
| 파일 업로드 fallback |

---

### M010-11: DuckDuckGo Search

**Goal**: 실제 DuckDuckGo 검색 연동

- **Status**: DONE
- **Commit**: 07fd705

| 완료 항목 |
|-----------|
| DuckDuckGoSearchProvider |
| use_mock 파라미터 |
| 검색 결과 → LLM 파이프라인 |

---

### M010-12: Identity Resolution Enhancement

**Goal**: Blocking keys + scoring 기반 중복 병합

- **Status**: DONE
- **Commit**: 465e167

| 완료 항목 |
|-----------|
| BlockingKey 추출 |
| Scoring 알고리즘 |
| Union-Find 병합 |
| Claim 중복 제거 |

---

## vNext 마일스톤 (대기)

| ID | 제목 | 설명 |
|----|------|------|
| M010-18 | Interview Outreach | 발굴 전문가에게 인터뷰 의사 확인 시퀀스 |
| M010-17 | SSE Streaming | 실시간 진행 상황 (아래 상세) |
| M010-16 | Contact Enhancement | ZoomInfo/Apollo 자동 분류 |
| M010-15 | React Frontend | SPA |
| M010-14 | Neo4j Integration | Graph DB |
| M010-13 | Advanced Graph UI | D3.js, force-graph |

### M010-17: SSE Streaming (상세)

**Goal**: 검색 진행 상황을 실시간으로 프론트엔드에 표시

**배경**: 현재 "검색 중..."만 표시됨. 사용자에게 어떤 단계인지 보여주면 UX 향상.

**구현 계획**:

| 단계 | 백엔드 | 프론트엔드 표시 |
|------|--------|----------------|
| 1 | LinkedIn 검색 시작 | 🔍 LinkedIn 검색 중... |
| 2 | 웹 검색 시작 | 🌐 웹 페이지 수집 중... |
| 3 | LLM 추출 시작 | 🤖 전문가 정보 추출 중... |
| 4 | 완료 | ✨ 결과 정리 중... |

**기술 스택**:
- 백엔드: `StreamingResponse` (FastAPI)
- 프론트엔드: `EventSource` API
- 엔드포인트: `POST /sessions/{id}/run/stream`

**예상 작업량**: 2-3시간

---

## Ad-hoc Tasks

임시 요청 추적. 마일스톤 외 작업.

| Date | Request | Status | Notes |
|------|---------|--------|-------|
| 2026-01-16 | Render 배포 설정 | DONE | render.yaml, api.js URL 감지 |
| 2026-01-16 | i18n 다국어 지원 | DONE | ko/en, 브라우저 언어 자동 감지 |
| 2026-01-16 | 배치 LLM 처리 | DONE | 5개 URL씩 묶어서 호출, rate limit 해결 |
| 2026-01-11 | 문서 구조 개선 (피라미드) | DONE | CLAUDE/requirements/design/tasks 재구성 |
| 2026-01-04 | Empty State UI | DONE | 0명 결과 시 안내 |
| 2026-01-03 | 검색 과정 투명성 UI | DONE | 접이식 UI, search_steps |
| 2026-01-03 | CLAUDE.md Agent Roles | DONE | planner/executor 분리 |
| 2026-01-03 | 프론트엔드 use_mock 옵션 | DONE | 체크박스 UI |
| 2026-01-03 | ddgs 패키지 업그레이드 | DONE | duckduckgo-search → ddgs |

---

## 마일스톤 메타데이터 형식

```markdown
### M010-X: 제목

**Goal**: 한 줄 목표

- **Status**: TODO | IN_PROGRESS | DONE
- **Commit**: (pending) | <sha>

| 완료 항목 |
|-----------|
| ... |
```
