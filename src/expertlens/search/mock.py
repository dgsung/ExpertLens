"""Mock search provider for ExpertLens M010-1."""

import uuid
from datetime import datetime, timezone

from ..models import (
    Company,
    ContactClaim,
    EmploymentClaim,
    Evidence,
    Expert,
)


class MockSearchProvider:
    """Provides mock search results for testing.

    This provider returns hardcoded data to validate the session JSON schema
    and end-to-end flow without actual web searches.
    """

    def __init__(self, language: str = "ko"):
        self.language = language

    def search(self, query: str) -> dict:
        """Execute mock search and return structured results.

        Args:
            query: The search query (ignored in mock).

        Returns:
            Dictionary with experts, companies, and evidence.
        """
        if self.language == "ko":
            return self._get_korean_mock_data()
        else:
            return self._get_english_mock_data()

    def _get_korean_mock_data(self) -> dict:
        """Return Korean mock data for battery expert search."""
        now = datetime.now(timezone.utc)

        # Evidence (최소 3개)
        evidence_1 = Evidence(
            evidence_id=str(uuid.uuid4()),
            url="https://linkedin.com/in/hong-gildong-battery",
            platform="linkedin",
            retrieved_at=now,
            title="홍길동 - 삼성SDI 수석연구원",
            snippet="배터리 소재 전문가, 리튬이온 배터리 연구 15년 경력",
        )

        evidence_2 = Evidence(
            evidence_id=str(uuid.uuid4()),
            url="https://linkedin.com/in/kim-chulsoo-battery",
            platform="linkedin",
            retrieved_at=now,
            title="김철수 - LG에너지솔루션 책임연구원",
            snippet="전고체 배터리 개발팀, 특허 30건 보유",
        )

        evidence_3 = Evidence(
            evidence_id=str(uuid.uuid4()),
            url="https://news.example.com/battery-conference-2025",
            platform="news",
            retrieved_at=now,
            title="2025 배터리 컨퍼런스 주요 발표자 명단",
            snippet="홍길동(삼성SDI), 김철수(LG에너지솔루션) 등 국내 배터리 전문가 발표 예정",
        )

        evidence_4 = Evidence(
            evidence_id=str(uuid.uuid4()),
            url="https://patents.example.com/KR20250001234",
            platform="patent",
            retrieved_at=now,
            title="리튬이온 배터리 양극재 조성물",
            snippet="발명자: 홍길동, 출원인: 삼성SDI",
        )

        # Companies (최소 2개)
        company_samsung = Company(
            company_id=str(uuid.uuid4()),
            name="삼성SDI",
            domain="samsungsdi.com",
            region="KR",
        )

        company_lg = Company(
            company_id=str(uuid.uuid4()),
            name="LG에너지솔루션",
            domain="lgensol.com",
            region="KR",
        )

        # Experts (최소 2명)
        expert_hong = Expert(
            expert_id=str(uuid.uuid4()),
            canonical_name="홍길동",
            claims=[
                EmploymentClaim(
                    company="삼성SDI",
                    company_id=company_samsung.company_id,
                    role="수석연구원",
                    start_date="2015-03",
                    end_date="present",
                    evidence_id=evidence_1.evidence_id,
                ),
                ContactClaim(
                    contact_type="linkedin",
                    contact_value="https://linkedin.com/in/hong-gildong-battery",
                    status="active",
                    evidence_id=evidence_1.evidence_id,
                ),
            ],
            evidence_ids=[
                evidence_1.evidence_id,
                evidence_3.evidence_id,
                evidence_4.evidence_id,
            ],
            created_at=now,
            updated_at=now,
        )

        expert_kim = Expert(
            expert_id=str(uuid.uuid4()),
            canonical_name="김철수",
            claims=[
                EmploymentClaim(
                    company="LG에너지솔루션",
                    company_id=company_lg.company_id,
                    role="책임연구원",
                    start_date="2018-07",
                    end_date="present",
                    evidence_id=evidence_2.evidence_id,
                ),
                ContactClaim(
                    contact_type="linkedin",
                    contact_value="https://linkedin.com/in/kim-chulsoo-battery",
                    status="active",
                    evidence_id=evidence_2.evidence_id,
                ),
            ],
            evidence_ids=[evidence_2.evidence_id, evidence_3.evidence_id],
            created_at=now,
            updated_at=now,
        )

        return {
            "experts": [expert_hong, expert_kim],
            "companies": [company_samsung, company_lg],
            "evidence": [evidence_1, evidence_2, evidence_3, evidence_4],
        }

    def _get_english_mock_data(self) -> dict:
        """Return English mock data."""
        now = datetime.now(timezone.utc)

        evidence_1 = Evidence(
            evidence_id=str(uuid.uuid4()),
            url="https://linkedin.com/in/john-smith-battery",
            platform="linkedin",
            retrieved_at=now,
            title="John Smith - Senior Researcher at Tesla",
            snippet="Battery materials expert, 12 years experience in lithium-ion technology",
        )

        evidence_2 = Evidence(
            evidence_id=str(uuid.uuid4()),
            url="https://linkedin.com/in/jane-doe-energy",
            platform="linkedin",
            retrieved_at=now,
            title="Jane Doe - Principal Scientist at CATL",
            snippet="Solid-state battery development lead, 25 patents",
        )

        evidence_3 = Evidence(
            evidence_id=str(uuid.uuid4()),
            url="https://news.example.com/battery-summit-2025",
            platform="news",
            retrieved_at=now,
            title="Battery Summit 2025 Speaker Lineup",
            snippet="John Smith (Tesla), Jane Doe (CATL) among keynote speakers",
        )

        company_tesla = Company(
            company_id=str(uuid.uuid4()),
            name="Tesla",
            domain="tesla.com",
            region="US",
        )

        company_catl = Company(
            company_id=str(uuid.uuid4()),
            name="CATL",
            domain="catl.com",
            region="CN",
        )

        expert_john = Expert(
            expert_id=str(uuid.uuid4()),
            canonical_name="John Smith",
            claims=[
                EmploymentClaim(
                    company="Tesla",
                    company_id=company_tesla.company_id,
                    role="Senior Researcher",
                    start_date="2019-01",
                    end_date="present",
                    evidence_id=evidence_1.evidence_id,
                ),
            ],
            evidence_ids=[evidence_1.evidence_id, evidence_3.evidence_id],
            created_at=now,
            updated_at=now,
        )

        expert_jane = Expert(
            expert_id=str(uuid.uuid4()),
            canonical_name="Jane Doe",
            claims=[
                EmploymentClaim(
                    company="CATL",
                    company_id=company_catl.company_id,
                    role="Principal Scientist",
                    start_date="2017-05",
                    end_date="present",
                    evidence_id=evidence_2.evidence_id,
                ),
            ],
            evidence_ids=[evidence_2.evidence_id, evidence_3.evidence_id],
            created_at=now,
            updated_at=now,
        )

        return {
            "experts": [expert_john, expert_jane],
            "companies": [company_tesla, company_catl],
            "evidence": [evidence_1, evidence_2, evidence_3],
        }
