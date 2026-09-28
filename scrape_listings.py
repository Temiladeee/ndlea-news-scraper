def get_article_links_from_page(page_url):
    r = requests.get(page_url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    links, seen = [], set()
    for a in soup.find_all("a", href=True):
        if "/blog/" in a["href"]:
            url = urllib.parse.urljoin(BASE_URL, a["href"])
            if url not in seen:
                seen.add(url)
                links.append({"title": a.get_text(strip=True) or None, "url": url})
    return links

def get_all_article_links(max_pages=5, page_param_style="query"):
    """page_param_style 'query' -> ?page=N ; 'path' -> /page/N. Confirm the real pattern first."""
    all_links = {}
    for n in range(1, max_pages + 1):
        if n == 1:
            page_url = NEWS_LIST_URL
        elif page_param_style == "query":
            page_url = f"{NEWS_LIST_URL}?page={n}"
        else:
            page_url = f"{NEWS_LIST_URL}/page/{n}"
        print("Listing page", n, page_url)
        try:
            found = get_article_links_from_page(page_url)
        except Exception as e:
            print("  failed:", e); break
        new = [x for x in found if x["url"] not in all_links]
        for x in new: all_links[x["url"]] = x
        print(f"  {len(found)} links, {len(new)} new")
        if not new: break
        polite_sleep()
    return list(all_links.values())
