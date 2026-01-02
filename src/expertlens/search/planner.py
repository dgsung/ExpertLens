"""Search query planner for ExpertLens."""

from dataclasses import dataclass


@dataclass
class SearchQuery:
    """A search query to execute."""

    query: str
    source: str  # e.g., "linkedin", "news", "patent"
    weight: float = 1.0


class SearchPlanner:
    """Plans search queries based on user requirements.

    This is a stub implementation for M010-1.
    Full implementation will use LLM in M010-2.
    """

    def __init__(self, language: str = "ko"):
        self.language = language

    def plan_queries(self, user_query: str) -> list[SearchQuery]:
        """Generate search queries from user requirement.

        Args:
            user_query: The user's natural language query.

        Returns:
            List of SearchQuery objects to execute.
        """
        # Stub: return simple queries for different sources
        return [
            SearchQuery(
                query=f"site:linkedin.com/in {user_query}",
                source="linkedin",
                weight=0.7,
            ),
            SearchQuery(
                query=f"{user_query} 연구원 논문",
                source="paper",
                weight=0.5,
            ),
            SearchQuery(
                query=f"{user_query} 특허",
                source="patent",
                weight=0.5,
            ),
        ]
