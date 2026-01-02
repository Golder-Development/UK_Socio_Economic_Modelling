# Fix lexicon loader: some filenames may start with L1 (no underscore parsing). Use regex to extract L1_\d+.
import re, os, pandas as pd

lex = {}
for fn in os.listdir(lex_dir):
    if not fn.lower().endswith(".csv"):
        continue
    m = re.search(r"(L1_\d{2})", fn)
    if not m:
        continue
    code = m.group(1)
    df = pd.read_csv(os.path.join(lex_dir, fn))
    df["term"] = df["term"].astype(str).str.strip().str.lower()
    df["match_type"] = df["match_type"].astype(str).str.strip().str.lower()
    lex[code] = df[["term","weight","match_type","source"]].to_dict("records")

sorted(lex.keys())
