"""Unit tests for search module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expertlens.search import MockSearchProvider, SearchPlanner
from expertlens.models import Expert, Company, Evidence


class TestMockSearchProvider:
    """Tests for MockSearchProvider."""

    def test_korean_search_returns_experts(self) -> None:
        """Test Korean mock search returns at least 2 experts."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("배터리 전문가")

        assert "experts" in results
        assert len(results["experts"]) >= 2

    def test_korean_search_returns_evidence(self) -> None:
        """Test Korean mock search returns at least 3 evidence items."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("배터리 전문가")

        assert "evidence" in results
        assert len(results["evidence"]) >= 3

    def test_korean_search_returns_companies(self) -> None:
        """Test Korean mock search returns companies."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("배터리 전문가")

        assert "companies" in results
        assert len(results["companies"]) >= 2

    def test_english_search_returns_data(self) -> None:
        """Test English mock search returns data."""
        provider = MockSearchProvider(language="en")
        results = provider.search("battery expert")

        assert len(results["experts"]) >= 2
        assert len(results["evidence"]) >= 3
        assert len(results["companies"]) >= 2

    def test_experts_are_expert_instances(self) -> None:
        """Test that returned experts are Expert model instances."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("test")

        for expert in results["experts"]:
            assert isinstance(expert, Expert)

    def test_companies_are_company_instances(self) -> None:
        """Test that returned companies are Company model instances."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("test")

        for company in results["companies"]:
            assert isinstance(company, Company)

    def test_evidence_are_evidence_instances(self) -> None:
        """Test that returned evidence are Evidence model instances."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("test")

        for evidence in results["evidence"]:
            assert isinstance(evidence, Evidence)

    def test_experts_have_claims_with_evidence_ids(self) -> None:
        """Test that experts have claims linked to evidence."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("test")

        for expert in results["experts"]:
            assert len(expert.claims) > 0
            for claim in expert.claims:
                assert claim.evidence_id is not None

    def test_expert_evidence_ids_exist_in_evidence_list(self) -> None:
        """Test that expert evidence_ids reference actual evidence."""
        provider = MockSearchProvider(language="ko")
        results = provider.search("test")

        evidence_ids = {e.evidence_id for e in results["evidence"]}

        for expert in results["experts"]:
            for eid in expert.evidence_ids:
                assert eid in evidence_ids


class TestSearchPlanner:
    """Tests for SearchPlanner."""

    def test_plan_queries_returns_list(self) -> None:
        """Test that plan_queries returns a list."""
        planner = SearchPlanner(language="ko")
        queries = planner.plan_queries("배터리 전문가")

        assert isinstance(queries, list)
        assert len(queries) > 0

    def test_plan_queries_includes_linkedin(self) -> None:
        """Test that plan includes LinkedIn source."""
        planner = SearchPlanner(language="ko")
        queries = planner.plan_queries("test")

        sources = [q.source for q in queries]
        assert "linkedin" in sources

    def test_search_query_has_required_fields(self) -> None:
        """Test that SearchQuery has required fields."""
        planner = SearchPlanner(language="ko")
        queries = planner.plan_queries("test")

        for query in queries:
            assert hasattr(query, "query")
            assert hasattr(query, "source")
            assert hasattr(query, "weight")
