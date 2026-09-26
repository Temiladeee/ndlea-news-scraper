# Cell 2: HTTP helpers + listing scraper

def safe_get(url: str, retries: int = 3) -> Optional[requests.Response]:
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=TIMEOUT)
            if r.status_code == 200:
                return r
            print(f"  [{r.status_code}] {url}")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(2 * (attempt + 1))
    return None


def parse_listing_page(html: str) -> List[Dict]:
    """Extract article cards from a news listing page."""
    soup = BeautifulSoup(html, "lxml")
    items = []
    seen = set()

    # Compact posts (main list)
    for a in soup.select("a.compact-post, a[href*='/blog/']"):
        href = a.get("href", "")
        if "/blog/" not in href:
            continue
        full_url = urljoin(BASE_URL, href)
        if full_url in seen:
            continue
        seen.add(full_url)

        title_tag = a.find("h3") or a.find("h2") or a.find("h4")
        title = title_tag.get_text(strip=True) if title_tag else a.get_text(" ", strip=True)[:200]
        meta = a.select_one(".post-meta")
        pub_raw = meta.get_text(" ", strip=True) if meta else ""
        # strip view count
        pub_raw = re.sub(r"\s*\d+\s*$", "", pub_raw).strip()
        pub_raw = re.sub(r"\s*<i.*", "", pub_raw).strip()

        items.append({
            "title": title,
            "url": full_url,
            "publication_date_raw": pub_raw,
        })
    return items


def scrape_listings(max_pages: int = MAX_LISTING_PAGES) -> List[Dict]:
    all_items = []
    seen_urls = set()
    for page in tqdm(range(1, max_pages + 1), desc="Listing pages"):
        url = f"{NEWS_LIST_URL}?page={page}"
        resp = safe_get(url)
        if not resp:
            print(f"Stopping at page {page} (no response)")
            break
        items = parse_listing_page(resp.text)
        if not items:
            print(f"No items on page {page}, stopping")
            break
        new = 0
        for it in items:
            if it["url"] not in seen_urls:
                seen_urls.add(it["url"])
                all_items.append(it)
                new += 1
        print(f"  Page {page}: {len(items)} cards, {new} new")
        time.sleep(REQUEST_DELAY)
    return all_items


# Run
listings = scrape_listings()
print(f"\nTotal unique articles collected: {len(listings)}")
listings[:3]