"""Session management for ExpertLens.

Handles session CRUD operations with file-based storage.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..models import Session, Query


class SessionManager:
    """Manages session lifecycle and file storage."""

    def __init__(self, output_dir: Path | str = "out"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, language: str = "ko") -> Session:
        """Create a new empty session.

        Args:
            language: Session language (default: "ko").

        Returns:
            Created Session object.
        """
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        session = Session(
            session_id=session_id,
            language=language,
            query="",
            queries=[],
            created_at=now,
            updated_at=now,
            experts=[],
            companies=[],
            evidence=[],
        )

        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.

        Args:
            session_id: The session UUID.

        Returns:
            Session object or None if not found.
        """
        file_path = self._get_session_path(session_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: The session UUID.

        Returns:
            True if session exists.
        """
        return self._get_session_path(session_id).exists()

    def update_session(self, session: Session) -> Session:
        """Update a session (save to file).

        Args:
            session: The session to update.

        Returns:
            Updated session with new updated_at timestamp.
        """
        session.updated_at = datetime.now(timezone.utc)
        self._save_session(session)
        return session

    def list_sessions(self) -> list[str]:
        """List all session IDs.

        Returns:
            List of session IDs.
        """
        session_files = self.output_dir.glob("session-*.json")
        session_ids = []

        for f in session_files:
            # Extract session ID from filename: session-<uuid>.json
            name = f.stem  # session-<uuid>
            if name.startswith("session-"):
                session_ids.append(name[8:])  # Remove "session-" prefix

        return session_ids

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.output_dir / f"session-{session_id}.json"

    def _save_session(self, session: Session) -> Path:
        """Save session to file."""
        file_path = self._get_session_path(session.session_id)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

        return file_path


# Default instance for convenience
_default_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get the default session manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = SessionManager()
    return _default_manager
