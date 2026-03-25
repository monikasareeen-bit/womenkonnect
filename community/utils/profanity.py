import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# Core word list — stems/roots only
# ---------------------------------------------------------------------------
PROFANITY_LIST: list[str] = [
    # Sexual / explicit
    'fuck', 'fck', 'fuk', 'fuq',
    'shit', 'sht', 'sex',
    'ass', 'arse',
    'bitch', 'btch',
    'bastard',
    'cunt',
    'dick', 'dck',
    'cock', 'cok',
    'pussy',
    'whore',
    'slut',
    'porn', 'pron',
    'rape', 'rapist',
    # Slurs
    'nigger', 'nigga',
    'faggot', 'fag',
    'retard',
    'chink',
    'spic',
    'kike',
    # Harassment / self-harm
    'kys',
    'killyourself',
    'killurself',
    'dieasshole',
    'godie',
    'suicide',
    'selfharm',
    'cutmyself',
]

# Whitelisted STEMS — if a token's normalized form starts with or equals these,
# it is innocent. Using stem prefixes is safer than full-word matching.
WHITELIST: set[str] = {
    # "ass" stem
    'assassin', 'assassination', 'assassinate',
    'classic', 'classical', 'classify', 'classification',
    'class', 'classes',
    'mass', 'masses', 'massive',
    'pass', 'passes', 'passion', 'passionate', 'passive',
    'grass', 'grassy',
    'glass', 'glasses',
    'brass', 'bass',
    'cassette', 'cassandra',
    'harassment', 'embarrass', 'embarrassment',
    'ambassador',
    'assistance', 'assistant', 'assess', 'asset', 'assets',
    'compass', 'surpass', 'crass', 'harass',
    # "cock" stem
    'cockerel', 'cockatoo', 'cockatiel', 'cocktail', 'cocoa',
    'peacock', 'weathercock', 'woodcock',
    # "dick" stem
    'dictionary', 'dictate', 'dictator', 'dictation', 'diction',
    'benedict', 'benediction', 'predict', 'verdict', 'edict',
    'addicted', 'addiction',
    # "rape" stem
    'drape', 'drapes', 'grape', 'grapes', 'grapevine',
    'landscape', 'escape', 'scrape',
    'rapeseed', 'oilseed',
    # "cum" Latin prefix
    'document', 'documents', 'documentary', 'documentation',
    'accumulate', 'accumulation', 'accumulated',
    'cucumber',
    # "shit" stem
    # "piss" stem
    'mississippi',
    # "bitch" stem
    'bitcoin',
    # "sex" stem — common in legitimate words
    'sexual', 'sexuality', 'sexology', 'sextet', 'sextuplet',
    'bisexual', 'asexual', 'intersex', 'sexism', 'sexist',
}

# ---------------------------------------------------------------------------
# Extended homoglyph / Cyrillic / Unicode lookalike map
# ---------------------------------------------------------------------------
_HOMOGLYPH_MAP: dict[str, str] = {
    # Cyrillic lookalikes
    'а': 'a', 'е': 'e', 'і': 'i', 'о': 'o', 'р': 'p',
    'с': 'c', 'у': 'y', 'х': 'x', 'ѕ': 'z', 'ї': 'i',
    # Greek lookalikes
    'α': 'a', 'β': 'b', 'ε': 'e', 'ι': 'i', 'ο': 'o',
    'ρ': 'p', 'τ': 't', 'υ': 'u', 'χ': 'x',
    # Misc Unicode
    'ø': 'o', 'ö': 'o', 'ü': 'u', 'ä': 'a', 'ñ': 'n',
    '\u200b': '',   # zero-width space
    '\u200c': '',   # zero-width non-joiner
    '\u200d': '',   # zero-width joiner
    '\ufeff': '',   # BOM
}

# Leet-speak map
_LEET_MAP: dict[str, str] = {
    '@': 'a', '4': 'a',
    '3': 'e', '€': 'e',
    '1': 'i', '!': 'i', '|': 'i',
    '0': 'o',
    '$': 's', '5': 's',
    '+': 't', '7': 't',
    '9': 'g', '6': 'b', '8': 'b',
}

# Multi-char substitutions (apply before single-char)
_MULTI_CHAR_MAP: dict[str, str] = {
    'ph': 'f',
    'ck': 'k',
    'qu': 'k',
}

_REPEATED_CHARS_RE = re.compile(r'(.)\1+')  # collapse ALL repeats to 1
_SEPARATOR_RE = re.compile(r'[\s\.\-_\*\^\~\`\'\"]+')


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def _apply_homoglyphs(text: str) -> str:
    return ''.join(_HOMOGLYPH_MAP.get(c, c) for c in text)


def normalize_text(text: str) -> str:
    """
    Full normalization pipeline:
      1. Unicode decomposition (strips accents)
      2. Homoglyph replacement (Cyrillic/Greek lookalikes)
      3. Lowercase
      4. Multi-char leet subs (ph → f)
      5. Single-char leet subs
      6. Remove separators
      7. Collapse ALL repeated chars to 1 (fuuuck → fuk)
    """
    text = _strip_accents(text)
    text = _apply_homoglyphs(text)
    text = text.lower()

    for src, dst in _MULTI_CHAR_MAP.items():
        text = text.replace(src, dst)

    for src, dst in _LEET_MAP.items():
        if len(src) == 1:
            text = text.replace(src, dst)

    text = _SEPARATOR_RE.sub('', text)

    # Collapse ALL repeats to single char: fuuuck → fuk
    text = _REPEATED_CHARS_RE.sub(r'\1', text)

    return text


