# NDLEA Event-Level Drug Enforcement Extractor

One row per **incident** (not per article). Publication date is metadata only.

## Design rules

1. Arrest info is **clause-local** — never broadcast an article-level total.
2. `mg` values ≤ 1000 are treated as drug **strength** (e.g. tramadol 225mg), never as a quantity.
3. A quantity is linked to a drug only via explicit local patterns and a ~100-character distance gate.
4. Dates never default to the publication date; any date after publication is rejected.
5. Near-duplicates (same URL + drug + unit + state + quantity within 1%) are consolidated.
6. Non-enforcement articles (MoU, speeches, recruitment, WADA-only, etc.) are excluded.
7. `quantity_kg > 5000` is flagged Low unless the clause mentions farm/plantation/hectares/destruction.
8. Validation **raises** on hard errors; export refuses to write until they are fixed.

## Quick start (Colab)

1. Open `NDLEA_Event_Extractor_v2.ipynb` in Google Colab.
2. Run cells top to bottom.
3. Typical usage at the bottom:

```python
links = get_all_article_links(max_pages=5)
df_raw = run_pipeline([x["url"] for x in links[:20]])
validate(finalize(df_raw), strict=False)
final_df = export_csv(df_raw)
