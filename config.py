BASE_URL = "https://ndlea.gov.ng"
NEWS_LIST_URL = "https://ndlea.gov.ng/news"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_LISTING_PAGES = 15
REQUEST_DELAY = 1.2
TIMEOUT = 25

NON_ENFORCEMENT_TITLE_KEYWORDS = [
    "recruitment", "screening", "interview", "training", "course",
    "conference", "speech", "keynote", "appointment", "promotion",
    "inaugurat", "meeting", "award", "public notice", "wada",
    "sensitisation", "sensitization", "advocacy", "lecture",
    "mou", "memorandum of understanding", "partnership",
    "world drug day", "commemorat", "celebration", "dialogue",
]