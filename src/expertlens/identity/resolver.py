"""Simple identity resolver for ExpertLens v1.

Provides basic name-matching identity resolution for merging
expert candidates from multiple evidence sources.
"""

import re
import unicodedata
from datetime import datetime, timezone

from ..models import EmploymentClaim, ContactClaim, Expert


class IdentityResolver:
    """Resolves and merges expert identities based on name matching.

    For v1, uses simple case-insensitive name matching with
    normalization for Korean and English names.
    """

    def __init__(self, similarity_threshold: float = 0.9):
        """Initialize resolver.

        Args:
            similarity_threshold: Threshold for fuzzy matching (0.0-1.0).
                Not used in v1 simple matching.
        """
        self.similarity_threshold = similarity_threshold

    def resolve(self, experts: list[Expert]) -> list[Expert]:
        """Resolve and merge expert identities.

        Args:
            experts: List of expert candidates to resolve.

        Returns:
            List of merged experts with combined claims and evidence.
        """
        if not experts:
            return []

        # Group by normalized name
        groups: dict[str, list[Expert]] = {}

        for expert in experts:
            key = self._normalize_name(expert.canonical_name)
            if key not in groups:
                groups[key] = []
            groups[key].append(expert)

        # Merge each group
        merged = []
        for group in groups.values():
            if len(group) == 1:
                merged.append(group[0])
            else:
                merged.append(self._merge_experts(group))

        return merged

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison.

        Handles:
        - Case normalization
        - Unicode normalization (Korean)
        - Whitespace normalization
        - Basic punctuation removal
        """
        if not name:
            return ""

        # Unicode normalize (NFC for Korean)
        normalized = unicodedata.normalize("NFC", name)

        # Lowercase
        normalized = normalized.lower()

        # Remove common punctuation
        normalized = re.sub(r"[.,\-_'\"()]", "", normalized)

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized.strip()

    def _merge_experts(self, experts: list[Expert]) -> Expert:
        """Merge multiple expert records into one.

        Uses the first expert as the base, combining claims and
        evidence from all experts in the group.
        """
        if not experts:
            raise ValueError("Cannot merge empty expert list")

        base = experts[0]
        now = datetime.now(timezone.utc)

        # Collect all claims (deduplicate by content)
        all_claims: list[EmploymentClaim | ContactClaim] = []
        seen_claims: set[str] = set()

        for expert in experts:
            for claim in expert.claims:
                # Create a signature for deduplication
                sig = self._claim_signature(claim)
                if sig not in seen_claims:
                    seen_claims.add(sig)
                    all_claims.append(claim)

        # Collect all evidence IDs (deduplicate)
        all_evidence = list(set(
            eid for expert in experts
            for eid in expert.evidence_ids
        ))

        # Find earliest creation time
        earliest_created = min(e.created_at for e in experts)

        return Expert(
            expert_id=base.expert_id,
            canonical_name=base.canonical_name,
            claims=all_claims,
            evidence_ids=all_evidence,
            created_at=earliest_created,
            updated_at=now,
        )

    def _claim_signature(self, claim: EmploymentClaim | ContactClaim) -> str:
        """Create a signature string for claim deduplication."""
        if isinstance(claim, EmploymentClaim):
            return f"emp:{claim.company}:{claim.role}:{claim.start_date}:{claim.end_date}"
        elif isinstance(claim, ContactClaim):
            return f"contact:{claim.contact_type}:{claim.contact_value}"
        else:
            return f"unknown:{claim.claim_type}"

    def find_matches(
        self,
        candidate: Expert,
        existing: list[Expert]
    ) -> list[Expert]:
        """Find potential matches for a candidate in existing experts.

        Args:
            candidate: The expert candidate to match.
            existing: List of existing experts to search.

        Returns:
            List of matching experts (by normalized name).
        """
        candidate_key = self._normalize_name(candidate.canonical_name)

        matches = []
        for expert in existing:
            if self._normalize_name(expert.canonical_name) == candidate_key:
                matches.append(expert)

        return matches

    def merge_into_existing(
        self,
        new_experts: list[Expert],
        existing: list[Expert],
    ) -> list[Expert]:
        """Merge new experts into existing expert list.

        Args:
            new_experts: New expert candidates to merge.
            existing: Existing expert list to merge into.

        Returns:
            Updated list of experts with merges applied.
        """
        # Create a working copy
        result = list(existing)
        result_by_name: dict[str, int] = {
            self._normalize_name(e.canonical_name): i
            for i, e in enumerate(result)
        }

        for new_expert in new_experts:
            key = self._normalize_name(new_expert.canonical_name)

            if key in result_by_name:
                # Merge with existing
                idx = result_by_name[key]
                result[idx] = self._merge_experts([result[idx], new_expert])
            else:
                # Add as new
                result_by_name[key] = len(result)
                result.append(new_expert)

        return result
