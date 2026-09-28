DRUG_CANON = {   # alias -> canonical name reported in the dataset
    "cannabis sativa": "cannabis", "indian hemp": "cannabis", "marijuana": "cannabis",
    "canadian loud": "loud", "crystal meth": "methamphetamine", "meth": "methamphetamine",
    "exol 5": "exol-5", "exol": "exol-5", "codeine syrup": "codeine",
}
DRUG_VOCAB = sorted([
    "cannabis sativa", "cannabis oil", "cannabis seeds", "cannabis", "indian hemp", "marijuana",
    "skunk", "canadian loud", "loud", "colorado", "arizona", "monkey tail", "skuchies",
    "cocaine", "heroin", "methamphetamine", "crystal meth", "meth",
    "tramadol", "codeine syrup", "codeine", "diazepam", "rohypnol",
    "exol-5", "exol 5", "exol", "mdma", "ecstasy", "ketamine", "captagon",
    "tapentadol", "pentazocine", "bromazepam", "psychotropic substances", "narcotics",
], key=len, reverse=True)
# Generic terms often used as an appositive for a named strain ("Loud, a strain of imported cannabis").
GENERIC_DRUGS = {"cannabis", "psychotropic substances", "narcotics"}
DRUG_RE = re.compile(r"\b(" + "|".join(re.escape(d) for d in DRUG_VOCAB) + r")\b", re.IGNORECASE)

def canon(drug):
    d = drug.lower().strip()
    return DRUG_CANON.get(d, d)

MASS_UNITS = {
    "kg": 1.0, "kgs": 1.0, "kilogram": 1.0, "kilograms": 1.0, "kilogramme": 1.0, "kilogrammes": 1.0,
    "g": 1e-3, "gram": 1e-3, "grams": 1e-3, "gramme": 1e-3, "grammes": 1e-3,
    "mg": 1e-6, "milligram": 1e-6, "milligrams": 1e-6,
    "tonne": 1000.0, "tonnes": 1000.0, "ton": 1000.0, "tons": 1000.0,
}
MG_UNITS = {"mg", "milligram", "milligrams"}
NON_MASS_UNITS = {
    "tablet", "tablets", "pill", "pills", "capsule", "capsules", "bottle", "bottles",
    "sachet", "sachets", "wrap", "wraps", "parcel", "parcels", "block", "blocks",
    "carton", "cartons",
    "litre", "litres", "liter", "liters", "ampoule", "ampoules",   # extras seen in real articles
}
ALL_UNITS = set(MASS_UNITS) | NON_MASS_UNITS
UNIT_ALT = "|".join(sorted((re.escape(u) for u in ALL_UNITS), key=len, reverse=True))
QTY = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"

# "<qty> <unit> [of] <up to 4 words>"  (drug is looked up inside the words)
TEMPLATE1_RE = re.compile(
    rf"(?<![\w.,])(?P<qty>{QTY})\s*(?P<unit>{UNIT_ALT})\b\s*(?:of\s+)?"
    rf"(?P<gap>[A-Za-z][A-Za-z\-]*(?:\s+[A-Za-z][A-Za-z\-]*){{0,3}})", re.IGNORECASE)
# "weighing <qty> <unit>"
WEIGHING_RE = re.compile(
    rf"(?:weighing|weighed|totalling|totaling|amounting\s+to)\s+(?:about\s+|approximately\s+|over\s+)?"
    rf"(?P<qty>{QTY})\s*(?P<unit>{UNIT_ALT})\b", re.IGNORECASE)
QTY_UNIT_ANY_RE = re.compile(rf"(?<![\w.,])(?:{QTY})\s*(?:{UNIT_ALT})\b", re.IGNORECASE)

DISTANCE_GATE = 100   # max characters between a drug mention and its "weighing" quantity

STATE_ALIASES = {"abuja": "FCT", "fct": "FCT", "federal capital territory": "FCT"}
NIGERIAN_STATES = ["Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno","Cross River",
    "Delta","Ebonyi","Edo","Ekiti","Enugu","Gombe","Imo","Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi",
    "Kwara","Lagos","Nasarawa","Niger","Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba",
    "Yobe","Zamfara","FCT","Abuja","Federal Capital Territory"]
