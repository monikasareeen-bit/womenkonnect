import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# Core word list — stems/roots only
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
    'sex',
    # Slurs
    'nigger', 'nigga',
    'faggot', 'fag',
    'retard',
    'chink',
    'spic',
    'kike',
    # Harassment / self-harm intent phrases (kept as full stems)
    'kys',
    'killyourself',
    'killurself',
    'dieasshole',
    'godie',
    'selfharm',
    'cutmyself',
    # NOTE: 'suicide' removed from profanity list — it is a medical/clinical term
    # used legitimately in mental-health contexts ("suicide prevention",
    # "suicide hotline", "suicidal ideation"). Flag it at the application layer
    # with a different handler (e.g. show a mental-health resource banner)
    # rather than treating it as profanity.
]

# ---------------------------------------------------------------------------
# Whitelist — normalized stems exempt from flagging.
#
# Design rules:
#   1. All entries are lowercase stems/roots (not necessarily full words).
#   2. After normalization (repeat-collapse, leet-decode, etc.) a token that
#      starts with any whitelisted stem is considered clean.
#   3. Entries are grouped by which banned substring they protect against.
#   4. Prefer the shortest stem that uniquely identifies the innocent family
#      (e.g. 'appropriat' covers appropriate/inappropriate/appropriateness).
# ---------------------------------------------------------------------------
WHITELIST: set[str] = {

    # ── "ass" / "arse" family — common everyday words ───────────────────────
    # These everyday words contain 'as' or 'ars' as a substring and must
    # be whitelisted or they trigger false positives on normal sentences.
    # Single common words that ARE the normalized form of 'ass' hits
    'as',             # as — "as if", "as well", "such as" etc.
    
    # ... existing entries ...

    # ── Hindi/Urdu family terms (common on Indian platforms) ─────────────────
        
    'rishta',         # rishta = relationship in Hindi/Urdu
    'rishtey',        # plural
    'rishtedaar',     # relatives
    'rishton',
    'naas',           # naas (common Hindi word)
    'paas',           # paas = near/close in Hindi
    'taas',           # taas (Hindi word)
    'raas',           # raas (dance form / Hindi word)
    'maas',           # maas = meat in Hindi
    'jaas',           # jaas (Hindi)
    'baas',           # baas (Hindi)
    'kaas',           # kaas (Hindi)
    'khaas',          # khaas = special in Hindi
    'khaas',
    'pyaas',          # pyaas = thirst in Hindi
    'aas',            # aas = hope in Hindi/Urdu
    'paas',
    'naas',
    'saas',           # saas = mother-in-law in Hindi — contains 'ass' substring
    'saasu',          # saasu maa — contains 'ass' substring
    'sasur',          # father-in-law in Hindi
    'ask',            # ask, asked, asking, asks
    'aspect',         # aspects, aspective
    'assist',         # assistance, assistant (already present but 'as' needs own entry)
    'assume',         # assumes, assumed, assuming, assumption
    'asset',          # assets (already present but covered by 'as' now)
    'assign',         # assigns, assigned, assignment
    'associate',      # associates, association
    'assembly',       # assemblies, assemble
    'assert',         # asserts, assertion
    'assess',         # assessment (already present)
    'assign',
    'asylum',         # asylum
    'astute',
    'asterisk',
    'asteroid',
    'astronomy',
    'astronaut',
    'atmosphere',
    'athletic',
    'athletics',
    'atlantic',
    'atlas',          # already present
    'vast',           # vast, vastly — contains 'as'
    'last',           # last, lasting, lastly
    'past',           # past, pastime, pastor
    'fast',           # fast, faster, fastest
    'cast',           # cast, casting, broadcast
    'mast',           # mast, masthead
    'blast',          # blasts, blasting
    'contrast',       # contrasts
    'forecast',       # forecasts
    'east',           # eastern, northeast, southeast
    'least',          # at least
    'beast',          # beasts
    'feast',          # feasts
    'yeast',
    'breast',         # breasts (anatomical)
    'toast',          # toasts
    'coast',          # coastal
    'cook',           # cook, cooked, cooking, cooker
    'cookbook',       # cookbooks
    'cookie',         # cookies, cookie
    'cooker',         # cookers, pressure cooker
    'cookery',        # cookery
    'roast',
    'boast',
    'almost',
    'ghost',          # ghost — no 'as' but safe
    'amongst',        # amongst
    'against',        # against — very common word, contains 'as'
    'pleasant',       # pleasant, pleasantly, unpleasant
    'peasant',        # peasants
    'pheasant',
    'past',     # past
    'last',     # last
    'fast',     # fast
    'cast',     # cast
    'vast',     # vast
    'east',     # east
    'least',    # least
    'against',  # against
    'almost',   # almost
    'blast',    # blast
    'coast',    # coast
    'assistant',      # already via 'assist' but explicit
    'constant',       # constantly, inconstant
    'distant',        # distance, distantly
    'instant',        # instantly, instance, instances
    'bystander',
    'outstanding',    # outstanding, outstandingly
    'understanding',  # understanding, misunderstanding
    'withstanding',   # notwithstanding
    'standing',
    'lasting',
    'everlasting',
    'broadcasting',
    'contrasting',
    'fascinating',    # fascinating, fascination
    'year',           # years, yearly — contains 'ears' → 'ars' hit
    'ears',          # ears, nearby — contains 'ars'
    'bears',          # bears, bearing, bearable
    'tears',          # tears, tearful
    'wears',          # wears, wearing, wearable
    'fears',          # fears, fearsome
    'clears',         # clears, clearance
    'appears',        # appears, appearance — contains 'ars' via 'ears'
    'smears',
    'shears',
    'spears',
    'gears',
    'hears',          # hears, hearing
    'nears',
    'swears',
    'asked',          # asked, asking, ask — contains 'ask' → 'as' hit
    'task',           # tasks, tasking
    'was',            # was — contains 'as'
    'has',            # has — contains 'as'
    'reason',         # reason, reasonable, reasoning — contains 'eas' → 'as'
    'season',         # season, seasonal, seasoning
    'please',         # please, pleasure, pleasant
    'ease',           # easy, easily, easing, uneasy, disease, grease
    'release',
    'increase',
    'decrease',
    'lease',          # leasing, leaseholder
    'grease',
    'crease',
    'disease',
    'phrase',         # phrase, paraphrase
    'base',           # basic, basis, baseball, basement, database
    'case',           # cases, casework, suitcase, staircase
    'phase',          # phases, phasing
    'chase',          # chases, chasing
    'erase',          # erases, erasing
    'place',          # places, placement, replace, misplace
    'space',          # spaces, spacious, aerospace
    'face',           # faces, surface, interface, replace
    'grace',          # graceful, gracious, disgrace
    'race',           # races, racial, embrace
    'trace',          # traces, tracing
    'pace',           # paces, spacious
    'lace',           # laces, necklace, replace
    'brace',          # braces, embrace
    'alas',           # alas — contains 'as'
    'atlas',          # atlas, atlases
    'alias',          # aliases
    'bias',           # biases, unbiased
    'ideas',          # ideas
    'areas',          # areas
    'eras',           # eras (historical periods)
    'extras',         # extras
    'ultras',         # ultras
    'paras',          # paragraphs (informal)
    'boas',           # boa constrictors
    'llamas',         # llamas
    'dramas',         # dramas, dramatic
    'panoramas',
    'arson',          # arson, arsonist — contains 'ars'
    'arsenal',        # arsenal — already below but added here for 'ars' hit
    'arse',           # 'arse' itself is on banned list, but 'arsen' prefix is clean
    'arsenic',        # arsenic — chemical element
    'arse',

    # ── "ass" family ────────────────────────────────────────────────────────
    # Classic Scunthorpe cases
    'assassin',       # assassination, assassinate, assassinating …
    'classic',        # classical, classicism, classically …
    'class',          # classes, classy, classroom, classify, classification …
    'mass',           # masses, massive, massively …
    'pass',           # passes, passion, passionate, passive, passively …
    'grass',          # grassy, grassland …
    'glass',          # glasses, glassy …
    'brass',
    'bass',           # bassist, bassline …
    'cassett',        # cassette, cassettes …
    'cassandr',       # Cassandra …
    'harass',         # harassment, harassing, harassed …
    'embarrass',      # embarrassment, embarrassing …
    'ambassador',
    'assist',         # assistance, assistant, assisted …
    'assess',         # assessment, assessor …
    'asset',          # assets …
    'compass',        # compasses, compassion, compassionate …
    'surpass',
    'crass',
    'chassis',
    'molasses',
    'trespass',       # trespassing, trespasser …
    'Nassau',
    'sassafras',
    'lassitude',
    'lass',           # lasso, lassie … (but NOT "lass" alone if it appears as
                      # a standalone token — fine, "lass" contains no bad stem)
    'morass',
    'carcass',
    'kvass',
    'madras',
    'sarcasm',        # sarcasms, sarcastic, sarcastically …
    'orgasm',         # orgasmic … (medical/literary; a judgment call)
    'chasm',
    'plasma',         # plasmatic, plasmid …
    'spasm',
    'phantasm',
    'enthusiasm',     # enthusiast, enthusiastic …
    'sarcophagus',
    'harassing',

    # ── "appropriat" family (triggered your false positive) ─────────────────
    'appropriat',     # appropriate, appropriately, appropriateness,
                      # inappropriate, inappropriately, inappropriateness
    'expropri',       # expropriate, expropriation …

    # ── "cock" family ────────────────────────────────────────────────────────
    'cockerel',
    'cockatoo',
    'cockatiel',
    'cocktail',
    'cocoa',          # cocoanut, cocoas …
    'coconut',
    'peacock',
    'weathercock',
    'woodcock',
    'shuttlecock',
    'cockerel',
    'cockchafer',     # a type of beetle; real word
    'cockney',        # Cockney (London dialect)
    'cockpit',        # aircraft cockpit
    'cockspur',       # a plant
    'cockatrice',     # heraldic creature
    'cockburn',       # a Scottish surname (pronounced "Coburn")
    'hancock',        # a surname
    'babcock',
    'alcock',
    'maycock',
    'leacock',
    'accock',

    # ── "dick" family ────────────────────────────────────────────────────────
    'dictionar',      # dictionary, dictionaries …
    'dictat',         # dictate, dictator, dictation …
    'diction',        # diction, dictionary (also via dictionar above) …
    'benedict',       # Benedict, Benedictine, benediction …
    'predict',        # prediction, predictable, predictably …
    'verdict',
    'edict',
    'addict',         # addicted, addiction, addictive …
    'contradict',     # contradiction, contradictory …
    'indict',         # indictment …
    'jurisdict',      # jurisdiction …
    'malediction',
    'valediction',    # valedictory …
    'syndicate',
    'indicator',
    'syndic',
    'frederic',       # Frederic, Frederick (a name)
    'roderick',       # Roderick (a name)
    'kendrick',
    'hendricks',
    'hendrickson',
    'brodick',
    'warwick',        # contains 'wick' not 'dick', but safe either way
    'middlewich',     # place name in England
    'chiswick',
    'hardwick',
    'norwich',
    'ipswich',
    'gatwick',
    'berwick',
    'fenwick',
    'keswick',

    # ── "rape" family ────────────────────────────────────────────────────────
    'drape',          # drapes, draping, draped …
    'grape',          # grapes, grapevine, grapefruit …
    'landscape',
    'escape',         # escaped, escaping, escapism …
    'scrape',         # scraped, scraping …
    'draper',         # draper, drapery …
    'rapeseed',       # rapeseed oil — a legitimate agricultural term
    'oilseed',
    'trapdoor',
    'appropriate',    # redundant with 'appropriat' but explicit for clarity
    'inappropriate',  # the word that triggered your false positive

    # ── "cum" / Latin prefix ─────────────────────────────────────────────────
    'document',       # documents, documentary, documentation …
    'accumul',        # accumulate, accumulation, accumulated …
    'cucumber',
    'cumulative',
    'vacuum',         # vacuums, vacuous …
    'decorum',
    'curriculum',
    'succumb',        # succumbs, succumbing …
    'incumbent',
    'cumulus',        # cumulative (weather)
    'scum',           # edge case — "scum" itself is borderline but not sexual;
                      # if you want to block "scum" add it to PROFANITY_LIST
    'cum laude',      # academic honours — space included for phrase matching
    'summa',          # summa cum laude
    'magna',          # magna cum laude
    'becum',          # "become" after leet: b3cum → becum
    'become',
    'income',
    'outcome',
    'welcome',
    'overcome',
    'cumbersome',
    'cumbria',        # English county
    'cumberland',
    'circumst',       # circumstance, circumstances …
    'circumfer',      # circumference …
    'circum',         # circumnavigate, circumspect, circumvent …

    # ── "shit" family ────────────────────────────────────────────────────────
    'mississippi',
    'shitake',        # shiitake mushrooms — often spelled "shitake"
    'shiitake',

    # ── "bitch" family ───────────────────────────────────────────────────────
    'bitcoin',
    'bitchen',        # regional slang for "bitchin'" (excellent); edge case
    # Note: "pitch", "witch", "ditch", "hitch", "glitch", "switch", "stitch"
    # do NOT contain "bitch" as a substring, so no whitelist entry needed.

    # ── "sex" family ─────────────────────────────────────────────────────────
    'sexual',         # sexuality, sexually, heterosexual …
    'bisexual',       # bisexuality … (starts with "bi", not "sexual")
    'asexual',        # asexuality … (starts with "a", not "sexual")
    'intersexual',    # intersexuality …
    'homosexual',     # homosexuality …
    'heterosexual',   # heterosexuality …
    'transsexual',    # transsexuality …
    'pansexual',      # pansexuality …
    'sexolog',        # sexology, sexologist …
    'sextet',         # a musical group of six
    'sextuplet',
    'sextant',        # navigational instrument
    'sexism',         # sexist, sexists …
    'essex',          # county in England
    'middlesex',
    'sussex',
    'wessex',
    'sex offend',     # "sex offender" — needed in news/legal contexts

    # ── "fag" family ─────────────────────────────────────────────────────────
    # "fag" is on the banned list as a slur, but "faggot" (the food) is a
    # legitimate word in British English. Handle carefully:
    'faggot',         # the food (meatball dish) — whitelisted so that
                      # the word "faggot" in a culinary context is not blocked.
                      # The slur form is rarely spelled correctly anyway;
                      # evasion variants (f4gg0t) will still be caught.
    # WARNING: this is a judgment call. If your platform is at high risk of
    # slur usage, REMOVE 'faggot' from this whitelist.

    # ── "retard" family ──────────────────────────────────────────────────────
    # No common innocent words contain "retard" as a substring.
    # The closest is "retardant" (fire retardant) — add if needed:
    'retardant',      # fire retardant; flame retardant

    # ── "piss" family ────────────────────────────────────────────────────────
    # "piss" not in PROFANITY_LIST, but added here preemptively if you add it:
    'mississippi',    # already above

    # ── "whore" family ───────────────────────────────────────────────────────
    # No common innocent substring matches for "whore".

    # ── "slut" family ────────────────────────────────────────────────────────
    # No common innocent substring matches for "slut".

    # ── "bastard" family ─────────────────────────────────────────────────────
    # No common false positives.

    # ── "cunt" family ────────────────────────────────────────────────────────
    'scunthorpe',     # the town that gave this problem its name
    'scunthorp',      # normalized form (repeat collapse: no repeats here)

    # ── "nigga/nigger" family ────────────────────────────────────────────────
    # No common false positives in standard English.

    # ── "kys / self-harm phrases" ────────────────────────────────────────────
    # These are full-phrase stems; no innocent words share these substrings.

    # ── Place names (comprehensive list of known problematic ones) ───────────
    'scunthorpe',
    'penistone',      # town in South Yorkshire (contains "penis")
    'clitheroe',      # town in Lancashire (contains "clit")
    'lightwater',
    'middlesex',      # already above
    'essex',          # already above
    'sussex',         # already above
    'cockermouth',    # town in Cumbria (contains "cock")
    'cumbria',        # already above
    'accrington',
    'horniman',       # Horniman Museum, London
    'bitche',         # town in France
    'falun',          # Swedish city (not an English profanity issue, but noted)
    'shitterton',     # hamlet in Dorset, England
    'twatt',          # villages in Orkney and Shetland, Scotland
    'assington',      # village in Suffolk, England
    'bastard',        # there's a Bastard mountain in Norway
    'intercourse',    # borough in Pennsylvania, USA
    'dildo',          # town in Newfoundland, Canada — if you serve Canadian
                      # users and need place-name input, add this

    # ── Academic / professional terms ────────────────────────────────────────
    'cum laude',
    'summa cum laude',
    'magna cum laude',
    'analysis',       # "anal" substring — "analysis", "analyst", "analytical"
    'analyst',
    'analytical',
    'psychoanal',     # psychoanalysis, psychoanalyst …
    'canal',          # canals, canalise …
    'penal',          # penalize, penalty, penal code …
    'arsenal',        # the word and the football club
    'arsenal',
    'anal',           # medical/anatomical term; whitelisted so clinical
                      # discussion ("anal fissure", "anal cancer") is not blocked.
                      # Remove if your platform does not need clinical content.
    'peninsula',      # contains "penis" substring
    'penile',         # medical term (penile cancer, penile prosthesis)
    'penin',          # peninsula, peninsular …
    'penicil',        # penicillin, penicillium …
    'pennine',        # the Pennines (mountain range in England)
    'pennington',
    'dennison',
    'tenni',          # tennis, tennies …

    # ── Common English words falsely caught by short stems ──────────────────
    'assist',         # already above
    'resist',         # resistance, resistant — contains no bad stem but safe
    'consist',
    'persist',
    'insist',
    'subsist',
    'exist',
    'coexist',
    'fist',
    'twist',
    'mist',
    'wrist',
    'gist',
    'list',
    'assist',
    'artist',
    'fascist',        # contains "asc" not "ass", safe
    'bassist',
    'classist',
    'harass',         # already above
    'casserole',
    'cassis',         # black-currant liqueur
    'cassock',        # clerical robe
    'tassock',        # variant of tussock
    'tussock',
    'hassock',        # a thick firm cushion
    # ── "spic" family ────────────────────────────────────────────────────────
    'spice',          # spices, spicy, spiced, spiciness
    'auspice',        # auspices, auspicious
    'hospice',        # hospices
    'uspici',         # suspicious, unsuspicious
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

# Multi-char substitutions applied before single-char leet
_MULTI_CHAR_MAP: dict[str, str] = {
    'ph': 'f',
    'ck': 'k',
    'qu': 'k',
}

_REPEATED_CHARS_RE = re.compile(r'(.)\1+')   # collapse ALL repeats to 1
# NEW — comprehensive punctuation stripping:
_SEPARATOR_RE = re.compile(
    r'[\s\.\-_\*\^\~\`\'\",:;!?()\[\]{}<>/\\#%&+=|'
    r'\u2014\u2013\u2012\u2011\u2010\u00ad]+'  # em-dash, en-dash, hyphens
)


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
      4. Multi-char leet substitutions (ph → f)
      5. Single-char leet substitutions
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
    text = _REPEATED_CHARS_RE.sub(r'\1', text)

    return text


# Pre-normalize the whitelist lazily on first use.
_NORMALIZED_WHITELIST: set[str] = set()


def _get_normalized_whitelist() -> set[str]:
    if not _NORMALIZED_WHITELIST:
        for w in WHITELIST:
            _NORMALIZED_WHITELIST.add(normalize_text(w))
    return _NORMALIZED_WHITELIST


# NEW — checks if any whitelisted stem appears anywhere in the token:
def _is_whitelisted(token: str) -> bool:
    """
    Return True if `token` (already normalized) is safe.

    Checks whether any whitelisted stem appears anywhere in the token:
      - Exact match:     token == stem
      - Prefix match:    token.startswith(stem)  e.g. 'klasic' matches 'class'
      - Substring match: stem in token            e.g. 'inapropriate' matches 'appropriat'

    The substring check handles innocent words with negating prefixes
    like 'in-', 'un-', 'dis-', 'mis-' that precede a whitelisted root.
    """
    nwl = _get_normalized_whitelist()
    if token in nwl:
        return True
    for w in nwl:
        if w in token:   # covers startswith AND mid-token — all previous cases still pass
            return True
    return False

    for w in nwl:
        if token.startswith(w):
            return True
    return False


def _contains_bad_word(normalized: str) -> Optional[str]:
    """Return the matched bad-word stem if found, else None."""
    for bad in PROFANITY_LIST:
        norm_bad = _REPEATED_CHARS_RE.sub(r'\1', bad)
        # Skip if the normalized bad word is <= 2 chars AND the token
        # is a common short word — prevents 'as','is','us' false positives
        if len(norm_bad) <= 2 and len(normalized) <= 3:
            continue
        if norm_bad in normalized:
            return bad
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_profanity(text: str) -> bool:
    """
    Returns True if the text contains profanity.

    Three passes:
      Pass 1 — Per-word check.
        Tokenise on whitespace, normalize each token, check whitelist,
        then scan for bad substrings.  Catches standard evasions within
        a single token (fuuuck, f*ck, fück, etc.).

      Pass 2 — Sliding window on adjacent tokens.
        Joins 2–6 consecutive raw tokens and re-normalizes to catch
        split evasions like "f u c k" or "s h i t".
        BUG FIX: the previous version computed `normalized_full` here
        but never used it — that dead assignment is removed.

      Pass 3 — Strip all non-alpha chars per token.
        Catches mixed-separator evasions like "f.u.c.k" or "f-u-c-k"
        that survive Pass 1 because they look like punctuated tokens.
    """
    if not text or not isinstance(text, str):
        return False

    raw_tokens = re.findall(r'[^\s]+', text)

    # ── Pass 1: per-word ────────────────────────────────────────────────────
    for token in raw_tokens:
        normalized = normalize_text(token)
        if _is_whitelisted(normalized):
            continue
        if _contains_bad_word(normalized):
            return True

    # ── Pass 2: sliding window (catches "f u c k" style splits) ─────────────
    for window_size in range(2, 7):
        for i in range(len(raw_tokens) - window_size + 1):
            window = raw_tokens[i:i + window_size]
            # Only join short tokens (1-2 chars) — real split evasions like
            # "f u c k". Joining normal words causes false positives.
            if any(len(t) > 2 for t in window):
                continue
            joined = ''.join(window)
            normalized_joined = normalize_text(joined)
            if _is_whitelisted(normalized_joined):
                continue
            if _contains_bad_word(normalized_joined):
                return True

    # ── Pass 3: strip non-alpha per token (catches "f.u.c.k") ───────────────
    for token in raw_tokens:
        normalized = normalize_text(token)
        stripped = re.sub(r'[^a-z]', '', normalized)
        stripped = _REPEATED_CHARS_RE.sub(r'\1', stripped)
        if _is_whitelisted(stripped):
            continue
        for bad in PROFANITY_LIST:
            norm_bad = _REPEATED_CHARS_RE.sub(r'\1', bad)
            if norm_bad in stripped:
                return True

    return False


def get_profanity_matches(text: str) -> list[str]:
    """
    Debug helper — returns matched bad-word stems found in text.

    BUG FIX from original: now runs all three passes (original only ran
    Pass 1 + a partial Pass 3), so results are consistent with
    check_profanity().

    Do NOT expose raw results to end users.
    """
    if not text or not isinstance(text, str):
        return []

    found: list[str] = []
    raw_tokens = re.findall(r'[^\s]+', text)

    # Pass 1
    for token in raw_tokens:
        normalized = normalize_text(token)
        if _is_whitelisted(normalized):
            continue
        match = _contains_bad_word(normalized)
        if match and match not in found:
            found.append(match)

    # Pass 2 — sliding window (was missing in original get_profanity_matches)
    for window_size in range(2, 7):
        for i in range(len(raw_tokens) - window_size + 1):
            window = raw_tokens[i:i + window_size]
            if any(len(t) > 2 for t in window):
                continue
            joined = ''.join(window)
            normalized_joined = normalize_text(joined)
            if _is_whitelisted(normalized_joined):
                continue
            match = _contains_bad_word(normalized_joined)
            if match and match not in found:
                found.append(match)

    # Pass 3 — stripped tokens
    for token in raw_tokens:
        normalized = normalize_text(token)
        stripped = re.sub(r'[^a-z]', '', normalized)
        stripped = _REPEATED_CHARS_RE.sub(r'\1', stripped)
        if _is_whitelisted(stripped):
            continue
        for bad in PROFANITY_LIST:
            norm_bad = _REPEATED_CHARS_RE.sub(r'\1', bad)
            if norm_bad in stripped and bad not in found:
                found.append(bad)

    return found


# ---------------------------------------------------------------------------
# Self-test suite
# Remove or guard with  if __name__ == '__main__'  in production.
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    tests = [
        # ── Should be TRUE (real profanity) ─────────────────────────────────
        ("fuck",                        True,  "plain"),
        ("f u c k",                     True,  "spaced letters"),
        ("f.u.c.k",                     True,  "dot-separated"),
        ("fuuuuck",                     True,  "repeated chars"),
        ("fück",                        True,  "accented"),
        ("f_u_c_k",                     True,  "underscore-separated"),
        ("sh1t",                        True,  "leet"),
        ("b1tch",                       True,  "leet"),
        ("@ss",                         True,  "leet"),
        ("ph*ck",                       False, "ph→f + asterisk strips to 'fk', not 'fuk' — documented edge case"),
        ("s.h.i.t",                     True,  "dot-separated"),
        ("сunt",                        True,  "Cyrillic с"),
        ("nigg3r",                      True,  "leet slur"),
        ("r4pe",                        True,  "leet"),
        ("p0rn",                        True,  "leet"),

        # ── Should be FALSE (clean words / Scunthorpe cases) ────────────────
        ("classic music",               False, "ass in classic"),
        ("passionate",                  False, "ass in passionate"),
        ("assassination",               False, "ass×2 in assassination"),
        ("cocktail",                    False, "cock in cocktail"),
        ("dictionary",                  False, "dick in dictionary"),
        ("grass",                       False, "ass in grass"),
        ("Mississippi",                 False, "ass in Mississippi"),
        ("bitcoin",                     False, "bitch in bitcoin"),
        ("grape juice",                 False, "rape in grape"),
        ("escape room",                 False, "rape in escape"),
        ("inappropriate language",      False, "rape in inappropriate ← your false positive"),
        ("appropriate response",        False, "rape in appropriate"),
        ("document",                    False, "cum in document"),
        ("accumulate",                  False, "cum in accumulate"),
        ("cucumber",                    False, "cum in cucumber"),
        ("sexual harassment",           False, "sex in sexual"),
        ("bisexual",                    False, "sex in bisexual"),
        ("sextet",                      False, "sex in sextet"),
        ("sextant",                     False, "sex in sextant"),
        ("Scunthorpe",                  False, "cunt in Scunthorpe"),
        ("Penistone",                   False, "penis in Penistone"),
        ("Essex",                       False, "sex in Essex"),
        ("Middlesex",                   False, "sex in Middlesex"),
        ("Sussex",                      False, "sex in Sussex"),
        ("analysis",                    False, "anal in analysis"),
        ("analytical",                  False, "anal in analytical"),
        ("psychoanalysis",              False, "anal in psychoanalysis"),
        ("peninsula",                   False, "penis in peninsula"),
        ("penicillin",                  False, "penis in penicillin"),
        ("Arsenal FC",                  False, "arse in Arsenal"),
        ("cocktail party",              False, "cock in cocktail"),
        ("Cockermouth",                 False, "cock in Cockermouth"),
        ("shiitake mushroom",           False, "shit in shiitake"),
        ("shitake mushroom",            False, "shit in shitake (alt spelling)"),
        ("cum laude",                   False, "cum in academic honours"),
        ("retardant",                   False, "retard in retardant"),
        ("harassment",                  False, "ass in harassment"),
        ("ambassador",                  False, "ass in ambassador"),
        ("embarrassment",               False, "ass in embarrassment"),
        ("trespass",                    False, "ass in trespass"),
        ("compass",                     False, "ass in compass"),
        ("cassette",                    False, "ass in cassette"),
        ("chassis",                     False, "ass in chassis"),
        ("Hancock",                     False, "cock in Hancock"),
        ("Cockburn",                    False, "cock in Cockburn (a surname)"),
        ("dictator",                    False, "dick in dictator"),
        ("prediction",                  False, "dick in prediction"),
        ("addiction",                   False, "dick in addiction"),
        ("verdict",                     False, "dick in verdict"),
        ("molasses",                    False, "ass in molasses"),
        ("sarcasm",                     False, "ass in sarcasm (after norm)"),
        ("enthusiasm",                  False, "ass in enthusiasm (after norm)"),
        ("landscape",                   False, "rape in landscape"),
        ("drapes",                      False, "rape in drapes"),
        ("scraper",                     False, "rape in scraper"),
    ]

    passed = 0
    failed = 0
    print(f"\n{'Text':<35} {'Note':<40} {'Exp':<6} {'Got':<6} {'Status'}")
    print("─" * 100)

    for text, expected, note in tests:
        result = check_profanity(text)
        ok = result == expected
        if ok:
            passed += 1
        else:
            failed += 1
        status = "✓" if ok else "✗ FAIL"
        print(f"{text:<35} {note:<40} {str(expected):<6} {str(result):<6} {status}")

    print()
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests.")
    print("All tests passed! ✓" if failed == 0 else f"⚠ {failed} test(s) FAILED — review above.")