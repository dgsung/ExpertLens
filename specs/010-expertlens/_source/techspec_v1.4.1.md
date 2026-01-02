ExpertLens
Search-Grounded, Explainable Expert Discovery
Technical Specification v1.4.1 (Pilot / DuckDuckGo-First)
0. 문서 성격과 사용 목적
본 문서는 ExpertLens 파일럿 시스템의 구현 기준 Tech Spec이다.
마케팅/IR 문서가 아니며, 특정 직업군을 직접 언급하지 않는다.

다만 본 시스템은 다음과 같은 **행동·결정 패턴을 설계 제약(Design Constraints)**으로 전제한다.

결과는 외부 이해관계자에게 설명 가능해야 한다

전문가는 개별 인물(Entity) 단위로 파악되어야 한다

회사 스콥은 고정값이 아니라 조정 가능한 변수다

전문성의 신뢰도(유명함) 와 연락 가능성(실행력) 은 서로 다른 1급 신호다

탐색은 단발성이 아니라 세션 단위로 누적·정제된다

이 제약은 이후 모든 아키텍처, 데이터 모델, UX 결정의 근거로 사용된다.

1. 시스템 목적 (Purpose)
ExpertLens는 사용자의 자연어 요구를 입력으로 받아:

요구를 Preference Stack으로 구조화하고

공개 웹 검색을 통해 근거(Evidence) 를 수집하며

근거 기반으로 전문가를 단일 Expert 엔티티로 정규화하고

그 결과를 설명 가능한 그래프 UI로 제공하는

Search-grounded Expert Discovery System이다.

2. 핵심 설계 원칙 (Design Constraints)
2.1 Explainability by Default
모든 Expert 결과는
Employment / Contact / Merge 근거를 Evidence URL로 역추적할 수 있어야 한다.

UI는 이 근거를 숨기지 않고 명시적으로 노출한다.

2.2 Company Scope is a Variable
회사 스콥은 필수 / 가점 / 무관으로 설정 가능해야 한다.

결과가 빈약할 경우, 시스템은 **스콥 확장(지역/회사 유형)**을 제안할 수 있다.

2.3 Credibility & Contactability are Orthogonal
유명함/신뢰도(근거의 양·질·최근성)

연락 가능성(활성 Contact 존재 여부)

두 신호는 독립적으로 관리되며, UI/랭킹/필터에 각각 반영된다.

2.4 Incremental Discovery
하나의 세션은 단발 질의가 아니라
전문가 그래프를 점진적으로 확장·정제하는 작업 단위다.

3. 언어 정책 (Language Policy)
입력 언어 = 출력 언어

세션 단위로 session.language 유지

모든 UI 텍스트/질문/요약은 이 언어를 따른다

Orchestrator는 모든 LLM 호출에 output_language를 명시한다

4. 전체 아키텍처
[ Frontend ]
  - Session Sidebar
  - Chat / Timeline
  - Graph UI
  - Detail Panel

[ Backend (Non-LLM) ]
  - Orchestrator (SSOT)
  - Search Planner
  - DuckDuckGo Search Adapter
  - Evidence Store
  - Identity Resolution Engine
  - Graph Writer (Neo4j AuraDB Free)

[ Backend (LLM) ]
  - Requirement Clarifier
  - Evidence Extractor
  - (Optional) Search Router
LLM은 해석·추출만 수행한다.
흐름 제어·판단·저장은 전부 Non-LLM Backend가 담당한다.

5. UI/UX 구조 (수평 분할)
좌 → 우 수평 레이아웃

Session Sidebar

ChatGPT 스타일

요청 유사도 기반 자동 그룹핑

세션명: intent_summary + 키워드

Chat / Timeline

사용자 입력

Clarification 질문(버튼)

단계별 이벤트 로그(침묵 금지)

Graph UI (메인)

Expert 단일 엔티티

Company 중심 클러스터

노드 크기: 신뢰도/근거 수

노드 테두리/아이콘: 연락 가능 여부

필터: 지역, 역할, 기술, 소스, 연락 가능

Detail Panel