MONTH_RE = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
WEEKDAY = r"(?:(?:Mon|Tues?|Wed(?:nes)?|Thu(?:rs)?|Fri|Sat(?:ur)?|Sun)(?:day)?\s+)?"
DATE_FULL_RE = re.compile(rf"\b{WEEKDAY}(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{MONTH_RE},?\s+(\d{{4}})\b", re.I)
DATE_NOYEAR_RE = re.compile(rf"\b{WEEKDAY}(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{MONTH_RE}\b(?!,?\s+\d{{4}})", re.I)
SAME_DAY_RE = re.compile(r"\b(?:on\s+)?the\s+same\s+day\b|\bsame\s+day\b", re.I)
MONTHS = {m: i + 1 for i, m in enumerate(["january","february","march","april","may","june","july",
                                          "august","september","october","november","december"])}

def parse_incident_date(text, publication_date, last_known_date):
    """Returns (datetime|None, note). Never returns a date after publication_date."""
    def guard(d, note):
        if publication_date is not None and d.date() > publication_date.date():
            return None, "future_date_rejected"
        return d, note

    m = DATE_FULL_RE.search(text)
    if m:
        try:
            return guard(datetime(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))), "explicit_full_date")
        except ValueError:
            return None, "invalid_date"

    m = DATE_NOYEAR_RE.search(text)
    if m:
        if publication_date is None:
            return None, "no_year_no_reference"
        day, month = int(m.group(1)), MONTHS[m.group(2).lower()]
        pub_d = publication_date.date()
        for year in (publication_date.year, publication_date.year - 1):
            try:
                cand = datetime(year, month, day)
            except ValueError:
                return None, "invalid_date"
            if cand.date() <= pub_d:
                # Previous-year fallback is only unambiguous for a recent event (e.g. a December raid in a January article).
                if year != publication_date.year and (pub_d - cand.date()).days > 60:
                    return None, "future_date_rejected"
                return cand, "explicit_no_year_inferred"
        return None, "future_date_rejected"

    if SAME_DAY_RE.search(text) and last_known_date is not None:
        return last_known_date, "same_day_reference"
    return None, "no_date_found"

def distinct_dates_in(text):
    return {(m.group(1), m.group(2).lower()) for m in DATE_NOYEAR_RE.finditer(text)} | \
           {(m.group(1), m.group(2).lower(), m.group(3)) for m in DATE_FULL_RE.finditer(text)}
    SENT_SPLIT_RE = re.compile(r"(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bProf)(?<!\bHon)(?<!\bCol)(?<!\bNo)(?<!\bSt)(?<!\bLt)(?<!\bGen)"
                           r"[.!?](?=\s+[A-Z0-9\"\u201c])")
CLAUSE_SPLIT_RE = re.compile(r";|\s+while\s+|\s+as\s+(?!well\b)", re.I)

def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n+", text) if p.strip()]

def split_sentences(paragraph):
    parts = SENT_SPLIT_RE.split(re.sub(r"\s+", " ", paragraph))
    return [p.strip() for p in parts if p.strip()]

def _has_event_content(fragment):
    return bool(DRUG_RE.search(fragment) and QTY_UNIT_ANY_RE.search(fragment))

def split_clauses(sentence):
    """Split on ';' / 'while' / 'as' - but only where the right-hand side carries its own drug+quantity.
    That keeps suspect-name lists ('A; B and C') and 'arrested as they ...' together with their event."""
    bounds = list(CLAUSE_SPLIT_RE.finditer(sentence))
    cuts = []
    for i, b in enumerate(bounds):
        right_end = bounds[i + 1].start() if i + 1 < len(bounds) else len(sentence)
        if _has_event_content(sentence[b.end():right_end]):
            cuts.append(b)
    pieces, start = [], 0
    for b in cuts:
        pieces.append(sentence[start:b.start()]); start = b.end()
    pieces.append(sentence[start:])
    return [p.strip(" ,;") for p in pieces if p.strip(" ,;")]
    NON_ENFORCEMENT_TITLE_RE = re.compile(
    r"recruit|screening|interview|training|workshop|conference|summit|symposium|keynote|speech|declaration|"
    r"appoint|promot|decorat|award|public notice|memorandum|\bmou\b|partnership|cooperation|collaborat|"
    r"sensiti[sz]ation|enlightenment|advocacy|wada|graduation|passing out|anniversary|courtesy|visit|"
    r"handover|inaugurat|commission(?:s|ed|ing)?\b|donat", re.I)
ENFORCEMENT_VERB_RE = re.compile(r"\b(arrest(?:ed)?|nabbed|apprehended|seiz(?:ed|ure)|intercept(?:ed|ion)|recover(?:ed|y)|raid(?:ed)?|busted|dismantl(?:ed|ing)|destroy(?:ed)?|uncovered|discovered|found)\b", re.I)

def concrete_enforcement_sentences(body):
    """Sentences with a verb + drug + quantity (candidate real incidents)."""
    out = []
    for para in split_paragraphs(body):
        for s in split_sentences(para):
            if ENFORCEMENT_VERB_RE.search(s) and DRUG_RE.search(s) and QTY_UNIT_ANY_RE.search(s):
                out.append(s)
    return out

def is_enforcement_article(title, body):
    concrete = concrete_enforcement_sentences(body)
    if not concrete:
        return False
    if NON_ENFORCEMENT_TITLE_RE.search(title or ""):
        # Speeches / MoUs / campaigns often quote statistics. Require at least one dated, concrete incident.
        return any(DATE_FULL_RE.search(s) or DATE_NOYEAR_RE.search(s) for s in concrete)
    return True
    def _pick_backward_drug(preceding):
    """Nearest drug mention before a 'weighing' quantity. Prefers a specific strain over a generic
    descriptor that sits between them. Returns (canonical_drug, distance_in_chars) or (None, None)."""
    matches = list(DRUG_RE.finditer(preceding))
    if not matches:
        return None, None
    chosen = matches[-1]
    if canon(chosen.group(1)) in GENERIC_DRUGS and len(matches) > 1:
        for m in reversed(matches[:-1]):
            if canon(m.group(1)) not in GENERIC_DRUGS:
                chosen = m; break
    return canon(chosen.group(1)), len(preceding) - chosen.end()

def extract_drug_quantity_pairs(clause):
    """Returns list of dicts: drug_type, quantity, unit, quantity_kg, confidence, note.
    Never combines every drug with every quantity: each quantity is tied to ONE drug by a local pattern."""
    results, claimed = [], []
    overlaps = lambda a, b: any(not (b <= s or a >= e) for s, e in claimed)

    # Pattern A: "<qty> <unit> [of] <drug>"  (also handles "A and B" coordination, one match per quantity)
    for m in TEMPLATE1_RE.finditer(clause):
        qty = float(m.group("qty").replace(",", ""))
        unit = m.group("unit").lower()
        if unit in MG_UNITS and qty <= 1000:
            continue                                   # tablet STRENGTH (e.g. tramadol 225mg), not a quantity
        gap = m.group("gap")
        dm = DRUG_RE.search(gap)
        if not dm or dm.start() > 40:                  # distance gate
            continue
        span = (m.start("qty"), m.start("gap") + dm.end())
        if overlaps(*span):
            continue
        claimed.append(span)
        results.append({"drug_type": canon(dm.group(1)), "quantity": qty, "unit": unit,
                        "quantity_kg": round(qty * MASS_UNITS[unit], 6) if unit in MASS_UNITS else None,
                        "confidence": "High" if dm.start() <= 20 else "Medium", "note": "qty_unit_of_drug"})

    # Pattern B: "<drug> ... weighing <qty> <unit>"
    for m in WEIGHING_RE.finditer(clause):
        qty = float(m.group("qty").replace(",", ""))
        unit = m.group("unit").lower()
        if unit in MG_UNITS and qty <= 1000:
            continue
        if overlaps(m.start("qty"), m.end("unit")):
            continue
        drug, dist = _pick_backward_drug(clause[:m.start()])
        if drug is None or dist > DISTANCE_GATE:
            results.append({"drug_type": None, "quantity": qty, "unit": unit,
                            "quantity_kg": round(qty * MASS_UNITS[unit], 6) if unit in MASS_UNITS else None,
                            "confidence": "Low", "note": "weighing_no_drug_within_gate"})
            continue
        kg = round(qty * MASS_UNITS[unit], 6) if unit in MASS_UNITS else None
        for ex in results:                            # same seizure counted in parcels AND kg -> one row, keep kg
            if ex["drug_type"] == drug and ex["unit"] in NON_MASS_UNITS and unit in MASS_UNITS:
                ex.update(quantity=qty, unit=unit, quantity_kg=kg, confidence="Medium",
                          note="merged_count_and_weight_kept_kg")
                break
        else:
            results.append({"drug_type": drug, "quantity": qty, "unit": unit, "quantity_kg": kg,
                            "confidence": "Medium", "note": "drug_weighing_qty"})
    return results
    NUM_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
