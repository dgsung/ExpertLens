# ExpertLens Design

Version: 1.1.0
Last Updated: 2026-01-16
Change Notes:
- v1.1.0: 배치 LLM 처리 추가, i18n 다국어 지원 추가
- v1.0.0: 피라미드 구조로 재구성. 기술 스택/아키텍처에 집중. 정책은 requirements.md로 이동.
- v0.5.0: FastAPI 마이그레이션
- v0.4.0: Contact Evidence Strategy 추가

---

## 한 줄 정의

**기술 구현 명세** — 시스템 아키텍처, 데이터 스키마, API 명세, 기술 결정 로그.

---

## 1. 시스템 아키텍처

### 1.1 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Vanilla JS)                         │
│  index.html + app.js + graph.js (Cytoscape.js CDN)              │
└─────────────────────────────────────────────────────────────────┘
                              │ fetch()
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI (Thin Wrapper)                        │
│  POST /sessions  │  POST /sessions/{id}/run  │  GET /sessions   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Orchestrator                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Search  │ │ Evidence │ │ Identity │ │ File I/O │           │
│  │  Planner │ │ Fetcher  │ │ Resolver │ │  (JSON)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
┌─────────────────┐                    ┌─────────────────────────┐
│ DuckDuckGo API  │                    │ out/session-*.json      │
└─────────────────┘                    └─────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM (HuggingFace API)                         │
│  Requirement Clarifier  │  Evidence Extractor                    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Thin API** | FastAPI는 core 호출만. 비즈니스 로직 금지. |
| **Core = Pure** | 상태 없는 순수 함수. 입력 → 출력만. |
| **LLM = 해석만** | LLM은 추출/해석만. 흐름 제어는 Core. |
| **파일 기반** | v1은 DB 없이 JSON 파일로 저장. |

---

## 2. 데이터 스키마

### 2.1 Session JSON

```json
{
  "session_id": "uuid",
  "language": "ko",
  "query": "배터리 소재 전문가",
  "queries": [{ "query": "...", "added_at": "ISO8601" }],
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "experts": [...],
  "companies": [...],
  "evidence": [...],
  "search_steps": [...]
}
```

### 2.2 Entity 정의

**Expert**
| 필드 | 타입 | 설명 |
|------|------|------|
| expert_id | UUID | 고유 식별자 |
| canonical_name | string | 대표 이름 |
| claims | Claim[] | 소속/연락처 등 |
| evidence_ids | UUID[] | 관련 증거 |

**Company**
| 필드 | 타입 | 설명 |
|------|------|------|
| company_id | UUID | 고유 식별자 |
| name | string | 회사명 |
| domain | string? | 웹사이트 도메인 |
| region | string? | 지역 코드 |

**Evidence**
| 필드 | 타입 | 설명 |
|------|------|------|
| evidence_id | UUID | 고유 식별자 |
| url | string | 원본 URL |
| platform | string | 출처 플랫폼 |
| retrieved_at | ISO8601 | 수집 시각 |

### 2.3 Claim 종류 (v1)

| Claim | 관계 | 설명 |
|-------|------|------|
| EmploymentClaim | Expert ↔ Company | 소속, 직책, 기간 |
| ContactClaim | Expert ↔ ContactPoint | 연락처 (공개 확인됨) |
| MergeDecision | Expert ↔ Expert | Identity Resolution 로그 |

---

## 3. API 명세

### 3.1 Endpoints

| Method | Path | 설명 | Request | Response |
|--------|------|------|---------|----------|
| GET | `/healthz` | 상태 확인 | - | `{ status: "ok" }` |
| POST | `/sessions` | 세션 생성 | `{ language }` | `{ session_id }` |
| GET | `/sessions/{id}` | 세션 조회 | - | Session JSON |
| POST | `/sessions/{id}/run` | 검색 실행 | `{ query, use_mock? }` | Session JSON |

### 3.2 에러 응답

| 코드 | 상황 |
|------|------|
| 404 | 세션 없음 |
| 422 | 잘못된 요청 형식 |
| 500 | 내부 오류 |

---

## 4. Core 모듈

### 4.1 파이프라인

```
run_session(session_id, query)
    │
    ├── 1. Search Planner: 검색 쿼리 생성
    │
    ├── 2. DuckDuckGo Adapter: URL 수집 (최대 10개)
    │
    ├── 3. Evidence Fetcher: 콘텐츠 추출 (LinkedIn은 메타데이터만)
    │
    ├── 4. LLM Extractor: Person/Claim 추출 (배치 처리)
    │       └── 5개 URL씩 묶어서 1회 LLM 호출
    │
    ├── 5. Identity Resolver: 중복 병합
    │
    └── 6. File Writer: JSON 저장
```

