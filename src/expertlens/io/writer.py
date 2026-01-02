"""File writers for ExpertLens session and report outputs."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SessionWriter:
    """Writes session JSON files to the out/ directory."""

    def __init__(self, output_dir: Path | str = "out"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        now = datetime.now(timezone.utc).isoformat()

        session_data = {
            "session_id": session_id,
            "language": language,
            "query": query,
            "queries": [{"query": query, "added_at": now}],
            "created_at": now,
            "updated_at": now,
            "experts": [],
            "companies": [],
            "evidence": [],
        }

        file_path = self.output_dir / f"session-{session_id}.json"
        self._write_json(file_path, session_data)

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
        self, session_id: str, query: str, language: str
    ) -> Path:
        """Create a run report markdown file.

        Args:
            session_id: The session UUID.
            query: The search query.
            language: The session language.

        Returns:
            Path to the created report file.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        file_path = self.reports_dir / f"run-{timestamp}.md"

        content = self._generate_run_report(session_id, query, language, timestamp)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path

    def _generate_run_report(
        self, session_id: str, query: str, language: str, timestamp: str
    ) -> str:
        """Generate the markdown content for a run report."""
        return f"""# ExpertLens Run Report

**Timestamp**: {timestamp}
**Session ID**: {session_id}
**Query**: {query}
**Language**: {language}

---

## Summary

(Run completed - skeleton report)

## Results

- Experts found: 0
- Evidence collected: 0
- Companies identified: 0

## Next Steps

- Add actual search implementation
- Integrate LLM extraction
"""
