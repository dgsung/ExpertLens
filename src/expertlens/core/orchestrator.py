"""Pipeline orchestrator for ExpertLens.

This module contains the core business logic for expert discovery.
All API routes should use functions from this module.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..evidence import EvidenceFetcher
from ..identity import IdentityResolver
from ..io.writer import ReportWriter, SessionWriter
from ..llm import EvidenceExtractor, HuggingFaceClient
from ..models import Evidence, Expert, Company, Query, Session
from ..search import MockSearchProvider


class Orchestrator:
    """Main pipeline orchestrator for ExpertLens.

    Coordinates the search, extraction, and output generation flow.
    """

    def __init__(
        self,
        output_dir: Path | str = "out",
        reports_dir: Path | str = "reports",
        use_mock: bool = True,
    ):
        self.session_writer = SessionWriter(output_dir)
        self.report_writer = ReportWriter(reports_dir)
        self.use_mock = use_mock

        # Real extraction components (lazy init)
        self._fetcher: EvidenceFetcher | None = None
        self._llm_client: HuggingFaceClient | None = None
        self._extractor: EvidenceExtractor | None = None
        self._resolver: IdentityResolver | None = None

    @property
    def fetcher(self) -> EvidenceFetcher:
        """Lazy-init URL fetcher."""
        if self._fetcher is None:
            self._fetcher = EvidenceFetcher()
        return self._fetcher

    @property
    def llm_client(self) -> HuggingFaceClient:
        """Lazy-init LLM client."""
        if self._llm_client is None:
            self._llm_client = HuggingFaceClient()
        return self._llm_client

    @property
    def extractor(self) -> EvidenceExtractor:
        """Lazy-init evidence extractor."""
        if self._extractor is None:
            self._extractor = EvidenceExtractor(client=self.llm_client)
        return self._extractor

    @property
    def resolver(self) -> IdentityResolver:
        """Lazy-init identity resolver."""
        if self._resolver is None:
            self._resolver = IdentityResolver()
        return self._resolver

    def run_search(self, query: str, language: str = "ko") -> dict:
        """Execute a search pipeline.

        Args:
            query: The search query string.
            language: The session language (default: "ko").

        Returns:
            Dictionary with session info and output paths.
        """
        now = datetime.now(timezone.utc)
        session_id = str(uuid.uuid4())

        # Execute mock search
        search_provider = MockSearchProvider(language=language)
        results = search_provider.search(query)

        # Build session with results
        session = Session(
            session_id=session_id,
            language=language,
            query=query,
            queries=[Query(query=query, added_at=now)],
            created_at=now,
            updated_at=now,
            experts=results["experts"],
            companies=results["companies"],
            evidence=results["evidence"],
        )

        # Write session JSON
        session_path = self.session_writer.create_session(session)

        # Create run report with counts
        report_path = self.report_writer.create_run_report(
            session_id=session_id,
            query=query,
            language=language,
            expert_count=len(results["experts"]),
            evidence_count=len(results["evidence"]),
            company_count=len(results["companies"]),
        )

        return {
            "session_id": session_id,
            "session_path": str(session_path),
            "report_path": str(report_path),
            "query": query,
            "language": language,
            "expert_count": len(results["experts"]),
            "evidence_count": len(results["evidence"]),
            "company_count": len(results["companies"]),
        }

    def process_urls(
        self,
        urls: list[str],
        session_id: str | None = None,
        language: str = "ko",
    ) -> dict:
        """Fetch URLs and extract experts using LLM.

        Args:
            urls: List of URLs to process.
            session_id: Optional existing session ID to add to.
            language: Session language (default: "ko").

        Returns:
            Dictionary with session info and extraction results.
        """
        now = datetime.now(timezone.utc)
        session_id = session_id or str(uuid.uuid4())

        all_evidence: list[Evidence] = []
        all_experts: list[Expert] = []
        all_companies: list[Company] = []

        for url in urls:
            try:
                # Fetch URL content
                evidence, content = self.fetcher.fetch(url)
                all_evidence.append(evidence)

                # Extract persons and companies using LLM
                extracted = self.extractor.extract_from_evidence(evidence, content)

                # Convert candidates to experts
                experts = self.extractor.candidates_to_experts(
                    extracted["persons"],
                    extracted["companies"],
                )

                all_experts.extend(experts)
                all_companies.extend(extracted["companies"])

            except RuntimeError as e:
                print(f"Failed to process URL {url}: {e}")
                continue

        # Resolve identities (merge duplicates)
        resolved_experts = self.resolver.resolve(all_experts)

        # Build session
        session = Session(
            session_id=session_id,
            language=language,
            query=", ".join(urls[:3]) + ("..." if len(urls) > 3 else ""),
            queries=[Query(query=url, added_at=now) for url in urls],
            created_at=now,
            updated_at=now,
            experts=resolved_experts,
            companies=all_companies,
            evidence=all_evidence,
        )

        # Write session JSON
        session_path = self.session_writer.create_session(session)

        # Create run report
        report_path = self.report_writer.create_run_report(
            session_id=session_id,
            query=f"URL extraction ({len(urls)} URLs)",
            language=language,
            expert_count=len(resolved_experts),
            evidence_count=len(all_evidence),
            company_count=len(all_companies),
        )

        return {
            "session_id": session_id,
            "session_path": str(session_path),
            "report_path": str(report_path),
            "urls_processed": len(all_evidence),
            "urls_failed": len(urls) - len(all_evidence),
            "expert_count": len(resolved_experts),
            "evidence_count": len(all_evidence),
            "company_count": len(all_companies),
        }

    def close(self) -> None:
        """Clean up resources."""
        if self._fetcher:
            self._fetcher.close()
        if self._extractor:
            self._extractor.close()
        if self._llm_client:
            self._llm_client.close()

    def __enter__(self) -> "Orchestrator":
        return self

    def __exit__(self, *args) -> None:
        self.close()
