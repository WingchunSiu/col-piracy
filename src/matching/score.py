from __future__ import annotations
import re
from typing import Iterable

from src.utils.normalize import normalize_for_match


try:
    from rapidfuzz import fuzz as _rf_fuzz  # type: ignore
except Exception:  # pragma: no cover - rapidfuzz optional
    _rf_fuzz = None


def _ratio(a: str, b: str) -> float:
    if _rf_fuzz is not None:
        return float(_rf_fuzz.ratio(a, b))
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio() * 100.0


def _partial_ratio(a: str, b: str) -> float:
    if _rf_fuzz is not None:
        return float(_rf_fuzz.partial_ratio(a, b))
    if not a or not b:
        return 0.0
    # Ensure a is longer so sliding windows are minimal
    if len(a) < len(b):
        a, b = b, a
    best = 0.0
    window = len(b)
    for i in range(len(a) - window + 1):
        segment = a[i : i + window]
        best = max(best, _ratio(segment, b))
        if best >= 99.0:
            break
    return best


def _token_sort_ratio(a: str, b: str) -> float:
    if _rf_fuzz is not None:
        return float(_rf_fuzz.token_sort_ratio(a, b))
    a_tokens = sorted(a.split())
    b_tokens = sorted(b.split())
    if not a_tokens or not b_tokens:
        return _ratio(a, b)
    return _ratio(" ".join(a_tokens), " ".join(b_tokens))


def _best_similarity(a: str, b: str) -> float:
    sims = [_ratio(a, b), _partial_ratio(a, b), _token_sort_ratio(a, b)]
    return max(sims)


BOOST_WORDS = [
    'full', '完整版', '完整', '全集', '1080p', '720p', 'hd', 'ep', 'episode', '第',
    'capítulo', 'episodio', 'épisode', 'folge', '화', '話', 'ตอน',
]


def _contains_keyword(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    # ASCII/latin keywords benefit from word boundaries; CJK simply check substring
    if keyword.isascii() and keyword.replace(' ', '').isalnum():
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return keyword in text


def compute_score(title: str, aliases: Iterable[str]) -> float:
    t_norm = normalize_for_match(title)
    score = 0.0
    best = 0.0
    exact_match = False

    for alias in aliases:
        a_norm = normalize_for_match(alias)
        if not a_norm:
            continue
        if t_norm == a_norm:
            exact_match = True
            best = max(best, 100.0)
            continue
        if a_norm in t_norm:
            best = max(best, 98.0)
        best = max(best, _best_similarity(t_norm, a_norm))

    if best >= 95:
        score += 1.5
    elif best >= 90:
        score += 1.2
    elif best >= 80:
        score += 0.8
    elif best >= 70:
        score += 0.4

    if exact_match:
        score += 0.2

    for w in BOOST_WORDS:
        kw = w.casefold()
        if _contains_keyword(t_norm, kw):
            score += 0.1

    return score
