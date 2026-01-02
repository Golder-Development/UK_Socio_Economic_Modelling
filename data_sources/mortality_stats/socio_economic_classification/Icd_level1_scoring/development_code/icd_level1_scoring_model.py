"""
ICD Level-1 Socio-Economic Classification Engine
------------------------------------------------

Lexicon-driven, weighted, explainable classifier with hard overrides.

Designed to classify ICD descriptions (any revision) into the
locked Level-1 Socio-Economic Mortality Taxonomy.

Author: (your project)
"""

from __future__ import annotations

import os
import re
import argparse
from typing import Dict, List, Tuple
import pandas as pd


# ------------------------------------------------------------
# Locked Level-1 taxonomy
# ------------------------------------------------------------

L1 = {
    "L1_01": "Infectious and Communicable Diseases",
    "L1_02": "Maternal and Early-Life Mortality",
    "L1_03": "Congenital and Developmental Conditions",
    "L1_04": "Later-Life Mortality",
    "L1_05": "Chronic Non-Communicable Diseases",
    "L1_06": "Respiratory and Environmental Disease",
    "L1_07": "Injury and Accidental Harm",
    "L1_08": "Violence and Conflict",
    "L1_09": "Self-Harm and Substance Use",
    "L1_10": "Ill-Defined, Administrative, and Other Causes",
}


# ------------------------------------------------------------
# Hard overrides (structural truths)
# ------------------------------------------------------------

HARD_OVERRIDES = {
    "L1_02": [
        ("puerperal", "token"),
        ("pregnancy", "token"),
        ("childbirth", "token"),
        ("delivery", "token"),
        ("abortion", "token"),
        ("ectopic", "token"),
        ("newborn", "token"),
        ("neonat", "substring"),
        ("immaturity", "token"),
        ("at birth", "phrase"),
        ("early infancy", "phrase"),
    ],
    "L1_03": [
        ("congenital", "token"),
        ("malformation", "token"),
        ("deformit", "substring"),
        ("spina bifida", "phrase"),
        ("cleft palate", "phrase"),
        ("harelip", "token"),
        ("clubfoot", "token"),
        ("haemophilia", "token"),
    ],
    "L1_08": [
        ("homicide", "token"),
        ("murder", "token"),
        ("execution", "token"),
        ("war", "token"),
        ("battle", "token"),
        ("assault", "token"),
    ],
    "L1_09": [
        ("suicide", "token"),
    ],
    "L1_01": [
        # infectious organism anchors
        ("streptococc", "substring"),
        ("staphylococc", "substring"),
        ("pneumococc", "substring"),
        ("mycobacter", "substring"),
        ("clostrid", "substring"),
        ("bordetella", "substring"),
        ("variola", "token"),
        ("poliomyel", "substring"),
        ("ricketts", "substring"),
        ("trypanosom", "substring"),
        ("leishmaniasis", "token"),
        ("malaria", "token"),
        ("yellow fever", "phrase"),
        ("infectious hepatitis", "phrase"),
        ("haemorrhagic fever", "phrase"),
        ("arthropod borne", "phrase"),
        ("venereal", "token"),
    ],
    "L1_10": [
        ("cause unknown", "phrase"),
        ("found dead", "phrase"),
        ("observation without need for further medical care", "phrase"),
        ("pyrexia of unknown origin", "phrase"),
    ],
}


# ------------------------------------------------------------
# Text utilities
# ------------------------------------------------------------

def normalise(text: str) -> str:
    text = str(text).lower()
    text = text.replace("—", " ").replace("-", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def matches(text: str, term: str, match_type: str) -> bool:
    if match_type == "token":
        return term in text.split()
    if match_type == "phrase":
        return term in text
    if match_type == "substring":
        return term in text
    if match_type == "regex":
        return re.search(term, text) is not None
    return False


# ------------------------------------------------------------
# Lexicon loading
# ------------------------------------------------------------

def load_lexicons(lex_dir: str) -> Dict[str, List[dict]]:
    lexicons: Dict[str, List[dict]] = {}

    for fn in os.listdir(lex_dir):
        if not fn.lower().endswith(".csv"):
            continue

        match = re.search(r"(L1_\d{2})", fn)
        if not match:
            continue

        code = match.group(1)
        df = pd.read_csv(os.path.join(lex_dir, fn))

        rows = []
        for _, r in df.iterrows():
            rows.append({
                "term": str(r["term"]).strip().lower(),
                "weight": int(r["weight"]),
                "match_type": str(r["match_type"]).strip().lower(),
            })

        lexicons[code] = rows

    missing = set(L1.keys()) - set(lexicons.keys())
    if missing:
        raise ValueError(f"Missing lexicons for: {missing}")

    return lexicons


# ------------------------------------------------------------
# Scoring logic
# ------------------------------------------------------------

def apply_hard_override(text: str) -> str | None:
    for code in ["L1_02", "L1_03", "L1_08", "L1_09", "L1_01", "L1_10"]:
        for term, mtype in HARD_OVERRIDES.get(code, []):
            if matches(text, term, mtype):
                return code
    return None


def score_description(description: str, lexicons: Dict[str, List[dict]]) -> Tuple[str, dict]:
    text = normalise(description)

    override = apply_hard_override(text)
    if override:
        scores = {c: 0 for c in L1}
        scores[override] = 999
        return override, scores

    scores = {c: 0 for c in L1}

    for code, terms in lexicons.items():
        for t in terms:
            if matches(text, t["term"], t["match_type"]):
                scores[code] += t["weight"]

    best = max(scores.items(), key=lambda kv: kv[1])[0]
    return best, scores


def confidence_from_scores(scores: dict) -> str:
    vals = sorted(scores.values(), reverse=True)
    top = vals[0]
    second = vals[1] if len(vals) > 1 else 0
    margin = top - second

    if top >= 999:
        return "high"
    if top >= 18 and margin >= 6:
        return "high"
    if top >= 10 and margin >= 3:
        return "medium"
    return "low"


# ------------------------------------------------------------
# DataFrame processing
# ------------------------------------------------------------

def split_multi_codes(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        codes = [c.strip() for c in str(r["icd_code"]).split(",")]
        for c in codes:
            rr = r.copy()
            rr["icd_code"] = c
            rows.append(rr)
    return pd.DataFrame(rows)


def classify_dataframe(df: pd.DataFrame, lex_dir: str) -> pd.DataFrame:
    lexicons = load_lexicons(lex_dir)

    out = []
    for _, r in df.iterrows():
        code, scores = score_description(r["description"], lexicons)
        out.append({
            "icd_version": r["icd_version"],
            "icd_code": r["icd_code"],
            "description": r["description"],
            "level1_code": code,
            "level1_name": L1[code],
            "classification_confidence": confidence_from_scores(scores),
        })

    return pd.DataFrame(out)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--lex_dir", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    df.columns = [c.lower().strip() for c in df.columns]

    if "icdcode" in df.columns and "icd_code" not in df.columns:
        df.rename(columns={"icdcode": "icd_code"}, inplace=True)

    if "description" not in df.columns:
        desc_cols = [c for c in df.columns if c not in ("icd_code", "icd_version")]
        if len(desc_cols) >= 2:
            df["description"] = (
                df[desc_cols[0]].astype(str) + " — " + df[desc_cols[1]].astype(str)
            )
        else:
            raise ValueError("No description column found")

    df["icd_version"] = df.get("icd_version", "ICD-UNK")
    df = split_multi_codes(df)

    result = classify_dataframe(df, args.lex_dir)
    result.to_csv(args.output_csv, index=False)


if __name__ == "__main__":
    main()
