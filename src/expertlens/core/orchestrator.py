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
from ..models import (
#     Clarification,
#     ClarificationOption,
    Company,
    Evidence,
    Expert,
    ExpertGroup,
    Query,
    SearchStep,
    Session,
)
from ..search import DuckDuckGoSearchProvider, MockSearchProvider


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

    def run_session(
        self,
        session: Session,
        query: str,
        clarification_response: str | None = None,
    ) -> Session:
        """Execute a search and update an existing session.

        This is the core function called by the API layer.

        Args:
            session: Existing session to update.
            query: Search query to execute.
            clarification_response: User's response to clarification (if any).

        Returns:
            Updated Session object with new results.
        """
        now = datetime.now(timezone.utc)

        # Handle clarification response
        if clarification_response and session.status == "clarification_needed":
            return self._handle_clarification_response(
                session, query, clarification_response
            )

        # Check if query needs clarification
        clarification = self._check_for_clarification(query)
        if clarification:
            session.query = query
            session.queries.append(Query(query=query, added_at=now))
            session.updated_at = now
            session.status = "clarification_needed"
            session.clarification = clarification
            self.session_writer.create_session(session)
            return session

        # Update session with new query
        session.query = query
        session.queries.append(Query(query=query, added_at=now))
        session.updated_at = now
        session.status = "searching"
        session.clarification = None

        if self.use_mock:
            # Mock search: returns pre-built experts/companies/evidence
            search_provider = MockSearchProvider(language=session.language)
            results = search_provider.search(query)

            # Merge new results with existing (avoiding duplicates by ID)
            existing_expert_ids = {e.expert_id for e in session.experts}
            existing_company_ids = {c.company_id for c in session.companies}
            existing_evidence_ids = {e.evidence_id for e in session.evidence}

            for expert in results["experts"]:
                if expert.expert_id not in existing_expert_ids:
                    session.experts.append(expert)
                    existing_expert_ids.add(expert.expert_id)

            for company in results["companies"]:
                if company.company_id not in existing_company_ids:
                    session.companies.append(company)
                    existing_company_ids.add(company.company_id)

            for evidence in results["evidence"]:
                if evidence.evidence_id not in existing_evidence_ids:
                    session.evidence.append(evidence)
                    existing_evidence_ids.add(evidence.evidence_id)
        else:
            # Real DuckDuckGo search + LLM extraction pipeline
            search_provider = DuckDuckGoSearchProvider(
                language=session.language,
                max_results=10,
            )

            # Step 1: Search LinkedIn
            linkedin_results = search_provider.search_site(query, "linkedin.com/in")
            session.search_steps.append(SearchStep(
                step_type="search",
                description=f"LinkedIn에서 '{query}' 검색",
                query=f"site:linkedin.com/in {query}",
                source="DuckDuckGo → LinkedIn",
                result_count=len(linkedin_results),
                urls=[e.url for e in linkedin_results[:5]],  # Top 5 for display
                timestamp=now,
            ))

            # Step 2: General search
            general_results = search_provider.search(query)
            session.search_steps.append(SearchStep(
                step_type="search",
                description=f"웹에서 '{query}' 검색",
                query=query,
                source="DuckDuckGo",
                result_count=len(general_results),
                urls=[e.url for e in general_results[:5]],
                timestamp=datetime.now(timezone.utc),
            ))

            # Combine and dedupe
            evidence_list = linkedin_results + general_results
            seen_urls: set[str] = set()
            unique_evidence: list[Evidence] = []
            for ev in evidence_list:
                if ev.url not in seen_urls:
                    unique_evidence.append(ev)
                    seen_urls.add(ev.url)
            evidence_list = unique_evidence[:10]

            # Collect URLs to process
            existing_evidence_urls = {e.url for e in session.evidence}

            # Process URLs: fetch content first, then batch LLM extraction
            all_new_experts: list[Expert] = []
            all_new_companies: list[Company] = []
            processed_urls: list[str] = []
            failed_urls: list[str] = []

            # Step 1: Fetch all content first
            evidence_content_pairs: list[tuple[Evidence, str]] = []

            for evidence in evidence_list:
                if evidence.url in existing_evidence_urls:
                    continue

                try:
                    # Check if LinkedIn URL (use metadata only, skip fetch)
                    is_linkedin = "linkedin.com" in evidence.url.lower()

                    if is_linkedin:
                        # Use DDG search metadata instead of fetching
                        # LinkedIn blocks scraping with 429 errors
                        content = f"Title: {evidence.title or ''}\n\n{evidence.snippet or ''}"
                        session.evidence.append(evidence)
                        existing_evidence_urls.add(evidence.url)
                        processed_urls.append(evidence.url)
                        evidence_content_pairs.append((evidence, content))
                    else:
                        # Fetch URL content for non-LinkedIn sites
                        fetched_evidence, content = self.fetcher.fetch(evidence.url)
                        session.evidence.append(fetched_evidence)
                        existing_evidence_urls.add(evidence.url)
                        processed_urls.append(evidence.url)
                        evidence_content_pairs.append((fetched_evidence, content))

                except Exception as e:
                    print(f"Failed to fetch URL {evidence.url}: {e}")
                    failed_urls.append(evidence.url)
                    # Still add evidence even if fetch failed
                    session.evidence.append(evidence)
                    existing_evidence_urls.add(evidence.url)
                    continue

            # Step 2: Batch LLM extraction (5 URLs per batch to avoid token limits)
            batch_size = self.extractor.BATCH_SIZE
            for i in range(0, len(evidence_content_pairs), batch_size):
                batch = evidence_content_pairs[i:i + batch_size]

                try:
                    extracted = self.extractor.extract_from_evidence_batch(batch)

                    # Convert candidates to experts
                    experts = self.extractor.candidates_to_experts(
                        extracted["persons"],
                        extracted["companies"],
                    )

                    all_new_experts.extend(experts)
                    all_new_companies.extend(extracted["companies"])

                except Exception as e:
                    print(f"Batch extraction failed: {e}")
                    continue

            # Step 3: Fetch & Extract
            session.search_steps.append(SearchStep(
                step_type="extract",
                description=f"{len(processed_urls)}개 페이지에서 전문가 정보 추출 (배치 처리)",
                source="HuggingFace LLM",
                result_count=len(all_new_experts),
                urls=processed_urls[:5],
                timestamp=datetime.now(timezone.utc),
            ))

            # Resolve identities (merge duplicates) for new experts
            if all_new_experts:
                # Combine with existing experts for proper resolution
                combined_experts = list(session.experts) + all_new_experts
                session.experts = self.resolver.resolve(combined_experts)

            # Merge new companies (avoiding duplicates by ID)
            existing_company_ids = {c.company_id for c in session.companies}
            for company in all_new_companies:
                if company.company_id not in existing_company_ids:
                    session.companies.append(company)
                    existing_company_ids.add(company.company_id)

        # Update status and generate expert groups
        session.status = "completed"
        session.expert_groups = self._group_experts(session.experts)

        # Write updated session JSON
        self.session_writer.create_session(session)

        # Create run report
        self.report_writer.create_run_report(
            session_id=session.session_id,
            query=query,
            language=session.language,
            expert_count=len(session.experts),
            evidence_count=len(session.evidence),
            company_count=len(session.companies),
        )

        return session

    def _check_for_clarification(self, query: str) -> Clarification | None:
        """Check if a query needs clarification.

        For now, uses simple keyword matching. In the future, could use LLM.

        Args:
            query: The search query.

        Returns:
            Clarification object if needed, None otherwise.
        """
        query_lower = query.lower()

        # Detect equipment/manufacturer queries that could benefit from broadening
        equipment_keywords = [
            "mixer", "mixing", "equipment", "machine", "machinery",
            "hf mixing", "banbury", "internal mixer",
        ]
        industry_keywords = [
            "rubber", "compound", "compounding", "polymer",
            "tire", "tyre", "automotive",
        ]

        has_equipment = any(kw in query_lower for kw in equipment_keywords)
        has_industry = any(kw in query_lower for kw in industry_keywords)

        if has_equipment and has_industry:
            # Check if query is about rubber compound manufacturers
            if "rubber" in query_lower and "compound" in query_lower:
                return Clarification(
                    question="Would experts from upstream tire manufacturers with HF Mixing Group mixer experience also work?",
                    options=[
                        ClarificationOption(
                            value="yes",
                            label="Yes, include tire manufacturers"
                        ),
                        ClarificationOption(
                            value="no",
                            label="No, only rubber compound manufacturers"
                        ),
                    ]
                )

        return None

    def _handle_clarification_response(
        self,
        session: Session,
        query: str,
        response: str,
    ) -> Session:
        """Handle user's response to a clarification question.

        Args:
            session: The session with pending clarification.
            query: The original query.
            response: User's response ('yes', 'no', or freeform).

        Returns:
            Updated session with search results.
        """
        now = datetime.now(timezone.utc)

        # Normalize response
        response_lower = response.lower().strip()
        is_affirmative = response_lower in [
            "yes", "y", "ok", "okay", "sure", "sounds good", "sounds good!",
            "yep", "yeah", "yes please", "include", "both",
        ]

        # Clear clarification and set status
        session.clarification = None
        session.status = "searching"
        session.updated_at = now

        # Execute search based on response
        if self.use_mock:
            # Generate mock results with grouping based on response
            results = self._generate_grouped_mock_results(
                query, session.language, include_upstream=is_affirmative
            )

            session.experts = results["experts"]
            session.companies = results["companies"]
            session.evidence = results["evidence"]
            session.expert_groups = results["expert_groups"]
            session.status = "completed"
        else:
            # Real search - would expand query based on response
            # For now, just run the regular search
            session = self.run_session(session, query, clarification_response=None)

        # Write session
        self.session_writer.create_session(session)

        return session

    def _generate_grouped_mock_results(
        self,
        query: str,
        language: str,
        include_upstream: bool = True,
    ) -> dict:
        """Generate mock results with expert groups.

        Args:
            query: Search query.
            language: Session language.
            include_upstream: Whether to include upstream tire manufacturers.

        Returns:
            Dictionary with experts, companies, evidence, and expert_groups.
        """
        now = datetime.now(timezone.utc)

        # Rubber Compound Manufacturer experts
        rubber_experts = [
            Expert(
                expert_id="exp-rubber-001",
                canonical_name="Dr. Hans Mueller",
                angle="Rubber Compound Manufacturers",
                industry_tag="rubber-compound",
                evidence_ids=["ev-001", "ev-002"],
                claims=[],
                created_at=now,
                updated_at=now,
            ),
            Expert(
                expert_id="exp-rubber-002",
                canonical_name="Maria Schmidt",
                angle="Rubber Compound Manufacturers",
                industry_tag="rubber-compound",
                evidence_ids=["ev-003"],
                claims=[],
                created_at=now,
                updated_at=now,
            ),
            Expert(
                expert_id="exp-rubber-003",
                canonical_name="Thomas Weber",
                angle="Rubber Compound Manufacturers",
                industry_tag="rubber-compound",
                evidence_ids=["ev-004"],
                claims=[],
                created_at=now,
                updated_at=now,
            ),
        ]

        # Tire Manufacturer (Upstream) experts
        tire_experts = [
            Expert(
                expert_id="exp-tire-001",
                canonical_name="James Kim",
                angle="Tire Manufacturers (Upstream)",
                industry_tag="tire-upstream",
                evidence_ids=["ev-005", "ev-006"],
                claims=[],
                created_at=now,
                updated_at=now,
            ),
            Expert(
                expert_id="exp-tire-002",
                canonical_name="Sarah Johnson",
                angle="Tire Manufacturers (Upstream)",
                industry_tag="tire-upstream",
                evidence_ids=["ev-007"],
                claims=[],
                created_at=now,
                updated_at=now,
            ),
        ]

        # Companies
        companies = [
            Company(company_id="comp-001", name="Continental Rubber GmbH", domain="continental.com"),
            Company(company_id="comp-002", name="Kraiburg TPE", domain="kraiburg-tpe.com"),
            Company(company_id="comp-003", name="Freudenberg Sealing Technologies", domain="fst.com"),
        ]

        if include_upstream:
            companies.extend([
                Company(company_id="comp-004", name="Michelin Korea", domain="michelin.co.kr"),
                Company(company_id="comp-005", name="Bridgestone Americas", domain="bridgestone.com"),
            ])

        # Evidence
        evidence = [
            Evidence(evidence_id="ev-001", url="https://linkedin.com/in/hans-mueller", platform="LinkedIn", retrieved_at=now),
            Evidence(evidence_id="ev-002", url="https://continental.com/team/mueller", platform="Company", retrieved_at=now),
            Evidence(evidence_id="ev-003", url="https://linkedin.com/in/maria-schmidt", platform="LinkedIn", retrieved_at=now),
            Evidence(evidence_id="ev-004", url="https://linkedin.com/in/thomas-weber", platform="LinkedIn", retrieved_at=now),
        ]

        if include_upstream:
            evidence.extend([
                Evidence(evidence_id="ev-005", url="https://linkedin.com/in/james-kim", platform="LinkedIn", retrieved_at=now),
                Evidence(evidence_id="ev-006", url="https://michelin.co.kr/team", platform="Company", retrieved_at=now),
                Evidence(evidence_id="ev-007", url="https://linkedin.com/in/sarah-johnson", platform="LinkedIn", retrieved_at=now),
            ])

        # Combine experts
        all_experts = rubber_experts[:]
        if include_upstream:
            all_experts.extend(tire_experts)

        # Create expert groups
        expert_groups = [
            ExpertGroup(
                group_id="group-rubber-compound",
                label="Rubber Compound Manufacturers",
                angle="rubber-compound",
                expert_ids=[e.expert_id for e in rubber_experts],
                count=len(rubber_experts),
            ),
        ]

        if include_upstream:
            expert_groups.append(
                ExpertGroup(
                    group_id="group-tire-upstream",
                    label="Tire Manufacturers (Upstream)",
                    angle="tire-upstream",
                    expert_ids=[e.expert_id for e in tire_experts],
                    count=len(tire_experts),
                )
            )

        return {
            "experts": all_experts,
            "companies": companies,
            "evidence": evidence,
            "expert_groups": expert_groups,
        }

    def _group_experts(self, experts: list[Expert]) -> list[ExpertGroup]:
        """Group experts by their angle/industry.

        Args:
            experts: List of experts to group.

        Returns:
            List of ExpertGroup objects.
        """
        groups: dict[str, list[str]] = {}
        labels: dict[str, str] = {}

        for expert in experts:
            if expert.industry_tag:
                if expert.industry_tag not in groups:
                    groups[expert.industry_tag] = []
                    labels[expert.industry_tag] = expert.angle or expert.industry_tag
                groups[expert.industry_tag].append(expert.expert_id)

        return [
            ExpertGroup(
                group_id=f"group-{angle}",
                label=labels[angle],
                angle=angle,
                expert_ids=expert_ids,
                count=len(expert_ids),
            )
            for angle, expert_ids in groups.items()
        ]

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
