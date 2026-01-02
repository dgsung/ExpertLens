"""Enhanced identity resolver for ExpertLens.

Provides blocking-key based identity resolution with scoring
for merging expert candidates from multiple evidence sources.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone

from ..models import EmploymentClaim, ContactClaim, Expert


@dataclass
class BlockingKey:
    """A blocking key for identity matching."""
    key_type: str  # linkedin, email, phone, name_company, name, website
    value: str
    weight: float  # Importance weight for scoring


@dataclass
class MatchResult:
    """Result of comparing two experts."""
    expert_id: str
    score: float
    matched_keys: list[str]


class IdentityResolver:
    """Resolves and merges expert identities using blocking keys and scoring.

    Blocking keys are used to find candidate matches efficiently.
    Scoring determines whether to merge or keep separate.

    Blocking Key Weights:
    - LinkedIn URL: 1.0 (unique identifier)
    - Email: 0.9 (usually unique)
    - Phone: 0.8 (usually unique)
    - Name + Company: 0.7 (strong signal)
    - Website: 0.6 (usually unique)
    - Name only: 0.3 (weak signal)

    Score Thresholds:
    - >= 0.90: Merge (same person)
    - 0.75-0.90: Review (v1: treat as new)
    - < 0.75: Keep separate
    """

    # Blocking key weights
    KEY_WEIGHTS = {
        "linkedin": 1.0,
        "email": 0.9,
        "phone": 0.8,
        "name_company": 0.7,
        "website": 0.6,
        "name": 0.3,
    }

    # Score thresholds
    MERGE_THRESHOLD = 0.90
    REVIEW_THRESHOLD = 0.75

    def __init__(
        self,
        merge_threshold: float = 0.90,
        review_threshold: float = 0.75,
    ):
        """Initialize resolver.

        Args:
            merge_threshold: Score threshold for auto-merge.
            review_threshold: Score threshold for review zone.
        """
        self.merge_threshold = merge_threshold
        self.review_threshold = review_threshold

    def extract_blocking_keys(self, expert: Expert) -> list[BlockingKey]:
        """Extract all blocking keys from an expert.

        Args:
            expert: Expert to extract keys from.

        Returns:
            List of blocking keys.
        """
        keys: list[BlockingKey] = []
        normalized_name = self._normalize_name(expert.canonical_name)

        # Always add normalized name
        if normalized_name:
            keys.append(BlockingKey(
                key_type="name",
                value=normalized_name,
                weight=self.KEY_WEIGHTS["name"],
            ))

        # Extract from claims
        companies: set[str] = set()

        for claim in expert.claims:
            if isinstance(claim, ContactClaim):
                # LinkedIn URL
                if claim.contact_type == "linkedin" and claim.contact_value:
                    linkedin_id = self._extract_linkedin_id(claim.contact_value)
                    if linkedin_id:
                        keys.append(BlockingKey(
                            key_type="linkedin",
                            value=linkedin_id,
                            weight=self.KEY_WEIGHTS["linkedin"],
                        ))

                # Email
                elif claim.contact_type == "email" and claim.contact_value:
                    email_norm = claim.contact_value.lower().strip()
                    keys.append(BlockingKey(
                        key_type="email",
                        value=email_norm,
                        weight=self.KEY_WEIGHTS["email"],
                    ))

                # Phone
                elif claim.contact_type == "phone" and claim.contact_value:
                    phone_norm = self._normalize_phone(claim.contact_value)
                    if phone_norm:
                        keys.append(BlockingKey(
                            key_type="phone",
                            value=phone_norm,
                            weight=self.KEY_WEIGHTS["phone"],
                        ))

                # Website
                elif claim.contact_type in ("website", "personal_site") and claim.contact_value:
                    website_norm = self._normalize_url(claim.contact_value)
                    if website_norm:
                        keys.append(BlockingKey(
                            key_type="website",
                            value=website_norm,
                            weight=self.KEY_WEIGHTS["website"],
                        ))

            elif isinstance(claim, EmploymentClaim):
                if claim.company:
                    companies.add(self._normalize_name(claim.company))

        # Name + Company combinations
        if normalized_name:
            for company in companies:
                keys.append(BlockingKey(
                    key_type="name_company",
                    value=f"{normalized_name}@{company}",
                    weight=self.KEY_WEIGHTS["name_company"],
                ))

        return keys

    def calculate_match_score(
        self,
        expert1: Expert,
        expert2: Expert,
    ) -> MatchResult:
        """Calculate match score between two experts.

        Args:
            expert1: First expert.
            expert2: Second expert.

        Returns:
            MatchResult with score and matched keys.
        """
        keys1 = self.extract_blocking_keys(expert1)
        keys2 = self.extract_blocking_keys(expert2)

        # Build key sets by type
        keys1_by_type: dict[str, set[str]] = {}
        keys2_by_type: dict[str, set[str]] = {}

        for key in keys1:
            if key.key_type not in keys1_by_type:
                keys1_by_type[key.key_type] = set()
            keys1_by_type[key.key_type].add(key.value)

        for key in keys2:
            if key.key_type not in keys2_by_type:
                keys2_by_type[key.key_type] = set()
            keys2_by_type[key.key_type].add(key.value)

        # Find matches and calculate score
        # Use max weight of matched keys (unique identifiers are sufficient alone)
        matched_keys: list[str] = []
        max_matched_weight = 0.0

        for key_type, weight in self.KEY_WEIGHTS.items():
            if key_type in keys1_by_type and key_type in keys2_by_type:
                intersection = keys1_by_type[key_type] & keys2_by_type[key_type]
                if intersection:
                    max_matched_weight = max(max_matched_weight, weight)
                    for val in intersection:
                        matched_keys.append(f"{key_type}:{val}")

        # Score = max matched weight (LinkedIn=1.0, Email=0.9, etc.)
        score = max_matched_weight

        return MatchResult(
            expert_id=expert2.expert_id,
            score=score,
            matched_keys=matched_keys,
        )

    def resolve(self, experts: list[Expert]) -> list[Expert]:
        """Resolve and merge expert identities.

        Args:
            experts: List of expert candidates to resolve.

        Returns:
            List of merged experts with combined claims and evidence.
        """
        if not experts:
            return []

        # Build blocking key index
        key_index: dict[str, list[int]] = {}  # key -> expert indices

        for i, expert in enumerate(experts):
            keys = self.extract_blocking_keys(expert)
            for key in keys:
                full_key = f"{key.key_type}:{key.value}"
                if full_key not in key_index:
                    key_index[full_key] = []
                key_index[full_key].append(i)

        # Find merge groups using Union-Find
        parent = list(range(len(experts)))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Check pairs that share blocking keys
        checked_pairs: set[tuple[int, int]] = set()

        for indices in key_index.values():
            if len(indices) > 1:
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        idx1, idx2 = indices[i], indices[j]
                        pair = (min(idx1, idx2), max(idx1, idx2))

                        if pair not in checked_pairs:
                            checked_pairs.add(pair)
                            result = self.calculate_match_score(
                                experts[idx1], experts[idx2]
                            )

                            if result.score >= self.merge_threshold:
                                union(idx1, idx2)

        # Group by root
        groups: dict[int, list[Expert]] = {}
        for i, expert in enumerate(experts):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(expert)

        # Merge each group
        merged = []
        for group in groups.values():
            if len(group) == 1:
                merged.append(group[0])
            else:
                merged.append(self._merge_experts(group))

        return merged

    def find_matches(
        self,
        candidate: Expert,
        existing: list[Expert],
    ) -> list[MatchResult]:
        """Find potential matches for a candidate in existing experts.

        Args:
            candidate: The expert candidate to match.
            existing: List of existing experts to search.

        Returns:
            List of MatchResults sorted by score (descending).
        """
        results: list[MatchResult] = []

        for expert in existing:
            result = self.calculate_match_score(candidate, expert)
            if result.score >= self.review_threshold:
                results.append(result)

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results

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
        result = list(existing)

        for new_expert in new_experts:
            matches = self.find_matches(new_expert, result)

            if matches and matches[0].score >= self.merge_threshold:
                # Merge with best match
                best_match_id = matches[0].expert_id
                for i, expert in enumerate(result):
                    if expert.expert_id == best_match_id:
                        result[i] = self._merge_experts([expert, new_expert])
                        break
            else:
                # Add as new
                result.append(new_expert)

        return result

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison."""
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

    def _extract_linkedin_id(self, url: str) -> str | None:
        """Extract LinkedIn profile ID from URL."""
        if not url:
            return None

        # Handle various LinkedIn URL formats
        patterns = [
            r"linkedin\.com/in/([a-zA-Z0-9\-]+)",
            r"linkedin\.com/pub/([a-zA-Z0-9\-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url.lower())
            if match:
                return match.group(1)

        return None

    def _normalize_phone(self, phone: str) -> str | None:
        """Normalize phone number (digits only)."""
        if not phone:
            return None

        # Remove all non-digits
        digits = re.sub(r"\D", "", phone)

        # Must have at least 7 digits
        if len(digits) < 7:
            return None

        return digits

    def _normalize_url(self, url: str) -> str | None:
        """Normalize URL for comparison."""
        if not url:
            return None

        # Remove protocol and www
        normalized = re.sub(r"^https?://", "", url.lower())
        normalized = re.sub(r"^www\.", "", normalized)

        # Remove trailing slash
        normalized = normalized.rstrip("/")

        return normalized if normalized else None

    def _merge_experts(self, experts: list[Expert]) -> Expert:
        """Merge multiple expert records into one."""
        if not experts:
            raise ValueError("Cannot merge empty expert list")

        base = experts[0]
        now = datetime.now(timezone.utc)

        # Collect all claims (deduplicate by signature)
        all_claims: list[EmploymentClaim | ContactClaim] = []
        seen_claims: set[str] = set()

        for expert in experts:
            for claim in expert.claims:
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

        # Choose best canonical name (longest, as it's usually most complete)
        best_name = max(
            (e.canonical_name for e in experts),
            key=len
        )

        return Expert(
            expert_id=base.expert_id,
            canonical_name=best_name,
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
