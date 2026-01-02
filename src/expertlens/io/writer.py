"""File writers for ExpertLens session and report outputs."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..models import Session, Query


class SessionWriter:
    """Writes session JSON files to the out/ directory."""

    def __init__(self, output_dir: Path | str = "out"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, session: Session) -> Path:
        """Write a Session model to JSON file.

        Args:
            session: The Session object to write.

        Returns:
            Path to the created file.
        """
        file_path = self.output_dir / f"session-{session.session_id}.json"
        self._write_json(file_path, session.model_dump(mode="json"))
        return file_path

    def create_session_skeleton(
        self, query: str, language: str = "ko"
    ) -> tuple[str, Path]:
        """Create a new session JSON file with skeleton structure.

        Args:
            query: The search query string.
            language: The session language (default: "ko").

        Returns:
            Tuple of (session_id, file_path).
        """
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        session = Session(
            session_id=session_id,
            language=language,
            query=query,
            queries=[Query(query=query, added_at=now)],
            created_at=now,
            updated_at=now,
            experts=[],
            companies=[],
            evidence=[],
        )

        file_path = self.create_session(session)
        return session_id, file_path

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        """Write JSON data to file with proper formatting."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class ReportWriter:
    """Writes markdown report files to the reports/ directory."""

    def __init__(self, reports_dir: Path | str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def create_run_report(
        self,
        session_id: str,
        query: str,
        language: str,
        expert_count: int = 0,
        evidence_count: int = 0,
        company_count: int = 0,
    ) -> Path:
        """Create a run report markdown file.

        Args:
            session_id: The session UUID.
            query: The search query.
            language: The session language.
            expert_count: Number of experts found.
            evidence_count: Number of evidence items.
            company_count: Number of companies identified.

        Returns:
            Path to the created report file.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        file_path = self.reports_dir / f"run-{timestamp}.md"

        content = self._generate_run_report(
            session_id, query, language, timestamp,
            expert_count, evidence_count, company_count
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path

    def _generate_run_report(
        self,
        session_id: str,
        query: str,
        language: str,
        timestamp: str,
        expert_count: int,
        evidence_count: int,
        company_count: int,
    ) -> str:
        """Generate the markdown content for a run report."""
        return f"""# ExpertLens Run Report

**Timestamp**: {timestamp}
**Session ID**: {session_id}
**Query**: {query}
**Language**: {language}

---

## Summary

Search completed successfully.

## Results

- Experts found: {expert_count}
- Evidence collected: {evidence_count}
- Companies identified: {company_count}

## Evidence Traceability

Each expert's claims are linked to evidence URLs.
See session JSON for full details.

## Next Steps

- Review expert profiles
- Verify evidence links
- Add additional queries if needed
"""
