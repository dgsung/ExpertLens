"""Evidence extractor using LLM for ExpertLens."""

import uuid
from datetime import datetime, timezone
from typing import Any

from ..models import (
    Company,
    ContactClaim,
    EmploymentClaim,
    Evidence,
    Expert,
)
from .client import HuggingFaceClient


class PersonCandidate:
    """A candidate person extracted from evidence before identity resolution."""

    def __init__(
        self,
        name: str,
        employment: list[dict] | None = None,
        contacts: list[dict] | None = None,
        evidence_id: str | None = None,
    ):
        self.name = name
        self.employment = employment or []
        self.contacts = contacts or []
        self.evidence_id = evidence_id


class EvidenceExtractor:
    """Extracts person candidates and claims from evidence using LLM."""

    EXTRACTION_PROMPT = """You are an expert extraction system. Extract all people mentioned in the following text, along with their employment and contact information.

Text:
{content}

Extract the information and respond with ONLY a JSON object in this exact format:
{{
  "persons": [
    {{
      "name": "Person's full name",
      "employment": [
        {{
          "company": "Company name",
          "role": "Job title or role",
          "start_date": "YYYY-MM or null",
          "end_date": "YYYY-MM or 'present' or null"
        }}
      ],
      "contacts": [
        {{
          "type": "linkedin|email|phone|website",
          "value": "contact value"
        }}
      ]
    }}
  ],
  "companies": [
    {{
      "name": "Company name",
      "domain": "company domain or null",
      "region": "country code like KR, US, CN or null"
    }}
  ]
}}

If no persons are found, return {{"persons": [], "companies": []}}.
Respond with ONLY the JSON, no other text."""

    def __init__(self, client: HuggingFaceClient | None = None, language: str = "ko"):
        """Initialize extractor.

        Args:
            client: HuggingFace client instance. Creates new one if None.
            language: Output language for responses.
        """
        self.client = client or HuggingFaceClient()
        self.language = language
        self._owns_client = client is None

    def extract_from_evidence(
        self, evidence: Evidence, content: str
    ) -> dict[str, Any]:
        """Extract persons and companies from evidence content.

        Args:
            evidence: The Evidence object with metadata.
            content: The text content to extract from.

        Returns:
            Dictionary with 'persons' (list of PersonCandidate) and
            'companies' (list of Company).
        """
        if not content or len(content.strip()) < 50:
            return {"persons": [], "companies": []}

        # Truncate very long content
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        prompt = self.EXTRACTION_PROMPT.format(content=content)

        try:
            result = self.client.extract_json(prompt)
        except (ValueError, RuntimeError) as e:
            # Fallback: return empty if LLM fails
            print(f"LLM extraction failed: {e}")
            return {"persons": [], "companies": []}

        # Parse persons
        persons = []
        for p in result.get("persons", []):
            if not p.get("name"):
                continue
            candidate = PersonCandidate(
                name=p["name"],
                employment=p.get("employment", []),
                contacts=p.get("contacts", []),
                evidence_id=evidence.evidence_id,
            )
            persons.append(candidate)

        # Parse companies
        companies = []
        for c in result.get("companies", []):
            if not c.get("name"):
                continue
            company = Company(
                company_id=str(uuid.uuid4()),
                name=c["name"],
                domain=c.get("domain"),
                region=c.get("region"),
            )
            companies.append(company)

        return {"persons": persons, "companies": companies}

    def candidates_to_experts(
        self,
        candidates: list[PersonCandidate],
        companies: list[Company],
    ) -> list[Expert]:
        """Convert PersonCandidates to Expert models with claims.

        Args:
            candidates: List of extracted person candidates.
            companies: List of extracted companies (for ID lookup).

        Returns:
            List of Expert models with claims attached.
        """
        now = datetime.now(timezone.utc)
        company_map = {c.name.lower(): c for c in companies}

        experts = []
        for candidate in candidates:
            claims: list[EmploymentClaim | ContactClaim] = []

            # Create employment claims
            for emp in candidate.employment:
                company_name = emp.get("company", "")
                company = company_map.get(company_name.lower())
                company_id = company.company_id if company else str(uuid.uuid4())

                # Add company if not in map
                if not company and company_name:
                    company = Company(
                        company_id=company_id,
                        name=company_name,
                    )
                    company_map[company_name.lower()] = company
                    companies.append(company)

                claims.append(
                    EmploymentClaim(
                        company=company_name,
                        company_id=company_id,
                        role=emp.get("role"),
                        start_date=emp.get("start_date"),
                        end_date=emp.get("end_date"),
                        evidence_id=candidate.evidence_id or "",
                    )
                )

            # Create contact claims
            for contact in candidate.contacts:
                claims.append(
                    ContactClaim(
                        contact_type=contact.get("type", "other"),
                        contact_value=contact.get("value", ""),
                        status="active",
                        evidence_id=candidate.evidence_id or "",
                    )
                )

            expert = Expert(
                expert_id=str(uuid.uuid4()),
                canonical_name=candidate.name,
                claims=claims,
                evidence_ids=[candidate.evidence_id] if candidate.evidence_id else [],
                created_at=now,
                updated_at=now,
            )
            experts.append(expert)

        return experts

    def close(self) -> None:
        """Close the LLM client if owned."""
        if self._owns_client and self.client:
            self.client.close()

    def __enter__(self) -> "EvidenceExtractor":
        return self

    def __exit__(self, *args) -> None:
        self.close()
