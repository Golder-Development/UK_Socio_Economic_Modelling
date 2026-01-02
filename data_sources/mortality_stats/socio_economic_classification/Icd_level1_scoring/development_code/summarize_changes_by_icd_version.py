# Summarize changes by ICD version and from->to category
diff["from_to"] = diff["level1_code"] + "->" + diff["level1_code_scored"]
summary_changes = (
    diff.groupby(["icd_version","from_to"])
        .size()
        .reset_index(name="count")
        .sort_values(["icd_version","count"], ascending=[True, False])
)
summary_path = os.path.join(base_dir, "lexicon_model_change_summary.csv")
summary_changes.to_csv(summary_path, index=False)

# Also provide per-ICD counts per category for the scored model
counts_paths = {}
for n, outp in new_maps.items():
    df = pd.read_csv(outp)
    c = df.groupby(["level1_code","level1_name"]).size().reset_index(name="code_count").sort_values("level1_code")
    p = os.path.join(base_dir, f"icd{n}_scored_counts.csv")
    c.to_csv(p, index=False)
    counts_paths[n] = p

summary_path, counts_paths