# Pre-normalize the whitelist so comparisons work after repeat-collapse
# Built lazily on first use since normalize_text must be defined first
_NORMALIZED_WHITELIST: set[str] = set()


def _get_normalized_whitelist() -> set[str]:
    if not _NORMALIZED_WHITELIST:
        for w in WHITELIST:
            _NORMALIZED_WHITELIST.add(normalize_text(w))
    return _NORMALIZED_WHITELIST


def _is_whitelisted(token: str) -> bool:
    """
    Check if a normalized token is whitelisted.
    Both token and whitelist entries are repeat-collapsed via normalize_text,
    so 'clasic' matches normalized('classic') = 'clasic'.
    Also matches if token starts with a whitelisted stem (handles -ed, -ing, -ly suffixes).
    """
    nwl = _get_normalized_whitelist()
    if token in nwl:
        return True
    for w in nwl:
        if token.startswith(w):
            return True
    return False


def _contains_bad_word(normalized: str) -> Optional[str]:
    """Return the matched bad word stem if found, else None."""
    for bad in PROFANITY_LIST:
        # Also normalize the bad word itself (handles repeat collapse)
        norm_bad = _REPEATED_CHARS_RE.sub(r'\1', bad)
        if norm_bad in normalized:
            return bad
    return None


def check_profanity(text: str) -> bool:
    """
    Returns True if the text contains profanity.

    Three passes:
      1. Per-word check — respects whitelist, catches embedded bad words in tokens
      2. Sliding window on normalized full text — catches split evasions like "f u c k"
         while still checking each window slice against whitelist
      3. Collapsed full text — catches spaced/separated evasions
    """
    if not text or not isinstance(text, str):
        return False

    # --- Pass 1: per-word check ---
    tokens = re.findall(r"[^\s]+", text)
    for token in tokens:
        normalized = normalize_text(token)
        if _is_whitelisted(normalized):
            continue
        if _contains_bad_word(normalized):
            return True

    # --- Pass 2: rejoin adjacent short tokens to catch split evasions ---
    # e.g. "f u c k" → tokens ["f","u","c","k"] → joined "fuck"
    # We slide a window of 2–6 adjacent tokens, join them, normalize, and check.
    normalized_full = normalize_text(text)

    raw_tokens = re.findall(r"[^\s]+", text)
    for window_size in range(2, 7):
        for i in range(len(raw_tokens) - window_size + 1):
            joined = ''.join(raw_tokens[i:i + window_size])
            normalized_joined = normalize_text(joined)
            if _is_whitelisted(normalized_joined):
                continue
            if _contains_bad_word(normalized_joined):
                return True

    # --- Pass 3: strip ALL non-alpha chars and check ---
    # Catches "f.u.c.k", "f-u-c-k", mixed separators
    # We must re-tokenize from the original to build a whitelist-safe stripped version.
    # Strategy: normalize each original token individually, strip non-alpha, then
    # only flag if that stripped token is not whitelisted.
    for token in tokens:
        normalized = normalize_text(token)
        stripped_token = re.sub(r'[^a-z]', '', normalized)
        stripped_token = _REPEATED_CHARS_RE.sub(r'\1', stripped_token)
        if _is_whitelisted(stripped_token):
            continue
        for bad in PROFANITY_LIST:
            norm_bad = _REPEATED_CHARS_RE.sub(r'\1', bad)
            if norm_bad in stripped_token:
                return True

    return False


def get_profanity_matches(text: str) -> list[str]:
    """Debug helper — returns matched bad word stems. Do NOT expose to end users."""
    if not text or not isinstance(text, str):
        return []

    found: list[str] = []
    tokens = re.findall(r"[^\s]+", text)

    for token in tokens:
        normalized = normalize_text(token)
        if _is_whitelisted(normalized):
            continue
        match = _contains_bad_word(normalized)
        if match and match not in found:
            found.append(match)

    normalized_full = normalize_text(text)
    stripped = re.sub(r'[^a-z]', '', normalized_full)
    stripped = _REPEATED_CHARS_RE.sub(r'\1', stripped)

    for bad in PROFANITY_LIST:
        norm_bad = _REPEATED_CHARS_RE.sub(r'\1', bad)
        if norm_bad in stripped and bad not in found:
            found.append(bad)

    return found


# ---------------------------------------------------------------------------
# Quick self-test — remove in production
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    tests = [
        # Should be TRUE (profanity)
        ("fuck",            True),
        ("f u c k",         True),
        ("f.u.c.k",         True),
        ("fuuuuck",         True),
        ("fück",            True),   # accented
        ("f_u_c_k",         True),
        ("sh1t",            True),
        ("b1tch",           True),
        ("@ss",             True),
        # Should be FALSE (clean)
        ("classic music",   False),
        ("passionate",      False),
        ("assassination",   False),
        ("cocktail",        False),
        ("dictionary",      False),
        ("grass",           False),
        ("Mississippi",     False),
        ("bitcoin",         False),
        ("grape juice",     False),
        ("escape room",     False),
    ]

    print(f"{'Text':<25} {'Expected':<10} {'Got':<10} {'Pass?'}")
    print("-" * 55)
    all_pass = True
    for text, expected in tests:
        result = check_profanity(text)
        passed = result == expected
        all_pass = all_pass and passed
        status = "✓" if passed else "✗ FAIL"
        print(f"{text:<25} {str(expected):<10} {str(result):<10} {status}")

    print()
    print("All tests passed!" if all_pass else "Some tests FAILED — review above.")