Expert/Company 클릭 시

Claim + Evidence URL

Contact 정보(출처 포함)

MergeDecision 요약(선택)

6. Requirement Clarification (LLM)
입력: 자연어 요구

출력: ClarificationDraft(JSON)

범위:

Functional / Industry / Value Chain

Company Scope(지역, 회사 경험 필요 여부)

UX 규칙:

질문은 한 번에 하나

“선도사” 같은 표현은 기본 가정 + 가정 노출

7. Search 전략 (DuckDuckGo-First)
7.1 Search Router (LLM, 권고용)
LLM은 소스 가중치만 제안한다.

{
  "linkedin": 0.7,
  "patents": 0.6,
  "papers": 0.3,
  "news": 0.4,
  "conference": 0.5
}
7.2 Search Execution 정책
자료	방식
LinkedIn	DuckDuckGo site:linkedin.com/in
Facebook / X / Instagram	DuckDuckGo
개인 웹사이트	DuckDuckGo
뉴스	DuckDuckGo
컨퍼런스	DuckDuckGo
PDF / Whitepaper	DuckDuckGo
YouTube	DuckDuckGo
책	Open Library API
특허	PatentsView API + DDG
논문	OpenAlex API + DDG
8. Evidence 정책
URL 하나 = Evidence 하나

하나의 Evidence에서 여러 Expert가 추출될 수 있음

필수 필드: url, platform, retrieved_at

비공개/로그인 페이지 제외

9. Claim 전략 (Ultra-Minimal, v1 고정)
v1에서 사용하는 Claim (딱 3개)
EmploymentClaim

Expert ↔ Company (기간/역할)

ContactClaim

Expert ↔ ContactPoint (active/deprecated)

MergeDecision

동일인 판별 감사 로그

그 외 정보(기술/스킬/학력)는 Evidence 기반 attribute로 관리한다.

10. Identity Resolution (DB Write 전)
Blocking Keys:

LinkedIn URL, Email, Phone, Name+Company, Name+Education, Personal Site

Threshold:

≥ 0.90 attach

0.75–0.90 review(v1은 new)

< 0.75 new

모든 결정은 MergeDecision으로 기록

11. Graph DB
Neo4j AuraDB Free

Canonical Expert 유지

Claim append 방식(이력 누적)

12. 업데이트 정책
기존 Expert:

Evidence 추가

Claim append

신규 Expert:

Expert 생성 + Claim 생성

수정(update) 대신 이력 누적

13. 세션 관리
세션 단위로 탐색 상태 유지

Evidence/Expert 누적

임베딩 기반 자동 그룹핑

14. 파일럿 개발 환경
Dev: 로컬 + GitHub Codespaces

LLM: Hugging Face Inference

Graph: Neo4j AuraDB Free

Search: DuckDuckGo HTML

API: 키 없는 오픈 API만 허용

15. Backlog (vNext)
로그인 / 사용자 인증

UX 최적화(그래프 안정화, progressive rendering)

성능 최적화(캐싱, 배치, 인덱스)

Review bucket 병합 UI

Export / CRM 연동

Appendix A: End-to-End Process Flow
User Input
자연어 요구 입력 → 세션 생성

Clarification
LLM이 요구를 구조화 → 필요 시 질문 1개

Preference Stack 확정
검색 파라미터 생성

Search
DuckDuckGo / 오픈 API로 URL 수집

Evidence Ingest
URL → Evidence 저장

LLM Extraction
Evidence → PersonCandidate + Claims(스테이징)

Identity Resolution
기존 DB 조회 → attach/new 결정

Graph Write
Canonical Expert 업데이트 + Claim 생성

UI Update
그래프/상세 정보 반영

Appendix B: Minimal Ontology & Data Model
Entities
Expert

Company

Evidence

ContactPoint

Claims
EmploymentClaim

ContactClaim

MergeDecision

Relations
Expert — employed_at — Company (EmploymentClaim)

Expert — has_contact — ContactPoint (ContactClaim)

Expert — supported_by — Evidence

MergeDecision — updates — Expert
