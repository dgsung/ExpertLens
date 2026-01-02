"""URL fetcher for evidence collection."""

import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from ..models import Evidence


class EvidenceFetcher:
    """Fetches and extracts content from URLs."""

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    PLATFORM_PATTERNS = {
        "linkedin": r"linkedin\.com",
        "twitter": r"(twitter|x)\.com",
        "facebook": r"facebook\.com",
        "youtube": r"youtube\.com",
        "news": r"(news|article|blog)",
        "patent": r"patent",
        "paper": r"(arxiv|scholar|researchgate|doi\.org)",
    }

    def __init__(self, timeout: float = 30.0):
        """Initialize fetcher.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": self.USER_AGENT},
        )

    def fetch(self, url: str) -> tuple[Evidence, str]:
        """Fetch URL and extract content.

        Args:
            url: The URL to fetch.

        Returns:
            Tuple of (Evidence object, extracted text content).

        Raises:
            RuntimeError: If fetch fails.
        """
        now = datetime.now(timezone.utc)

        try:
            response = self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to fetch URL: {e}")

        # Detect platform
        platform = self._detect_platform(url)

        # Parse HTML and extract content
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = None
        if soup.title:
            title = soup.title.string
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        # Extract main content
        content = self._extract_content(soup)

        # Create snippet (first 500 chars)
        snippet = content[:500] if content else None

        evidence = Evidence(
            evidence_id=str(uuid.uuid4()),
            url=url,
            platform=platform,
            retrieved_at=now,
            title=title,
            snippet=snippet,
        )

        return evidence, content

    def _detect_platform(self, url: str) -> str:
        """Detect platform type from URL."""
        url_lower = url.lower()

        for platform, pattern in self.PLATFORM_PATTERNS.items():
            if re.search(pattern, url_lower):
                return platform

        # Default based on domain
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "linkedin" in domain:
            return "linkedin"
        elif "scholar" in domain or "arxiv" in domain:
            return "paper"
        elif "patent" in domain:
            return "patent"
        else:
            return "web"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from parsed HTML."""
        # Remove script, style, nav, footer elements
        for element in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Try to find main content area
        main_content = None

        # Look for common content containers
        for selector in ["article", "main", '[role="main"]', ".content", "#content"]:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            # Fall back to body
            body = soup.find("body")
            text = body.get_text(separator="\n", strip=True) if body else ""

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def fetch_multiple(self, urls: list[str]) -> list[tuple[Evidence, str]]:
        """Fetch multiple URLs.

        Args:
            urls: List of URLs to fetch.

        Returns:
            List of (Evidence, content) tuples. Failed URLs are skipped.
        """
        results = []
        for url in urls:
            try:
                result = self.fetch(url)
                results.append(result)
            except RuntimeError as e:
                print(f"Skipping URL {url}: {e}")
                continue
        return results

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "EvidenceFetcher":
        return self

    def __exit__(self, *args) -> None:
        self.close()
