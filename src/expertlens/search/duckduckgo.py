"""DuckDuckGo search provider for ExpertLens."""

import uuid
from datetime import datetime, timezone

from duckduckgo_search import DDGS

from ..models import Evidence


class DuckDuckGoSearchProvider:
    """Provides real search results from DuckDuckGo.

    Uses the duckduckgo-search library to perform web searches
    and returns Evidence objects containing URLs and metadata.
    """

    def __init__(self, language: str = "ko", max_results: int = 10):
        """Initialize the search provider.

        Args:
            language: Search language/region (ko, en, etc.)
            max_results: Maximum number of search results to return.
        """
        self.language = language
        self.max_results = max_results
        self._region = self._get_region(language)

    def _get_region(self, language: str) -> str:
        """Map language to DuckDuckGo region code."""
        region_map = {
            "ko": "kr-kr",
            "en": "us-en",
            "ja": "jp-jp",
            "zh": "cn-zh",
        }
        return region_map.get(language, "wt-wt")  # wt-wt = worldwide

    def search(self, query: str) -> list[Evidence]:
        """Execute DuckDuckGo search and return Evidence objects.

        Args:
            query: The search query string.

        Returns:
            List of Evidence objects containing URLs and metadata.
        """
        now = datetime.now(timezone.utc)
        evidence_list: list[Evidence] = []

        try:
            with DDGS() as ddgs:
                results = ddgs.text(
                    query,
                    region=self._region,
                    max_results=self.max_results,
                )

                for result in results:
                    url = result.get("href", "")
                    if not url:
                        continue

                    evidence = Evidence(
                        evidence_id=str(uuid.uuid4()),
                        url=url,
                        platform=self._detect_platform(url),
                        retrieved_at=now,
                        title=result.get("title", ""),
                        snippet=result.get("body", ""),
                    )
                    evidence_list.append(evidence)

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            # Return empty list on error

        return evidence_list

    def search_site(self, query: str, site: str) -> list[Evidence]:
        """Search within a specific site.

        Args:
            query: The search query string.
            site: Site domain to search (e.g., 'linkedin.com/in').

        Returns:
            List of Evidence objects.
        """
        site_query = f"site:{site} {query}"
        return self.search(site_query)

    def search_expert(self, query: str) -> list[Evidence]:
        """Search for experts using multiple strategies.

        Searches LinkedIn profiles, news, and general web.

        Args:
            query: The expert search query.

        Returns:
            Combined list of Evidence objects.
        """
        all_evidence: list[Evidence] = []
        seen_urls: set[str] = set()

        # Strategy 1: LinkedIn profiles
        linkedin_results = self.search_site(query, "linkedin.com/in")
        for ev in linkedin_results:
            if ev.url not in seen_urls:
                all_evidence.append(ev)
                seen_urls.add(ev.url)

        # Strategy 2: General search
        general_results = self.search(query)
        for ev in general_results:
            if ev.url not in seen_urls:
                all_evidence.append(ev)
                seen_urls.add(ev.url)

        return all_evidence[:self.max_results]

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()

        if "linkedin.com" in url_lower:
            return "linkedin"
        elif "scholar.google" in url_lower:
            return "google_scholar"
        elif "researchgate.net" in url_lower:
            return "researchgate"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "youtube.com" in url_lower:
            return "youtube"
        elif "github.com" in url_lower:
            return "github"
        elif "patents.google" in url_lower or "patent" in url_lower:
            return "patent"
        elif "news" in url_lower or "article" in url_lower:
            return "news"
        elif ".pdf" in url_lower:
            return "pdf"
        else:
            return "web"
