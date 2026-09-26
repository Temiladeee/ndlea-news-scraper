# NDLEA News Event-Level Scraper

Event-level extraction of drug-enforcement incidents from the 
[National Drug Law Enforcement Agency (NDLEA)](https://ndlea.gov.ng) Nigeria news archive.

## Key design rules
- Publication date is metadata only – never used as incident date
- Quantities are associated only with the drug they refer to (no Cartesian product)
- Arrest count is `NaN` when not explicitly stated (never defaulted to 0)
- State/location attached per event clause, not broadcast across the article

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/ndlea-news-scraper.git
cd ndlea-news-scraper
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt