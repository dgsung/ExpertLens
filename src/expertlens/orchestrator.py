"""Pipeline orchestrator for ExpertLens."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .io.writer import ReportWriter, SessionWriter
from .models import Query, Session
from .search import MockSearchProvider


class Orchestrator:
    """Main pipeline orchestrator for ExpertLens.

    Coordinates the search, extraction, and output generation flow.
    """

    def __init__(
        self,
        output_dir: Path | str = "out",
        reports_dir: Path | str = "reports",
    ):
        self.session_writer = SessionWriter(output_dir)
        self.report_writer = ReportWriter(reports_dir)

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