### 4.2 배치 LLM 처리

**문제**: URL당 개별 LLM 호출 시 HuggingFace API rate limit 및 타임아웃 발생

**해결**: 여러 URL 콘텐츠를 하나의 프롬프트에 묶어서 호출

| 설정 | 값 | 설명 |
|------|------|------|
| BATCH_SIZE | 5 | 1회 호출당 최대 URL 수 |
| CONTENT_PER_URL | 800자 | URL당 최대 콘텐츠 길이 |
| max_new_tokens | 2048 | 배치 응답 최대 토큰 |

**효과**:
- API 호출 횟수: 10회 → 2회 (80% 감소)
- Rate limit 회피
- 총 처리 시간: ~60초 → ~15초

### 4.3 Identity Resolution

**Blocking Keys** (후보 매칭 기준):
- LinkedIn URL
- Email
- Phone
- Name + Company
- Name + Education
- Personal Website

**Scoring Threshold**:
| 점수 | 처리 |
|------|------|
| ≥ 0.90 | 기존 Expert에 병합 |
| 0.75–0.90 | 리뷰 필요 (v1: 새로 생성) |
| < 0.75 | 새 Expert 생성 |

---

## 5. Frontend 구조

### 5.1 파일

```
frontend/
├── index.html    # 메인 (Cytoscape.js CDN 로드)
├── app.js        # 앱 로직
├── api.js        # API 클라이언트
├── graph.js      # 그래프 렌더링
├── i18n.js       # 다국어 지원 (ko, en)
└── style.css     # 스타일
```

### 5.2 다국어 지원 (i18n)

**지원 언어**: 한국어(ko), 영어(en)

**동작 방식**:
1. 브라우저 언어 자동 감지 (`navigator.language`)
2. 한국어 → ko, 그 외 → en
3. UI 텍스트는 `data-i18n` 속성으로 관리
4. 세션 생성 시 감지된 언어로 API 호출

**수동 전환**: `I18n.setLanguage('en')` 또는 `I18n.setLanguage('ko')`

### 5.3 Cytoscape.js 설정

**로드**:
```html
<script src="https://unpkg.com/cytoscape@latest/dist/cytoscape.min.js"></script>
```

**노드 스타일**:
| 타입 | 모양 | 색상 | 크기 |
|------|------|------|------|
| Expert | 원 | #4A90D9 | evidenceCount 비례 |
| Company | 사각형 | #7B68EE | 고정 |

**레이아웃**: `cose` (force-directed)

---

## 6. 기술 결정 로그 (ADR)

### ADR-001: Cytoscape.js 선택

**결정**: v1 그래프 UI는 Cytoscape.js만 사용

**이유**:
- Vanilla JS 호환
- CDN 로드 가능 (빌드 불필요)
- 충분한 기능 (노드/엣지, 레이아웃, 이벤트)

**대안 (vNext 검토)**:
- D3.js: 저수준, 학습 곡선 높음
- force-graph: WebGL 복잡도

### ADR-002: FastAPI Thin Wrapper

**결정**: API 레이어에 비즈니스 로직 금지

**이유**:
- Core 테스트 용이
- CLI와 API 동일 로직 공유
- 관심사 분리

### ADR-003: JSON 파일 저장 (v1)

**결정**: 데이터베이스 없이 JSON 파일로 저장

**이유**:
- MVP 속도 우선
- 디버깅 용이 (파일 직접 확인)
- vNext에서 DB 도입 예정

### ADR-004: 배치 LLM 호출

**결정**: 여러 URL 콘텐츠를 묶어서 1회 LLM 호출

**이유**:
- HuggingFace 무료 tier rate limit 회피
- 개별 호출 시 타임아웃 문제 발생 (URL당 5-6초 × 10개 = 60초+)
- 배치 처리로 API 호출 80% 감소

**설정**:
- 5개 URL씩 배치
- URL당 800자로 콘텐츠 제한
- 토큰 제한 내에서 최대 효율

### ADR-005: 브라우저 기반 i18n

**결정**: 서버 사이드 없이 클라이언트에서 다국어 처리

**이유**:
- Vanilla JS 제약 (빌드 없음)
- 정적 호스팅 가능 (Render Static Site)
- 번역 키 관리 단순화

**구현**:
- `i18n.js`에 번역 객체 포함
- `data-i18n` 속성으로 DOM 바인딩
- 브라우저 언어 자동 감지

---

## 7. 개발 환경

| 항목 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| API | FastAPI + uvicorn |
| LLM | HuggingFace Inference API |
| 검색 | DuckDuckGo (duckduckgo-search) |
| 그래프 | Cytoscape.js (CDN) |
| 저장 | JSON 파일 (out/) |
| 테스트 | pytest |
