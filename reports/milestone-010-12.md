# Milestone M010-12: Identity Resolution Enhancement

**Status**: DONE
**Completed**: 2026-01-02

---

## Goal

Blocking keys + scoring 기반 identity resolution 구현

---

## Deliverables

| File | Description |
|------|-------------|
| `src/expertlens/identity/resolver.py` | Enhanced IdentityResolver with blocking keys and scoring |
| `src/expertlens/identity/__init__.py` | Export BlockingKey, MatchResult |

---

## Blocking Keys

| Key Type | Weight | Description |
|----------|--------|-------------|
| linkedin | 1.0 | LinkedIn profile ID (unique identifier) |
| email | 0.9 | Email address |
| phone | 0.8 | Phone number (digits only) |
| name_company | 0.7 | Name + Company combination |
| website | 0.6 | Personal website URL |
| name | 0.3 | Name only (weak signal) |

---

## Scoring Algorithm

```
Score = max(weight of matched keys)
```

**Rationale**: Unique identifiers (LinkedIn, Email, Phone) are sufficient alone for identity matching. A single LinkedIn match should trigger merge regardless of other keys.

**Thresholds**:
- `>= 0.90`: Auto-merge (same person)
- `0.75 - 0.90`: Review zone (v1: treat as new)
- `< 0.75`: Keep separate

---

## Key Classes

### BlockingKey
```python
@dataclass
class BlockingKey:
    key_type: str   # linkedin, email, phone, name_company, name, website
    value: str      # Normalized value
    weight: float   # Importance weight
```

### MatchResult
```python
@dataclass
class MatchResult:
    expert_id: str
    score: float
    matched_keys: list[str]
```

### IdentityResolver Methods

| Method | Description |
|--------|-------------|
| `extract_blocking_keys(expert)` | Extract all blocking keys from an expert |
| `calculate_match_score(e1, e2)` | Calculate match score between two experts |
| `resolve(experts)` | Resolve and merge expert list using Union-Find |
| `find_matches(candidate, existing)` | Find potential matches in existing list |
| `merge_into_existing(new, existing)` | Merge new experts into existing list |

---

## Normalization

| Key Type | Normalization |
|----------|---------------|
| name | Unicode NFC, lowercase, remove punctuation |
| linkedin | Extract profile ID from URL |
| email | Lowercase, strip whitespace |
| phone | Digits only, min 7 digits |
| website | Remove protocol, www, trailing slash |

---

## Test Results

| Test | Input | Output | Result |
|------|-------|--------|--------|
| LinkedIn match | 2 experts (same LinkedIn) | Merged into 1 | Pass |
| No match | 2 experts (different) | Keep separate | Pass |
| Evidence merge | 3 experts (2 same) | 2 experts | Pass |
| Claims dedup | Duplicate claims | Deduplicated | Pass |

---

## Usage

```python
from expertlens.identity import IdentityResolver, BlockingKey, MatchResult

resolver = IdentityResolver(
    merge_threshold=0.90,
    review_threshold=0.75
)

# Extract blocking keys
keys = resolver.extract_blocking_keys(expert)

# Calculate match score
result = resolver.calculate_match_score(expert1, expert2)
print(f"Score: {result.score}, Matched: {result.matched_keys}")

# Resolve list of experts
merged = resolver.resolve(experts)

# Merge new experts into existing
updated = resolver.merge_into_existing(new_experts, existing)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IdentityResolver                          │
├─────────────────────────────────────────────────────────────┤
│  1. Extract blocking keys from each expert                  │
│     └─ LinkedIn ID, Email, Phone, Name+Company, Website     │
├─────────────────────────────────────────────────────────────┤
│  2. Build key index (key -> expert indices)                 │
│     └─ Candidates share at least one blocking key           │
├─────────────────────────────────────────────────────────────┤
│  3. Score candidate pairs                                   │
│     └─ Score = max(matched key weights)                     │
├─────────────────────────────────────────────────────────────┤
│  4. Union-Find grouping                                     │
│     └─ Score >= 0.90 → same group                           │
├─────────────────────────────────────────────────────────────┤
│  5. Merge each group                                        │
│     └─ Combine claims, evidence, pick best name             │
└─────────────────────────────────────────────────────────────┘
```

---

## Done Definition Checklist

- [x] BlockingKey dataclass 구현
- [x] MatchResult dataclass 구현
- [x] Blocking key extraction (LinkedIn, Email, Phone, Name+Company, Website, Name)
- [x] Scoring algorithm (max weight based)
- [x] Union-Find merge grouping
- [x] Expert merge with claim deduplication
- [x] Export classes from module

---

## Follow-ups

- M010-13: LLM extraction pipeline (DDG URLs → Expert extraction)
- Configurable thresholds via API
- Review queue for 0.75-0.90 score matches

---

## Related

- M010-11: DuckDuckGo Search Integration (provides URLs)
- M010-6: Run Endpoint + Core (uses resolver)
