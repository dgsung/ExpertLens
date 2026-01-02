"""LLM module for ExpertLens."""

from .client import HuggingFaceClient
from .extractor import EvidenceExtractor

__all__ = ["HuggingFaceClient", "EvidenceExtractor"]
