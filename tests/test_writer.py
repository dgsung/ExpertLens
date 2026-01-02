"""Unit tests for io/writer.py."""

import json
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expertlens.io.writer import ReportWriter, SessionWriter


class TestSessionWriter:
    """Tests for SessionWriter class."""

    def test_create_session_skeleton_creates_file(self, tmp_path: Path) -> None:
        """Test that create_session_skeleton creates a JSON file."""
        writer = SessionWriter(output_dir=tmp_path)
        session_id, file_path = writer.create_session_skeleton(
            query="test query", language="ko"
        )

        assert file_path.exists()
        assert file_path.name.startswith("session-")
        assert file_path.suffix == ".json"

    def test_create_session_skeleton_returns_valid_uuid(self, tmp_path: Path) -> None:
        """Test that session_id is a valid UUID string."""
        writer = SessionWriter(output_dir=tmp_path)
        session_id, _ = writer.create_session_skeleton(query="test", language="ko")

        # UUID format: 8-4-4-4-12 hex characters
        parts = session_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_create_session_skeleton_json_structure(self, tmp_path: Path) -> None:
        """Test that created JSON has required structure."""
        writer = SessionWriter(output_dir=tmp_path)
        session_id, file_path = writer.create_session_skeleton(
            query="배터리 전문가", language="ko"
        )

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Check required fields
        assert data["session_id"] == session_id
        assert data["language"] == "ko"
        assert data["query"] == "배터리 전문가"
        assert isinstance(data["queries"], list)
        assert len(data["queries"]) == 1
        assert data["queries"][0]["query"] == "배터리 전문가"
        assert "added_at" in data["queries"][0]
        assert "created_at" in data
        assert "updated_at" in data
        assert data["experts"] == []
        assert data["companies"] == []
        assert data["evidence"] == []

    def test_create_session_skeleton_handles_different_languages(
        self, tmp_path: Path
    ) -> None:
        """Test that language parameter is correctly stored."""
        writer = SessionWriter(output_dir=tmp_path)

        _, file_path_ko = writer.create_session_skeleton(query="test", language="ko")
        _, file_path_en = writer.create_session_skeleton(query="test", language="en")

        with open(file_path_ko, encoding="utf-8") as f:
            data_ko = json.load(f)
        with open(file_path_en, encoding="utf-8") as f:
            data_en = json.load(f)

        assert data_ko["language"] == "ko"
        assert data_en["language"] == "en"

    def test_output_dir_created_if_not_exists(self, tmp_path: Path) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "nested" / "output"
        assert not output_dir.exists()

        writer = SessionWriter(output_dir=output_dir)
        writer.create_session_skeleton(query="test", language="ko")

        assert output_dir.exists()


class TestReportWriter:
    """Tests for ReportWriter class."""

    def test_create_run_report_creates_file(self, tmp_path: Path) -> None:
        """Test that create_run_report creates a markdown file."""
        writer = ReportWriter(reports_dir=tmp_path)
        file_path = writer.create_run_report(
            session_id="test-session-id",
            query="test query",
            language="ko",
        )

        assert file_path.exists()
        assert file_path.name.startswith("run-")
        assert file_path.suffix == ".md"

    def test_create_run_report_content(self, tmp_path: Path) -> None:
        """Test that report contains required information."""
        writer = ReportWriter(reports_dir=tmp_path)
        file_path = writer.create_run_report(
            session_id="abc-123",
            query="배터리 전문가",
            language="ko",
        )

        content = file_path.read_text(encoding="utf-8")

        assert "abc-123" in content
        assert "배터리 전문가" in content
        assert "ko" in content
        assert "# ExpertLens Run Report" in content

    def test_reports_dir_created_if_not_exists(self, tmp_path: Path) -> None:
        """Test that reports directory is created if it doesn't exist."""
        reports_dir = tmp_path / "nested" / "reports"
        assert not reports_dir.exists()

        writer = ReportWriter(reports_dir=reports_dir)
        writer.create_run_report(
            session_id="test", query="test", language="ko"
        )

        assert reports_dir.exists()
