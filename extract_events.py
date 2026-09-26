# Cell 5: Lexicons & regex patterns

DRUG_PATTERNS = [
    # order matters: longer / more specific first
    (r"canadian\s+loud|scottish\s+loud|ghanaian\s+loud|\bloud\b", "Loud"),
    (r"\bskunk\b|\bcannabis\s+sativa\b|\bcannabis\b|\bmarijuana\b", "cannabis"),
    (r"\bcolos?\b|\bcolorado\b|\badb[\s\-]?chminaca\b", "Colorado/Colos"),
    (r"\bcocaine\b", "cocaine"),
    (r"\bheroin\b", "heroin"),
    (r"\bmethamphetamine\b|\bmeth\b|\bp2p\b", "methamphetamine"),
    (r"\btramadol\b", "tramadol"),
    (r"\bcodeine\b", "codeine"),
    (r"\bdiazepam\b|\bvalium\b", "diazepam"),
    (r"\bpregabalin\b|\blyrica\b", "pregabalin"),
    (r"\bcaptagon\b|\bjihadi\s+drug\b", "captagon"),
    (r"\becstasy\b|\bmdma\b", "ecstasy"),
    (r"\brohypnol\b|\bflunitrazepam\b", "rohypnol"),
    (r"\bkhat\b", "khat"),
    (r"\bopioids?\b", "opioids"),
    (r"\bfentanyl\b", "fentanyl"),
]

# Quantity + unit capture (number can have commas)
QTY_UNIT_RE = re.compile(
    r"""
    (?P<qty>[\d,]+(?:\.\d+)?)\s*
    (?:
        (?P<unit_kg>kg|kilograms?|kilos?)|
        (?P<unit_g>g|grams?)|
        (?P<unit_mg>mg|milligrams?)|
        (?P<unit_t>tonnes?|tons?)|
        (?P<unit_tab>tablets?|pills?|capsules?)|
        (?P<unit_bot>bottles?)|
        (?P<unit_sach>sachets?|wraps?|parcels?|blocks?|cartons?)
    )
    """,
    re.I | re.VERBOSE,
)

# Date patterns inside body (operational dates)
DATE_PATTERNS = [
    # "Wednesday 16th September 2026", "Friday 18th September"
    re.compile(
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"(?:\s+(\d{4}))?",
        re.I,
    ),
    # "16th September 2026", "23 rd June 2026"
    re.compile(
        r"\b(\d{1,2})\s*(?:st|nd|rd|th)?\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"(?:\s+(\d{4}))?",
        re.I,
    ),
    # "on 16/09/2026" or "16-09-2026"
    re.compile(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b"),
]

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

NIGERIA_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu",
    "FCT", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi",
    "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun",
    "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
    "Abuja",  # common shorthand
]

STATE_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in sorted(NIGERIA_STATES, key=len, reverse=True)) + r")\b",
    re.I,
)

ARREST_YES_RE = re.compile(
    r"\b(arrested|apprehended|nabbed|detained|taken into custody|in custody|"
    r"docked|remanded|caught|intercepted.*?suspect)\b",
    re.I,
)
ARREST_NO_RE = re.compile(
    r"\b(no arrest|without arrest|suspect(?:s)? (?:fled|escaped|at large)|"
    r"nobody was arrested|no one was arrested)\b",
    re.I,
)
ARREST_COUNT_RE = re.compile(
    r"\b(?:(?P<num>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"a|an)\s+)?(?:suspects?|persons?|traffickers?|kingpins?|accomplices?|"
    r"individuals?|men|women|ladies|teenagers?|grandpas?|grandmas?)\b"
    r".{0,40}?\b(?:arrested|nabbed|apprehended|detained|taken into custody)\b|"
    r"\b(?:arrested|nabbed|apprehended|detained)\s+(?:(?P<num2>\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an)\s+)?"
    r"(?:suspects?|persons?|traffickers?|kingpins?)",
    re.I,
)

WORD_TO_NUM = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}