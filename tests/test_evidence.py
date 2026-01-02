"""Tests for evidence fetcher module."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expertlens.evidence import EvidenceFetcher
from expertlens.models import Evidence


class TestEvidenceFetcher:
    """Tests for EvidenceFetcher class."""

    @pytest.fixture
    def fetcher(self):
        return EvidenceFetcher(timeout=10.0)

    def test_detect_platform_linkedin(self, fetcher):
        assert fetcher._detect_platform("https://linkedin.com/in/john") == "linkedin"
        assert fetcher._detect_platform("https://www.linkedin.com/in/john") == "linkedin"

    def test_detect_platform_twitter(self, fetcher):
        assert fetcher._detect_platform("https://twitter.com/user") == "twitter"
        assert fetcher._detect_platform("https://x.com/user") == "twitter"

    def test_detect_platform_youtube(self, fetcher):
        assert fetcher._detect_platform("https://youtube.com/watch?v=123") == "youtube"

    def test_detect_platform_paper(self, fetcher):
        assert fetcher._detect_platform("https://arxiv.org/abs/2301.00001") == "paper"
        assert fetcher._detect_platform("https://scholar.google.com/") == "paper"

    def test_detect_platform_patent(self, fetcher):
        assert fetcher._detect_platform("https://patents.google.com/patent/US123") == "patent"

    def test_detect_platform_news(self, fetcher):
        assert fetcher._detect_platform("https://news.example.com/article") == "news"

    def test_detect_platform_default_web(self, fetcher):
        assert fetcher._detect_platform("https://example.com/page") == "web"

    def test_extract_content_removes_scripts(self, fetcher):
        from bs4 import BeautifulSoup

        html = """
        <html>
        <body>
            <script>var x = 1;</script>
            <p>Main content here.</p>
            <style>.foo { color: red; }</style>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        content = fetcher._extract_content(soup)

        assert "Main content here" in content
        assert "var x" not in content
        assert "color: red" not in content

    def test_extract_content_finds_article(self, fetcher):
        from bs4 import BeautifulSoup

        html = """
        <html>
        <body>
            <nav>Navigation menu</nav>
            <article>
                <h1>Article Title</h1>
                <p>This is the main article content.</p>
            </article>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        content = fetcher._extract_content(soup)

        assert "Article Title" in content
        assert "main article content" in content
        # nav and footer should be removed
        assert "Navigation menu" not in content
        assert "Footer content" not in content

    def test_extract_content_falls_back_to_body(self, fetcher):
        from bs4 import BeautifulSoup

        html = """
        <html>
        <body>
            <div>Some content in a div.</div>
            <p>Another paragraph.</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        content = fetcher._extract_content(soup)

        assert "Some content in a div" in content
        assert "Another paragraph" in content

    @patch("httpx.Client")
    def test_fetch_creates_evidence(self, mock_client_class, fetcher):
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <article>
                <p>This is test content about John Smith, CEO of TechCorp.</p>
            </article>
        </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        fetcher._client = mock_client

        evidence, content = fetcher.fetch("https://example.com/page")

        assert isinstance(evidence, Evidence)
        assert evidence.url == "https://example.com/page"
        assert evidence.title == "Test Page"
        assert evidence.platform == "web"
        assert "John Smith" in content

    @patch("httpx.Client")
    def test_fetch_multiple_skips_failures(self, mock_client_class, fetcher):
        import httpx

        mock_client = MagicMock()

        # First URL succeeds, second fails
        def mock_get(url):
            if "good" in url:
                response = MagicMock()
                response.text = "<html><body><p>Good content</p></body></html>"
                response.raise_for_status = MagicMock()
                return response
            else:
                raise httpx.HTTPError("Failed")

        mock_client.get.side_effect = mock_get
        fetcher._client = mock_client

        results = fetcher.fetch_multiple([
            "https://good.example.com/",
            "https://bad.example.com/",
        ])

        assert len(results) == 1
        assert results[0][0].url == "https://good.example.com/"

    def test_context_manager(self):
        with EvidenceFetcher() as fetcher:
            assert fetcher is not None
        # Client should be closed after context exits
