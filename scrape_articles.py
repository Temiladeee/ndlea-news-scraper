# Cell 3: Article page scraper

def parse_publication_date(raw: str) -> Optional[str]:
    """Return ISO date YYYY-MM-DD or None."""
    if not raw or not raw.strip():
        return None
    try:
        # Common formats: "Sep 20, 2026", "Sep 20, 2026 - 10:40"
        cleaned = re.sub(r"\s*[-–]\s*\d{1,2}:\d{2}.*", "", raw).strip()
        dt = date_parser.parse(cleaned, fuzzy=True, dayfirst=False)
        return dt.date().isoformat()
    except Exception:
        return None


def extract_article(url: str) -> Optional[Dict]:
    resp = safe_get(url)
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "lxml")

    title_tag = soup.select_one("h1.article-title") or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    meta_tag = soup.select_one(".article-meta") or soup.select_one(".post-meta")
    pub_raw = ""
    if meta_tag:
        pub_raw = meta_tag.get_text(" ", strip=True)
        pub_raw = re.sub(r"\s*\d+\s*$", "", pub_raw)          # remove view count
        pub_raw = re.sub(r"\s*[-–]\s*\d{1,2}:\d{2}.*", "", pub_raw).strip()

    body_div = soup.select_one(".article-body") or soup.select_one("article") or soup.select_one(".entry-content")
    if body_div:
        # Keep paragraph structure; convert <br> to newlines
        for br in body_div.find_all("br"):
            br.replace_with("\n")
        paragraphs = [p.get_text(" ", strip=True) for p in body_div.find_all("p") if p.get_text(strip=True)]
        body = "\n\n".join(paragraphs)
        if not body:
            body = body_div.get_text("\n", strip=True)
    else:
        body = ""

    return {
        "title": title,
        "url": url,
        "publication_date_raw": pub_raw,
        "publication_date": parse_publication_date(pub_raw),
        "body": body,
    }


def scrape_articles(listings: List[Dict], limit: Optional[int] = None) -> List[Dict]:
    articles = []
    to_process = listings[:limit] if limit else listings
    for item in tqdm(to_process, desc="Articles"):
        art = extract_article(item["url"])
        if art:
            # Prefer title/pub from article page if richer
            if not art["title"]:
                art["title"] = item.get("title", "")
            if not art["publication_date"]:
                art["publication_date"] = parse_publication_date(item.get("publication_date_raw", ""))
            articles.append(art)
        time.sleep(REQUEST_DELAY)
    return articles


# Start with a small limit for debugging (increase later)
articles = scrape_articles(listings, limit=25)
print(f"Scraped {len(articles)} full articles")
print(articles[0]["title"][:80] if articles else "none")
print("Pub date:", articles[0].get("publication_date") if articles else None)
print("Body length:", len(articles[0]["body"]) if articles else 0)