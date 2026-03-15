# community/utils/profanity.py
import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# Core word list — stems/roots only; variants are handled by normalization.
# Keeping this focused reduces false positives vs. an exhaustive list.
# ---------------------------------------------------------------------------
PROFANITY_LIST: list[str] = [
    # Sexual / explicit
    'fuck', 'fck', 'fuk', 'fuq',
    'shit', 'sht',
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
    'kys',          # "kill yourself" abbreviation
    'killyourself',
    'killurself',
    'dieasshole',
    'godie',
    'suicide',
    'selfharm',
    'cutmyself',
]

# Words that CONTAIN a bad stem but are perfectly innocent.
# These are checked BEFORE flagging, using the full (space-preserved) normalized text.
WHITELIST: set[str] = {
    # "ass" stem
    'assassin', 'assassinate', 'assassination',
    'classic', 'classics', 'classical',
    'class', 'classes', 'classify', 'classification',
    'mass', 'masses', 'massive',
    'pass', 'passes', 'passion', 'passionate', 'passive',
    'grass', 'grassy',
    'glass', 'glasses',
    'brass',
    'bass',
    'cassette', 'cassandra',
    'harassment',    # contains "rass"
    'embarrass', 'embarrassment',
    'ambassador',
    'assistance', 'assistant', 'assess', 'asset', 'assets',
    'compass',
    'surpass',
    'crass',
    'harass',
    # "cock" stem
    'cockerel', 'cockatoo', 'cockatiel', 'cocktail', 'cocoa',
    'peacock', 'weathercock', 'woodcock',
    # "dick" stem
    'dictionary', 'dictate', 'dictator', 'dictation', 'diction',
    'benedict', 'benediction', 'predict', 'verdict', 'edict',
    'addicted', 'addiction',
    # "fag" stem  (UK usage = cigarette / bundle of sticks)
    'fagot',    # bundle of sticks — note: also a common misspelling of slur, keep short list
    # "rape" stem — plant/agriculture
    'drape', 'drapes', 'grape', 'grapes', 'grapevine',
    'landscape', 'escape', 'scrape',
    'rapeseed', 'oilseed',   # legitimate crop
    # "slut" — Scandinavian surname / place suffix
    'slutsk',
    # "cum" — Latin prefix (common in English words)
    'document', 'documents', 'documentary', 'documentation',
    'accumulate', 'accumulation', 'accumulated',
    'cucumber',
    'scum',      # borderline — keep whitelisted; context matters
    # "shit" stem
    'bullshit',  # NOTE: this is itself profanity — remove if you want to block it
    # "piss" stem
    'mississippi',
    # "bitch" stem — female dog, female animal
    'bitcoin',
}

# ---------------------------------------------------------------------------
# Leet-speak / substitution normalization map
# ---------------------------------------------------------------------------
_NORMALIZE_MAP: dict[str, str] = {
    '@': 'a',
    '4': 'a',
    '3': 'e',
    '€': 'e',
    '1': 'i',
    '!': 'i',
    '|': 'i',
    '0': 'o',
    '$': 's',
    '5': 's',
    '+': 't',
    '7': 't',
    '9': 'g',
    '6': 'b',
    '8': 'b',
    'ph': 'f',   # "phuck" → "fuck"
    'ck': 'k',
    'qu': 'k',
    'x': 'ks',
}

# Regex to collapse repeated characters: "fuuuuck" → "fuk" (keep 2 max, then de-dup in check)
_REPEATED_CHARS_RE = re.compile(r'(.)\1{2,}')

# Regex to strip punctuation / separators between letters: "f.u.c.k" → "fuck"
_SEPARATOR_RE = re.compile(r'[\s\.\-_\*\^\~\`\'\"]+')


def _strip_accents(text: str) -> str:
    """Decompose Unicode and remove combining marks: 'fück' → 'fuck'."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
    """
    Full normalization pipeline:
      1. Unicode decomposition (strips accents / homoglyphs)
      2. Lowercase
      3. Multi-char substitutions (ph → f)
      4. Single-char leet substitutions
      5. Remove separators between letters (f.u.c.k → fuck)
      6. Collapse 3+ repeated chars (fuuuck → fuuck → fuk handled at match time)
    """
    text = _strip_accents(text)
    text = text.lower()

    # Multi-char subs first (order matters: 'ph' before single chars)
    for src, dst in _NORMALIZE_MAP.items():
        if len(src) > 1:
            text = text.replace(src, dst)

    # Single-char subs
    for src, dst in _NORMALIZE_MAP.items():
        if len(src) == 1:
            text = text.replace(src, dst)

    # Remove separators
    text = _SEPARATOR_RE.sub('', text)

    # Collapse 3+ repeated chars to 2 (fuuuck → fuuck)
    text = _REPEATED_CHARS_RE.sub(r'\1\1', text)

    return text


def _is_whitelisted(word: str) -> bool:
    """Return True if the full normalized token is an innocent whitelisted word."""
    return word in WHITELIST


def check_profanity(text: str) -> bool:
    """
    Returns True if the text contains profanity.

    Strategy:
      - Tokenise the original text into words (preserves word boundaries).
      - For each token, normalize it and check against the profanity list.
      - A token is only flagged if it is NOT in the whitelist AND contains a bad stem.
      - Also checks the fully-collapsed (no-space) version to catch spaced-out evasions
        like "f u c k" or "s h i t" while keeping per-token whitelist protection.
    """
    if not text or not isinstance(text, str):
        return False

    # --- Pass 1: per-word check (protects whitelist words) ---
    tokens = re.findall(r"[a-zA-Z0-9@$!|€\.\-_\*\^\~\`\'\"]+", text)
    for token in tokens:
        normalized_token = normalize_text(token)
        if _is_whitelisted(normalized_token):
            continue
        for bad in PROFANITY_LIST:
            # Use substring match but only on single tokens to avoid cross-word false positives
            if bad in normalized_token:
                return True

    # --- Pass 2: full collapsed check (catches "f u c k" spaced evasions) ---
    # Strip everything except alphanumeric + leet chars, then normalize
    collapsed = normalize_text(re.sub(r'[^a-zA-Z0-9@$!|€]', '', text))
    for bad in PROFANITY_LIST:
        if bad in collapsed:
            # Before flagging, verify it's not a whitelisted word hiding in collapsed form
            if not _is_whitelisted(collapsed):
                return True

    return False


def get_profanity_matches(text: str) -> list[str]:
    """
    Debug / logging helper — returns list of matched bad words.
    Do NOT expose this output to end users.
    """
    if not text or not isinstance(text, str):
        return []

    found: list[str] = []
    tokens = re.findall(r"[a-zA-Z0-9@$!|€\.\-_\*\^\~\`\'\"]+", text)

    for token in tokens:
        normalized_token = normalize_text(token)
        if _is_whitelisted(normalized_token):
            continue
        for bad in PROFANITY_LIST:
            if bad in normalized_token and bad not in found:
                found.append(bad)

    collapsed = normalize_text(re.sub(r'[^a-zA-Z0-9@$!|€]', '', text))
    for bad in PROFANITY_LIST:
        if bad in collapsed and bad not in found:
            if not _is_whitelisted(collapsed):
                found.append(bad)

    return found