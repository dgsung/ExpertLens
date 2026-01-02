"""Tests for identity resolution module."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expertlens.identity import IdentityResolver
from expertlens.models import EmploymentClaim, ContactClaim, Expert


class TestIdentityResolver:
    """Tests for IdentityResolver class."""

    @pytest.fixture
    def resolver(self):
        return IdentityResolver()

    @pytest.fixture
    def sample_expert(self):
        now = datetime.now(timezone.utc)
        return Expert(
            expert_id="test-id-1",
            canonical_name="홍길동",
            claims=[
                EmploymentClaim(
                    company="삼성SDI",
                    company_id="company-1",
                    role="수석연구원",
                    evidence_id="ev-1",
                )
            ],
            evidence_ids=["ev-1"],
            created_at=now,
            updated_at=now,
        )

    def test_resolve_empty_list(self, resolver):
        result = resolver.resolve([])
        assert result == []

    def test_resolve_single_expert(self, resolver, sample_expert):
        result = resolver.resolve([sample_expert])
        assert len(result) == 1
        assert result[0].canonical_name == "홍길동"

    def test_resolve_merges_same_name(self, resolver):
        now = datetime.now(timezone.utc)
        expert1 = Expert(
            expert_id="id-1",
            canonical_name="홍길동",
            claims=[
                EmploymentClaim(
                    company="삼성SDI",
                    company_id="c-1",
                    role="연구원",
                    evidence_id="ev-1",
                )
            ],
            evidence_ids=["ev-1"],
            created_at=now,
            updated_at=now,
        )
        expert2 = Expert(
            expert_id="id-2",
            canonical_name="홍길동",
            claims=[
                ContactClaim(
                    contact_type="linkedin",
                    contact_value="linkedin.com/in/hong",
                    evidence_id="ev-2",
                )
            ],
            evidence_ids=["ev-2"],
            created_at=now,
            updated_at=now,
        )

        result = resolver.resolve([expert1, expert2])

        assert len(result) == 1
        assert result[0].canonical_name == "홍길동"
        assert len(result[0].claims) == 2
        assert len(result[0].evidence_ids) == 2

    def test_resolve_case_insensitive(self, resolver):
        now = datetime.now(timezone.utc)
        expert1 = Expert(
            expert_id="id-1",
            canonical_name="John Smith",
            claims=[],
            evidence_ids=["ev-1"],
            created_at=now,
            updated_at=now,
        )
        expert2 = Expert(
            expert_id="id-2",
            canonical_name="john smith",
            claims=[],
            evidence_ids=["ev-2"],
            created_at=now,
            updated_at=now,
        )

        result = resolver.resolve([expert1, expert2])

        assert len(result) == 1
        assert len(result[0].evidence_ids) == 2

    def test_resolve_keeps_different_names_separate(self, resolver):
        now = datetime.now(timezone.utc)
        expert1 = Expert(
            expert_id="id-1",
            canonical_name="홍길동",
            claims=[],
            evidence_ids=["ev-1"],
            created_at=now,
            updated_at=now,
        )
        expert2 = Expert(
            expert_id="id-2",
            canonical_name="김철수",
            claims=[],
            evidence_ids=["ev-2"],
            created_at=now,
            updated_at=now,
        )

        result = resolver.resolve([expert1, expert2])

        assert len(result) == 2
        names = {e.canonical_name for e in result}
        assert names == {"홍길동", "김철수"}

    def test_normalize_name_removes_punctuation(self, resolver):
        assert resolver._normalize_name("Dr. John Smith") == "dr john smith"
        assert resolver._normalize_name("Smith, John") == "smith john"

    def test_normalize_name_handles_korean(self, resolver):
        assert resolver._normalize_name("홍길동") == "홍길동"
        assert resolver._normalize_name("  홍길동  ") == "홍길동"

    def test_merge_deduplicates_claims(self, resolver):
        now = datetime.now(timezone.utc)
        claim = EmploymentClaim(
            company="삼성SDI",
            company_id="c-1",
            role="연구원",
            evidence_id="ev-1",
        )
        expert1 = Expert(
            expert_id="id-1",
            canonical_name="홍길동",
            claims=[claim],
            evidence_ids=["ev-1"],
            created_at=now,
            updated_at=now,
        )
        expert2 = Expert(
            expert_id="id-2",
            canonical_name="홍길동",
            claims=[claim],
            evidence_ids=["ev-1"],
            created_at=now,
            updated_at=now,
        )

        result = resolver.resolve([expert1, expert2])

        assert len(result) == 1
        assert len(result[0].claims) == 1

    def test_find_matches(self, resolver, sample_expert):
        now = datetime.now(timezone.utc)
        other = Expert(
            expert_id="id-2",
            canonical_name="김철수",
            claims=[],
            evidence_ids=[],
            created_at=now,
            updated_at=now,
        )

        candidate = Expert(
            expert_id="id-3",
            canonical_name="홍길동",
            claims=[],
            evidence_ids=[],
            created_at=now,
            updated_at=now,
        )

        matches = resolver.find_matches(candidate, [sample_expert, other])

        assert len(matches) == 1
        assert matches[0].expert_id == sample_expert.expert_id

    def test_merge_into_existing(self, resolver):
        now = datetime.now(timezone.utc)
        existing = [
            Expert(
                expert_id="id-1",
                canonical_name="홍길동",
                claims=[],
                evidence_ids=["ev-1"],
                created_at=now,
                updated_at=now,
            )
        ]
        new_experts = [
            Expert(
                expert_id="id-2",
                canonical_name="홍길동",
                claims=[],
                evidence_ids=["ev-2"],
                created_at=now,
                updated_at=now,
            ),
            Expert(
                expert_id="id-3",
                canonical_name="김철수",
                claims=[],
                evidence_ids=["ev-3"],
                created_at=now,
                updated_at=now,
            ),
        ]

        result = resolver.merge_into_existing(new_experts, existing)

        assert len(result) == 2
        hong = next(e for e in result if "홍길동" in e.canonical_name)
        assert len(hong.evidence_ids) == 2
