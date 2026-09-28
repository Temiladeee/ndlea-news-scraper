class ValidationError(Exception):
    pass

def validate(df, strict=True, verbose=True):
    hard = {}
    d = df.copy()
    pub = pd.to_datetime(d["publication_date"], errors="coerce")
    inc = pd.to_datetime(d["incident_date"], errors="coerce")

    hard["1_duplicates_after_consolidation"] = d.loc[~d.index.isin(consolidate_events(d).index)]
    hard["2_incident_eq_publication_without_explicit_date"] = d[(inc == pub) & inc.notna() & ~d["_date_note"].isin(ALLOWED_EQ_PUB_NOTES)]
    hard["3_incident_after_publication"] = d[(inc > pub)]
    g = d.groupby(["source_url", "_clause_full"])
    dup_idx = [i for _, grp in g if grp["drug_type"].nunique() > 1 and grp["quantity"].duplicated(keep=False).any()
               for i in grp.index[grp["quantity"].duplicated(keep=False)]]
    hard["4_same_quantity_across_different_drugs"] = d.loc[dup_idx]
    hard["5_multiple_states_in_one_row"] = d[d["state"].fillna("").str.contains(r"[,;/&]| and ")]
    hard["6_arrest_count_zero"] = d[d["arrest_count"] == 0]
    hard["7_negative_quantity"] = d[d["quantity"] < 0]
    hard["8_mg_strength_emitted_as_quantity"] = d[d["unit"].isin(MG_UNITS) & (d["quantity"] <= 1000)]
    hard["9_ambiguous_association_not_flagged"] = d[d["_note"].eq("weighing_no_drug_within_gate") & (d["drug_type"].notna() | (d["extraction_confidence"] != "Low"))]
    hard["10_arrest_count_without_arrest_yes"] = d[d["arrest_count"].notna() & (d["arrest_status"] != "Yes")]
    hard["11_bad_enum_values"] = d[~d["arrest_status"].isin(["Yes", "No", "Not stated"]) | ~d["extraction_confidence"].isin(["High", "Medium", "Low"])]
    hard["12_kg_for_non_mass_unit"] = d[d["quantity_kg"].notna() & ~d["unit"].isin(MASS_UNITS)]
    hard["13_huge_quantity_not_low_without_farm_context"] = d[(d["quantity_kg"] > 5000) & (d["extraction_confidence"] != "Low")
                                                              & ~d["_clause_full"].apply(lambda t: bool(_FARM_RE.search(t)))]
    failures = {k: v for k, v in hard.items() if len(v)}

    if verbose:
        print("=" * 70, f"\nRows: {len(d)}")
        for k in hard:
            print(f"  [{'FAIL' if k in failures else 'ok  '}] {k}: {len(hard[k])}")
        cols = ["article_title", "incident_date", "drug_type", "quantity", "unit", "state", "arrest_count", "arrest_status", "extraction_confidence"]
        print("\n-- 20 random sample rows --");                       print(d.sample(min(20, len(d)), random_state=1)[cols].to_string() if len(d) else "(none)")
        print("\n-- extraction_confidence != High --");               print(d[d["extraction_confidence"] != "High"][cols + ["debug_clause"]].to_string())
        print("\n-- incident_date is NULL --");                       print(d[d["incident_date"].isna()][cols + ["debug_clause"]].to_string())
        print("\n-- drug_type NULL but quantity exists --");          print(d[d["drug_type"].isna() & d["quantity"].notna()][cols + ["debug_clause"]].to_string())
        print("\n-- arrest_count filled AND status 'Not stated' (must be empty) --")
        print(d[d["arrest_count"].notna() & (d["arrest_status"] == "Not stated")][cols].to_string())
        print("\n-- quantity_kg > 5000 --");                          print(d[d["quantity_kg"] > 5000][cols + ["debug_clause"]].to_string())

    if strict and failures:
        EXPORT_COLUMNS = ["event_id","incident_date","publication_date","article_title","incident_type","drug_type",
                  "quantity","unit","quantity_kg","location","state","arrest_count","arrest_status",
                  "arrest_group_id","source_url","extraction_confidence","debug_clause"]

def finalize(df):
    out = consolidate_events(df).reset_index(drop=True)
    out.insert(0, "event_id", range(1, len(out) + 1))
    return out

def export_csv(df, path="ndlea_events.csv", keep_debug=True, force=False):
    final = finalize(df)
    validate(final, strict=not force)          # raises ValidationError unless force=True
    cols = EXPORT_COLUMNS if keep_debug else [c for c in EXPORT_COLUMNS if c != "debug_clause"]
    final[cols].to_csv(path, index=False)
    print(f"Saved {len(final)} rows -> {path}")
    return final[cols]

# Typical run:
# links = get_all_article_links(max_pages=2)
# df_raw = run_pipeline([x["url"] for x in links])
# final_df = export_csv(df_raw)
        raise ValidationError("Validation failed: " + ", ".join(f"{k} ({len(v)} rows)" for k, v in failures.items()))
    return failures
