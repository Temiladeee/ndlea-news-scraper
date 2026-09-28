def fetch_article(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else None

    # Header line looks like "May 10, 2026 - 10:25" -> metadata only
    page_text = soup.get_text("\n", strip=True)
    m = re.search(r"([A-Z][a-z]{2,8}\s+\d{1,2},?\s+\d{4})\s*-\s*\d{1,2}:\d{2}", page_text[:3000])
    pub_raw = m.group(1) if m else None
    try:
        pub_dt = dateparser.parse(pub_raw) if pub_raw else None
    except Exception:
        pub_dt = None

    body = None
    for kw in ({"class_": re.compile(r"(post|blog|entry|article).*(content|body|details)", re.I)},
               {"class_": re.compile(r"content", re.I)}):
        cand = soup.find("div", **kw)
        if cand and len(cand.get_text(strip=True)) > 200:
            body = cand; break
    if body is None:
        best, best_len = None, 0
        for div in soup.find_all("div"):
            n = sum(len(p.get_text(strip=True)) for p in div.find_all("p", recursive=False))
            if n > best_len: best, best_len = div, n
        body = best
    body_text = "\n".join(p.get_text(" ", strip=True) for p in body.find_all("p") if p.get_text(strip=True)) if body else ""

    return {"title": title, "publication_date": pub_dt, "publication_date_raw": pub_raw,
            "body_text": body_text, "source_url": url}