ARREST_WORDS = r"arrested|nabbed|apprehended|detained|taken\s+into\s+custody"
ARREST_TERM_RE = re.compile(rf"\b({ARREST_WORDS}|arrest\s+of)\b", re.I)
NO_ARREST_RE = re.compile(r"\bno\s+(?:one\s+was\s+|suspects?\s+(?:was|were)\s+)?arrest(?:s|ed)?\b|\bwithout\s+(?:any\s+)?arrests?\b|"
                          r"\bnobody\s+was\s+arrested\b", re.I)
PERSON_NOUNS = (r"(?:other\s+)?(?:suspects?|persons?|people|men|women|traffickers?|dealers?|individuals?|pushers?|"
                r"couriers?|youths?|foreigners?|nationals?|PWDs?|members|drug\s+(?:suspects|traffickers|dealers|barons))")
COUNT_RE = re.compile(rf"\b(?P<num>\d{{1,4}}|{'|'.join(NUM_WORDS)})\s+(?:\d{{1,2}}-year-old\s+)?{PERSON_NOUNS}\b", re.I)
NAME_TOKEN = r"[A-Z][a-z]+(?:[-'][A-Za-z]+)?"
NAME = rf"{NAME_TOKEN}(?:\s+{NAME_TOKEN}){{1,2}}"
NAME_BEFORE_RE = re.compile(rf"(?P<name>{NAME})(?:,\s*\d{{1,2}},?)?\s+(?:was\s+|were\s+)?(?:{ARREST_WORDS})")
NAME_AFTER_RE = re.compile(rf"(?:{ARREST_WORDS})\s+(?:another\s+|a\s+)?(?:[A-Z]{{2,5}}\s+)?(?P<name>{NAME})(?:,\s*\d{{1,2}}|\s+with\b|\s+over\b|\s+in\b|\s+at\b)")
NAME_BLACKLIST = {"national","drug","law","enforcement","agency","command","operations","operatives","operative",
                  "unit","special","nigeria","nigerian","airport","commander","officers","officer","police","customs",
                  "service","state","federal","ndlea","marc","chairman","director","the","interdiction","patrol"}

def _valid_names(regex, text):
    names = set()
    for m in regex.finditer(text):
        n = m.group("name")
        toks = [t.lower() for t in n.split()]
        if any(t in NAME_BLACKLIST for t in toks) or STATE_RE.fullmatch(n):
            continue
        names.add(n)
    return names

def extract_arrest_info(clause):
    """(arrest_count|None, arrest_status). Clause-local only; count is None unless stated; never 0."""
    if NO_ARREST_RE.search(clause):
        return None, "No"
    terms = list(ARREST_TERM_RE.finditer(clause))
    if not terms:
        return None, "Not stated"
    for m in COUNT_RE.finditer(clause):
        if min(abs(m.start() - t.start()) for t in terms) <= 120:
            raw = m.group("num").lower()
            return float(NUM_WORDS.get(raw) or int(raw)), "Yes"
    names = _valid_names(NAME_BEFORE_RE, clause) | _valid_names(NAME_AFTER_RE, clause)
    if names:
        return float(len(names)), "Yes"
    return None, "Yes"       # arrest language present, count genuinely unstated

