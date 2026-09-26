
all_events = []
for art in tqdm(enforcement_articles, desc="Extracting events"):
    all_events.extend(extract_events_from_article(art))

df = pd.DataFrame(all_events)

if df.empty:
    print("No events extracted — check filters / scraping")
else:
    # Stable event_id
    def make_id(row):
        key = f"{row['source_url']}|{row['incident_date']}|{row['drug_type']}|{row['quantity']}|{row['unit']}|{row['state']}|{row['arrest_count']}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    df.insert(0, "event_id", df.apply(make_id, axis=1))
    df = df.drop_duplicates(subset=["event_id"]).reset_index(drop=True)

    # Ensure arrest_count is nullable float (never forced to 0)
    df["arrest_count"] = pd.to_numeric(df["arrest_count"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["quantity_kg"] = pd.to_numeric(df["quantity_kg"], errors="coerce")

    print(f"Total event rows: {len(df)}")
    print(df["extraction_confidence"].value_counts())
    print(df["arrest_status"].value_counts())