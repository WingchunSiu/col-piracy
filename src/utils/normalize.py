import re
import unicodedata


_APOSTROPHES = {
    "’": "'",
    "`": "'",
    "´": "'",
    "‘": "'",
    "ʻ": "'",
}


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    # Normalize unicode width/compatibility
    s = unicodedata.normalize("NFKC", str(s))
    # Standardize apostrophes
    for k, v in _APOSTROPHES.items():
        s = s.replace(k, v)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s


def normalize_for_match(s: str) -> str:
    s = normalize_text(s)
    # Lowercase for Latin; keep CJK scripts untouched but casefold safe
    s = s.casefold()
    # Remove leading/trailing punctuation and collapse multiple punctuation
    s = re.sub(r"[\u3000\s]+", " ", s)  # full-width space -> normal
    s = re.sub(r"[\p{P}\p{S}]+", " ", s) if hasattr(re, "_pattern_type") else s
    # Fallback punctuation strip: remove common ascii punct
    s = re.sub(r"[\.,;:!\?\-_/\\\(\)\[\]\{\}\|\*\^\$`~\"'“”‘’·]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_aliases(raw: str) -> list[str]:
    if not raw:
        return []
    raw = normalize_text(raw)
    # Split on common separators including CJK punctuation
    parts = re.split(r"[\n,;，、/\\\|]+", raw)
    return [p.strip() for p in parts if p and p.strip()]

