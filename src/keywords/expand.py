from __future__ import annotations
from typing import Dict, Iterable, List, Optional, Tuple

from src.utils.normalize import normalize_text


EP_PATTERNS = [
    "EP1",
    "E01",
    "E1",
    "Episode 1",
    "Ep 1",
    "第1集",
    "第1話",
    "第1话",
    "1화",
    "ตอนที่ 1",
    "Capítulo 1",
    "Episodio 1",
    "Épisode 1",
    "Folge 1",
    "Episódio 1",
    "Episodio 1",
]


def _alias_priority(name: str, is_primary: bool, canonical_norm: str) -> float:
    norm = normalize_text(name)
    if not norm:
        return 0.0

    score = 0.0
    if canonical_norm and norm.casefold() == canonical_norm:
        score += 200.0
    if is_primary:
        score += 120.0

    token_count = len(norm.split())
    length = len(norm)

    if token_count >= 2:
        score += 40.0
    elif token_count == 1:
        score -= 15.0

    if length <= 4:
        score -= 35.0
    elif length <= 6:
        score -= 20.0
    elif length >= 20:
        score += 25.0
    elif length >= 12:
        score += 18.0
    elif length >= 8:
        score += 12.0

    if any(ch in norm for ch in {" ", "·", "-", "・"}):
        score += 8.0

    return score


def _canonical_map(data: Dict) -> Dict[str, str]:
    m: Dict[str, str] = {}
    for item in data.get("series", []):
        sid = item.get("series_id")
        if not sid:
            continue
        canonical = normalize_text(item.get("canonical_title", ""))
        if canonical:
            m[sid] = canonical.casefold()
    return m


def expand_terms_for_series(
    aliases: Iterable[str],
    *,
    include_ep_patterns: bool = False,
    ep_patterns: Optional[Iterable[str]] = None,
    max_aliases: Optional[int] = None,
) -> List[str]:
    """Return a deduplicated set of search keywords for a series."""

    seen_aliases = set()
    base_terms: List[str] = []

    for alias in aliases:
        a_norm = normalize_text(alias)
        if not a_norm:
            continue
        key = a_norm.casefold()
        if key in seen_aliases:
            continue
        seen_aliases.add(key)
        base_terms.append(a_norm)
        if max_aliases is not None and len(base_terms) >= max_aliases:
            break

    if not base_terms:
        return []

    terms = base_terms.copy()

    if include_ep_patterns:
        patterns = list(ep_patterns) if ep_patterns is not None else EP_PATTERNS
        anchor = base_terms[0]
        for ep in patterns:
            combo = f"{anchor} {ep}".strip()
            if combo:
                terms.append(combo)

    deduped: Dict[str, None] = {}
    for term in terms:
        if term not in deduped:
            deduped[term] = None
    return list(deduped.keys())


def build_series_keywords(
    data: Dict,
    *,
    include_ep_patterns: bool = False,
    max_aliases: Optional[int] = None,
) -> Dict[str, List[str]]:
    """Build map of series_id -> prioritized search terms."""

    canonical_lookup = _canonical_map(data)

    aliases_by_sid: Dict[str, List[Dict]] = {}
    for al in data.get("aliases", []):
        sid = al.get("series_id")
        name = al.get("name")
        if not sid or not name:
            continue
        aliases_by_sid.setdefault(sid, []).append(al)

    keywords: Dict[str, List[str]] = {}
    for sid, alias_entries in aliases_by_sid.items():
        canonical_norm = canonical_lookup.get(sid, "")
        scored: List[Tuple[float, int, str]] = []
        for idx, entry in enumerate(alias_entries):
            name = entry.get("name")
            if not name:
                continue
            score = _alias_priority(name, bool(entry.get("is_primary")), canonical_norm)
            scored.append((score, idx, name))

        if not scored:
            keywords[sid] = []
            continue

        scored.sort(key=lambda x: (-x[0], x[1]))
        ordered_names = [name for _, _, name in scored]

        filtered: List[str] = []
        for name in ordered_names:
            norm = normalize_text(name)
            tokens = norm.split()
            if canonical_norm and norm.casefold() == canonical_norm:
                filtered.append(name)
                continue
            # Drop ultra-generic aliases (single token, very short) to avoid noise
            if len(tokens) == 1 and len(norm.replace(" ", "")) <= 6:
                continue
            filtered.append(name)

        if not filtered:
            filtered = ordered_names[:1]

        keywords[sid] = expand_terms_for_series(
            filtered,
            include_ep_patterns=include_ep_patterns,
            max_aliases=max_aliases,
        )

    return keywords
