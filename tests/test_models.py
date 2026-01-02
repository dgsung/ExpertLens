"""Unit tests for data models."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expertlens.models import (
    Company,
    ContactClaim,
    EmploymentClaim,
    Evidence,
    Expert,
    Query,
    Session,
)


class TestEvidence:
    """Tests for Evidence model."""

    def test_evidence_creation(self) -> None:
        """Test creating an Evidence instance."""
        now = datetime.now(timezone.utc)
        evidence = Evidence(
            evidence_id="test-id",
            url="https://example.com",
            platform="linkedin",
            retrieved_at=now,
        )

        assert evidence.evidence_id == "test-id"
        assert evidence.url == "https://example.com"
        assert evidence.platform == "linkedin"
        assert evidence.retrieved_at == now
        assert evidence.title is None
        assert evidence.snippet is None

    def test_evidence_with_optional_fields(self) -> None:
        """Test Evidence with optional fields."""
        now = datetime.now(timezone.utc)
        evidence = Evidence(
            evidence_id="test-id",
            url="https://example.com",
            platform="news",
            retrieved_at=now,
            title="Test Article",
            snippet="This is a test snippet.",
        )

        assert evidence.title == "Test Article"
        assert evidence.snippet == "This is a test snippet."

    def test_evidence_json_serialization(self) -> None:
        """Test Evidence JSON serialization."""
        now = datetime.now(timezone.utc)
        evidence = Evidence(
            evidence_id="test-id",
            url="https://example.com",
            platform="linkedin",
            retrieved_at=now,
        )

        data = evidence.model_dump(mode="json")
        assert data["evidence_id"] == "test-id"
        assert data["url"] == "https://example.com"
        assert "retrieved_at" in data


class TestCompany:
    """Tests for Company model."""

    def test_company_creation(self) -> None:
        """Test creating a Company instance."""
        company = Company(
            company_id="company-1",
            name="Test Corp",
        )

        assert company.company_id == "company-1"
        assert company.name == "Test Corp"
        assert company.domain is None
        assert company.region is None

    def test_company_with_optional_fields(self) -> None:
        """Test Company with optional fields."""
        company = Company(
            company_id="company-1",
            name="삼성SDI",
            domain="samsungsdi.com",
            region="KR",
        )

        assert company.domain == "samsungsdi.com"
        assert company.region == "KR"


class TestClaims:
    """Tests for Claim models."""

    def test_employment_claim(self) -> None:
        """Test EmploymentClaim creation."""
        claim = EmploymentClaim(
            company="Test Corp",
            company_id="company-1",
            role="Engineer",
            evidence_id="evidence-1",
        )

        assert claim.claim_type == "employment"
        assert claim.company == "Test Corp"
        assert claim.role == "Engineer"
        assert claim.start_date is None
        assert claim.end_date is None

    def test_employment_claim_with_dates(self) -> None:
        """Test EmploymentClaim with date fields."""
        claim = EmploymentClaim(
            company="Test Corp",
            company_id="company-1",
            role="Senior Engineer",
            start_date="2020-01",
            end_date="present",
            evidence_id="evidence-1",
        )

        assert claim.start_date == "2020-01"
        assert claim.end_date == "present"

    def test_contact_claim(self) -> None:
        """Test ContactClaim creation."""
        claim = ContactClaim(
            contact_type="linkedin",
            contact_value="https://linkedin.com/in/test",
            evidence_id="evidence-1",
        )

        assert claim.claim_type == "contact"
        assert claim.contact_type == "linkedin"
        assert claim.status == "active"

    def test_contact_claim_deprecated(self) -> None:
        """Test ContactClaim with deprecated status."""
        claim = ContactClaim(
            contact_type="email",
            contact_value="old@example.com",
            status="deprecated",
            evidence_id="evidence-1",
        )

        assert claim.status == "deprecated"


class TestExpert:
    """Tests for Expert model."""

    def test_expert_creation(self) -> None:
        """Test creating an Expert instance."""
        now = datetime.now(timezone.utc)
        expert = Expert(
            expert_id="expert-1",
            canonical_name="홍길동",
            created_at=now,
            updated_at=now,
        )

        assert expert.expert_id == "expert-1"
        assert expert.canonical_name == "홍길동"
        assert expert.claims == []
        assert expert.evidence_ids == []

    def test_expert_with_claims(self) -> None:
        """Test Expert with claims."""
        now = datetime.now(timezone.utc)
        expert = Expert(
            expert_id="expert-1",
            canonical_name="홍길동",
            claims=[
                EmploymentClaim(
                    company="삼성SDI",
                    company_id="company-1",
                    role="수석연구원",
                    evidence_id="evidence-1",
                ),
            ],
            evidence_ids=["evidence-1"],
            created_at=now,
            updated_at=now,
        )

        assert len(expert.claims) == 1
        assert expert.claims[0].company == "삼성SDI"
        assert len(expert.evidence_ids) == 1


class TestSession:
    """Tests for Session model."""

    def test_session_creation(self) -> None:
        """Test creating a Session instance."""
        now = datetime.now(timezone.utc)
        session = Session(
            session_id="session-1",
            language="ko",
            query="배터리 전문가",
            queries=[Query(query="배터리 전문가", added_at=now)],
            created_at=now,
            updated_at=now,
        )

        assert session.session_id == "session-1"
        assert session.language == "ko"
        assert session.query == "배터리 전문가"
        assert len(session.queries) == 1
        assert session.experts == []
        assert session.companies == []
        assert session.evidence == []

    def test_session_json_has_required_fields(self) -> None:
        """Test Session JSON has all required fields."""
        now = datetime.now(timezone.utc)
        session = Session(
            session_id="session-1",
            language="ko",
            query="test",
            queries=[Query(query="test", added_at=now)],
            created_at=now,
            updated_at=now,
        )

        data = session.model_dump(mode="json")

        # Check required fields from design.md
        assert "session_id" in data
        assert "language" in data
        assert "query" in data
        assert "queries" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "experts" in data
        assert "companies" in data
        assert "evidence" in data

    def test_session_with_full_data(self) -> None:
        """Test Session with experts, companies, and evidence."""
        now = datetime.now(timezone.utc)

        evidence = Evidence(
            evidence_id="evidence-1",
            url="https://example.com",
            platform="linkedin",
            retrieved_at=now,
        )

        company = Company(
            company_id="company-1",
            name="Test Corp",
        )

        expert = Expert(
            expert_id="expert-1",
            canonical_name="Test Person",
            claims=[
                EmploymentClaim(
                    company="Test Corp",
                    company_id="company-1",
                    role="Engineer",
                    evidence_id="evidence-1",
                ),
            ],
            evidence_ids=["evidence-1"],
            created_at=now,
            updated_at=now,
        )

        session = Session(
            session_id="session-1",
            language="en",
            query="test expert",
            queries=[Query(query="test expert", added_at=now)],
            created_at=now,
            updated_at=now,
            experts=[expert],
            companies=[company],
            evidence=[evidence],
        )

        assert len(session.experts) == 1
        assert len(session.companies) == 1
        assert len(session.evidence) == 1

        # Verify JSON serialization works
        data = session.model_dump(mode="json")
        assert len(data["experts"]) == 1
        assert data["experts"][0]["canonical_name"] == "Test Person"
