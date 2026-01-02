"""Pipeline orchestrator for ExpertLens."""

from pathlib import Path

from .io.writer import ReportWriter, SessionWriter


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
        # Create session JSON skeleton
        session_id, session_path = self.session_writer.create_session_skeleton(
            query=query,
            language=language,
        )

        # Create run report
        report_path = self.report_writer.create_run_report(
            session_id=session_id,
            query=query,
            language=language,
        )

        return {
            "session_id": session_id,
            "session_path": str(session_path),
            "report_path": str(report_path),
            "query": query,
            "language": language,
        }
