"""Tests for LLM module."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expertlens.llm import HuggingFaceClient, EvidenceExtractor
from expertlens.llm.extractor import PersonCandidate
from expertlens.models import Evidence, Company


class TestHuggingFaceClient:
    """Tests for HuggingFaceClient class."""

    @pytest.fixture
    def client(self):
        return HuggingFaceClient(api_key="test-key")

    def test_default_model(self, client):
        assert "Mistral" in client.model

    def test_custom_model(self):
        client = HuggingFaceClient(model="custom/model", api_key="test-key")
        assert client.model == "custom/model"

    @patch("httpx.Client.post")
    def test_generate_returns_text(self, mock_post, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "Test output"}]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.generate("Test prompt")
        assert result == "Test output"

    @patch("httpx.Client.post")
    def test_extract_json_parses_response(self, mock_post, client):
        json_output = '{"persons": [{"name": "John"}], "companies": []}'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": json_output}]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.extract_json("Extract persons")
        assert result == {"persons": [{"name": "John"}], "companies": []}

    @patch("httpx.Client.post")
    def test_extract_json_handles_markdown_wrapper(self, mock_post, client):
        json_output = '```json\n{"persons": [], "companies": []}\n```'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": json_output}]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.extract_json("Extract persons")
        assert result == {"persons": [], "companies": []}

    @patch("httpx.Client.post")
    def test_extract_json_raises_on_invalid_json(self, mock_post, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "not valid json"}]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="parse JSON"):
            client.extract_json("Test prompt")


class TestPersonCandidate:
    """Tests for PersonCandidate class."""

    def test_creation(self):
        candidate = PersonCandidate(
            name="홍길동",
            employment=[{"company": "삼성SDI", "role": "연구원"}],
            contacts=[{"type": "email", "value": "hong@example.com"}],
            evidence_id="ev-1",
        )

        assert candidate.name == "홍길동"
        assert len(candidate.employment) == 1
        assert len(candidate.contacts) == 1
        assert candidate.evidence_id == "ev-1"

    def test_default_values(self):
        candidate = PersonCandidate(name="Test Person")

        assert candidate.name == "Test Person"
        assert candidate.employment == []
        assert candidate.contacts == []
        assert candidate.evidence_id is None


class TestEvidenceExtractor:
    """Tests for EvidenceExtractor class."""

    @pytest.fixture
    def mock_client(self):
        return MagicMock(spec=HuggingFaceClient)

    @pytest.fixture
    def extractor(self, mock_client):
        return EvidenceExtractor(client=mock_client)

    @pytest.fixture
    def sample_evidence(self):
        return Evidence(
            evidence_id="ev-1",
            url="https://example.com/article",
            platform="web",
            retrieved_at=datetime.now(timezone.utc),
        )

    def test_extract_from_evidence_empty_content(self, extractor, sample_evidence):
        result = extractor.extract_from_evidence(sample_evidence, "")
        assert result == {"persons": [], "companies": []}

    def test_extract_from_evidence_short_content(self, extractor, sample_evidence):
        result = extractor.extract_from_evidence(sample_evidence, "Too short")
        assert result == {"persons": [], "companies": []}

    def test_extract_from_evidence_calls_llm(
        self, extractor, mock_client, sample_evidence
    ):
        mock_client.extract_json.return_value = {
            "persons": [
                {
                    "name": "홍길동",
                    "employment": [{"company": "삼성SDI", "role": "연구원"}],
                    "contacts": [],
                }
            ],
            "companies": [{"name": "삼성SDI", "domain": "samsungsdi.com", "region": "KR"}],
        }

        content = "홍길동은 삼성SDI의 수석연구원이다. " * 10  # Make it long enough

        result = extractor.extract_from_evidence(sample_evidence, content)

        assert len(result["persons"]) == 1
        assert result["persons"][0].name == "홍길동"
        assert len(result["companies"]) == 1
        assert result["companies"][0].name == "삼성SDI"

    def test_extract_from_evidence_skips_nameless_persons(
        self, extractor, mock_client, sample_evidence
    ):
        mock_client.extract_json.return_value = {
            "persons": [{"name": ""}, {"name": "Valid Name"}],
            "companies": [],
        }

        content = "Some content here. " * 10

        result = extractor.extract_from_evidence(sample_evidence, content)

        assert len(result["persons"]) == 1
        assert result["persons"][0].name == "Valid Name"

    def test_extract_from_evidence_handles_llm_failure(
        self, extractor, mock_client, sample_evidence
    ):
        mock_client.extract_json.side_effect = ValueError("LLM failed")

        content = "Some content here. " * 10

        result = extractor.extract_from_evidence(sample_evidence, content)

        assert result == {"persons": [], "companies": []}

    def test_candidates_to_experts(self, extractor):
        candidates = [
            PersonCandidate(
                name="홍길동",
                employment=[{"company": "삼성SDI", "role": "연구원"}],
                contacts=[{"type": "linkedin", "value": "linkedin.com/in/hong"}],
                evidence_id="ev-1",
            )
        ]
        companies = [
            Company(
                company_id="c-1",
                name="삼성SDI",
                domain="samsungsdi.com",
                region="KR",
            )
        ]

        experts = extractor.candidates_to_experts(candidates, companies)

        assert len(experts) == 1
        expert = experts[0]
        assert expert.canonical_name == "홍길동"
        assert len(expert.claims) == 2  # 1 employment + 1 contact
        assert expert.evidence_ids == ["ev-1"]

    def test_candidates_to_experts_creates_missing_companies(self, extractor):
        candidates = [
            PersonCandidate(
                name="Test Person",
                employment=[{"company": "New Company", "role": "CEO"}],
                contacts=[],
                evidence_id="ev-1",
            )
        ]
        companies: list[Company] = []

        experts = extractor.candidates_to_experts(candidates, companies)

        assert len(experts) == 1
        assert len(experts[0].claims) == 1
        # The company should be added to the list
        assert len(companies) == 1
        assert companies[0].name == "New Company"

    def test_context_manager(self):
        mock_client = MagicMock(spec=HuggingFaceClient)
        with EvidenceExtractor(client=mock_client) as extractor:
            assert extractor is not None