def extract_state(text, anchor=None):
    """(state|None, ambiguous). One state only; if several are named, pick the nearest to the anchor and flag it."""
    found = [(m.start(), STATE_ALIASES.get(m.group(1).lower(), m.group(1).title())) for m in STATE_RE.finditer(text)]
    if not found:
        return None, False
    distinct = {s for _, s in found}
    if len(distinct) == 1:
        return found[0][1], False
    if anchor is None:
        return None, True
    return min(found, key=lambda x: abs(x[0] - anchor))[1], True

_LOC_RE = re.compile(r"\b(?:at|in|along|around|near|within|inside)\s+(?:the\s+)?((?:[A-Z][\w'/\-]*)(?:\s+[A-Z][\w'/\-]*){0,3})")
_LOC_JUNK = re.compile(r"\b(?:Mon|Tues?|Wednes|Thurs?|Fri|Satur|Sun)day\b|\b(?:January|February|March|April|May|June|July|August|"
                       r"September|October|November|December)\b|\b\d{1,2}(?:st|nd|rd|th)\b|\b\d{4}\b|\bState\b|"
                       r"\b(?:NDLEA|National|Agency|Command|Operatives)\b", re.I)
def extract_location(clause):
    """Best-effort place name from the same clause (dates / 'State' stripped). None if unsure."""
    for m in _LOC_RE.finditer(clause):
        loc = _LOC_JUNK.sub("", m.group(1)).strip(" ,/-")
        if loc and not STATE_RE.fullmatch(loc):
            return loc
    return None

_FARM_RE = re.compile(r"\b(farm|farms|plantation|hectares?|destroy(?:ed)?|destruction|eradicat\w*)\b", re.I)
_LAB_RE = re.compile(r"\b(laborator(?:y|ies)|clandestine|dismantl\w*|meth\s+lab)\b", re.I)
_INTERDICT_RE = re.compile(r"\b(intercept\w*|checkpoint|patrol\w*|airport|seaport|port|border|bus|vehicle|truck|luggage|courier|parcel)\b", re.I)
def classify_incident_type(clause, arrest_status):
    if _LAB_RE.search(clause):      return "lab_dismantling"
    if _FARM_RE.search(clause):     return "farm_destruction"
    if arrest_status == "Yes":      return "arrest"
    if _INTERDICT_RE.search(clause): return "interdiction"
    return "seizure"
    LIST_ITEM_RE = re.compile(r"^(?:and\s+)?\d")            # fragment starts with a quantity: elliptical list item
OWN_VERB_RE = re.compile(r"\b(recovered|intercepted|seized|found|discovered|arrested|nabbed|apprehended|detained|raided|uncovered)\b", re.I)
ALLOWED_EQ_PUB_NOTES = {"explicit_full_date", "explicit_no_year_inferred", "inherited_from_sentence", "same_day_reference"}

def _qty_anchor(clause):
    m = QTY_UNIT_ANY_RE.search(clause)
    return m.start() if m else None

