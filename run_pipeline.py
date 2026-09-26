"""Main entry point for the NDLEA event-level scraper."""

from scrape_listings import scrape_listings
from scrape_articles import scrape_articles
from extract_events import extract_events_from_article, is_primarily_non_enforcement
from validate_and_export import build_dataframe, run_validation, export_csv
import config

def main():
    print("1. Scraping listing pages...")
    listings = scrape_listings(max_pages=config.MAX_LISTING_PAGES)

    print("2. Scraping full articles...")
    articles = scrape_articles(listings)  # add limit=N while testing

    print("3. Filtering non-enforcement articles...")
    enforcement = [
        a for a in articles
        if not is_primarily_non_enforcement(a["title"], a["body"])
    ]

    print("4. Extracting events...")
    all_events = []
    for art in enforcement:
        all_events.extend(extract_events_from_article(art))

    print("5. Building DataFrame & validating...")
    df = build_dataframe(all_events)
    run_validation(df)

    print("6. Exporting CSV...")
    export_csv(df, path="ndlea_events_event_level.csv")
    print("Done.")

if __name__ == "__main__":
    main()