def process_article(article, article_idx=0):
    title, pub, body = article.get("title"), article.get("publication_date"), article.get("body_text", "")
    if not is_enforcement_article(title, body):
        return []
    events, last_known, group_n = [], None, 0

    for para in split_paragraphs(body):
        for sentence in split_sentences(para):
            sent_dates = distinct_dates_in(sentence)
            sent_date, sent_note = parse_incident_date(sentence, pub, last_known)
            sent_states = {STATE_ALIASES.get(m.group(1).lower(), m.group(1).title()) for m in STATE_RE.finditer(sentence)}
            run_date = run_state = None
            prev_arrest, prev_group = (None, "Not stated"), None
            sent_events = []

            for clause in split_clauses(sentence):
                # ---- date (clause first, then running value inside this sentence, then the sentence's single date)
                c_date, c_note = parse_incident_date(clause, pub, last_known)
                if c_note in ("explicit_full_date", "explicit_no_year_inferred"):
                    date, note, run_date, last_known = c_date, c_note, c_date, c_date
                elif c_note == "same_day_reference":
                    date, note = c_date, c_note
                elif c_note in ("future_date_rejected", "invalid_date"):
                    date, note = None, c_note
                elif run_date is not None:
                    date, note = run_date, "inherited_from_sentence"
                elif len(sent_dates) == 1 and sent_date is not None:
                    date, note = sent_date, "inherited_from_sentence"
                else:
                    date, note = None, "no_date_found"

                # ---- state
                anchor = _qty_anchor(clause)
                state, amb = extract_state(clause, anchor)
                if state is not None:
                    run_state = state
                elif not amb:
                    state = run_state or (next(iter(sent_states)) if len(sent_states) == 1 else None)

                # ---- arrest (clause-local; list continuations inherit from the governing clause)
                count, status = extract_arrest_info(clause)
                group, inherited = None, False
                if status == "Yes":
                    group_n += 1; group = f"{article_idx}-{group_n}"
                    prev_arrest, prev_group = (count, status), group
                elif status == "No":
                    prev_arrest, prev_group = (None, "No"), None
                elif prev_arrest[1] == "Yes" and LIST_ITEM_RE.match(clause) and not OWN_VERB_RE.search(clause):
                    count, status = prev_arrest; group, inherited = prev_group, True

                pairs = extract_drug_quantity_pairs(clause)
                location = extract_location(clause) if pairs else None
                for p in pairs:
                    conf = p["confidence"]
                    if p["drug_type"] is None:
                        conf = "Low"
                    if date is None and conf == "High":
                        conf = "Medium"
                    if note == "same_day_reference" and conf == "High":
                        conf = "Medium"
                    if (amb or inherited) and conf == "High":
                        conf = "Medium"
                    if p["quantity_kg"] and p["quantity_kg"] > 5000 and not _FARM_RE.search(clause):
                        conf = "Low"
                    sent_events.append({
                        "incident_date": date.date().isoformat() if date else None,
                        "publication_date": pub.date().isoformat() if pub else None,
                        "article_title": title,
                        "incident_type": classify_incident_type(clause, status),
                        "drug_type": p["drug_type"], "quantity": p["quantity"], "unit": p["unit"],
                        "quantity_kg": p["quantity_kg"], "location": location, "state": state,
                        "arrest_count": count, "arrest_status": status,
                        "arrest_group_id": group, "source_url": article.get("source_url"),
                        "extraction_confidence": conf, "debug_clause": clause[:200],
                        "_clause_full": clause, "_date_note": note, "_note": p["note"], "_sentence": sentence,
                    })

            # single-event sentence: the sentence's own arrest language belongs to that event (not broadcasting)
            if len(sent_events) == 1 and sent_events[0]["arrest_status"] == "Not stated":
                s_count, s_status = extract_arrest_info(sentence)
                if s_status == "Yes":
                    group_n += 1
                    sent_events[0].update(arrest_count=s_count, arrest_status="Yes", arrest_group_id=f"{article_idx}-{group_n}")
                    if sent_events[0]["incident_type"] in ("seizure", "interdiction"):
                        sent_events[0]["incident_type"] = "arrest"
            events.extend(sent_events)
    return events

def build_dataframe(events):
    cols = ["incident_date","publication_date","article_title","incident_type","drug_type","quantity","unit",
            "quantity_kg","location","state","arrest_count","arrest_status","arrest_group_id","source_url",
            "extraction_confidence","debug_clause","_clause_full","_date_note","_note","_sentence"]
    df = pd.DataFrame(events, columns=cols)
    df["arrest_count"] = pd.to_numeric(df["arrest_count"], errors="coerce")   # NaN stays NaN, never 0
    return df

def run_pipeline(article_urls, verbose=True):
    events = []
    for i, url in enumerate(article_urls):
        if verbose: print(f"[{i+1}/{len(article_urls)}] {url}")
        try:
            art = fetch_article(url)
        except Exception as e:
            print("  FAILED:", e); continue
        events.extend(process_article(art, article_idx=i))
        polite_sleep()
    return build_dataframe(events)

STATE_RE = re.compile(r"\b(" + "|".join(re.escape(s) for s in sorted(NIGERIAN_STATES, key=len, reverse=True)) + r")\b", re.IGNORECASE)
