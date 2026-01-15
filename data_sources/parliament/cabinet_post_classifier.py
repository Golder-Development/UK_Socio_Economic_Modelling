"""
Classify UK cabinet/ministerial post titles into:
- "senior" (Secretaries of State OR senior Cabinet positions)
- "non_senior"
- "ambiguous" (needs explicit override decision)

Designed to be conservative and auditable:
- deterministic regex rules
- clear reason/match rule written out
- optional JSON overrides for edge cases

Usage examples:

1) Classify the titles list you provided:
python scripts/classify_posts.py \
  --posts-csv /mnt/data/post_field_analysis.csv \
  --out-csv data/derived/posts_classified.csv

2) Apply classification onto an appointments dataset (e.g. cabinet_ministers.csv):
python scripts/classify_posts.py \
  --posts-csv /mnt/data/post_field_analysis.csv \
  --out-csv data/derived/posts_classified.csv \
  --apply-to data/raw/cabinet_ministers.csv \
  --apply-post-col post \
  --applied-out data/derived/cabinet_ministers_classified.csv

3) Add an overrides file (recommended for long-term accuracy):
python scripts/classify_posts.py \
  --posts-csv /mnt/data/post_field_analysis.csv \
  --overrides-json configs/post_overrides.json \
  --out-csv data/derived/posts_classified.csv
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


# --- Default paths relative to repo root -----------------------------------
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[2]

DEFAULT_POSTS_CSV = REPO_ROOT / "data_sources/parliament/most recent output/post_field_analysis.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "data_sources/parliament/most recent output/posts_classified.csv"
DEFAULT_APPLY_TO = REPO_ROOT / "data_sources/parliament/most recent extract/cabinet_ministers.csv"


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    is_senior: bool
    match_rule: str
    reason: str


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _compile_patterns(patterns: Iterable[str]) -> List[re.Pattern]:
    return [re.compile(p, flags=re.IGNORECASE) for p in patterns]


# --- Core rules -------------------------------------------------------------

# Senior Cabinet positions that are NOT always written as "Secretary of State"
# (We still treat "Foreign Secretary" / "Home Secretary" etc. as senior even if
# dataset uses the shorthand.)
SENIOR_EXACT_OR_CONTAINS: Tuple[Tuple[str, str], ...] = (
    ("prime minister", "Prime Minister is senior Cabinet by definition."),
    ("first lord of the treasury", "PM title variant; treat as senior."),
    ("chancellor of the exchequer", "Chancellor is senior Cabinet."),
    ("lord chancellor", "Lord Chancellor is senior Cabinet."),
    ("chancellor of the duchy of lancaster", "Senior Cabinet post."),
    ("lord president of the council", "Senior Cabinet post."),
    ("lord privy seal", "Senior Cabinet post (historically)."),
    ("minister without portfolio", "Senior Cabinet post."),
    ("chief secretary to the treasury", "Usually Cabinet-level; treat as senior."),
    ("leader of the house of commons", "Senior Cabinet post."),
    ("leader of the house of lords", "Senior Cabinet post."),
    ("secretary of state", "Secretary of State is senior Cabinet by definition."),
    ("first secretary of state", "Senior Cabinet post."),
)

# Titles that are *very likely* non-senior (junior posts / whips)
NON_SENIOR_PATTERNS = _compile_patterns(
    [
        r"\bparliamentary under-?secretary\b",
        r"\bunder-?secretary\b",
        r"\bparliamentary secretary\b",
        r"\bassistant whip\b",
        r"\bwhip\b",
        r"\blord commissioner\b.*\bwhip\b",
        r"\blord in waiting\b",
        r"\bjr\.?\s*lord\b",
        r"\bvice chamberlain\b",
        r"\bassistant\b(?!\s*secretary of state)",
    ]
)

# Titles that are often Cabinet-adjacent but not consistently "senior Cabinet"
# across periods/governments; we mark these ambiguous by default.
AMBIGUOUS_PATTERNS = _compile_patterns(
    [
        r"\bminister of state\b",
        r"\bfinancial secretary\b",
        r"\beconomic secretary\b",
        r"\bpaymaster general\b",
        r"\battorney general\b",
        r"\bsolicitor general\b",
        r"\bminister for\b",
        r"\bchief whip\b",
    ]
)


def load_overrides(path: Optional[Path]) -> Dict[str, Dict[str, str]]:
    """
    Overrides file format (JSON):
    {
      "Some Post Title": {"category": "senior", "reason": "explicit decision"},
      "Other Title": {"category": "non_senior", "reason": "explicit decision"}
    }

    Category must be one of: senior, non_senior, ambiguous
    """
    if path is None:
        return {}

    if not path.exists():
        raise FileNotFoundError(f"Overrides JSON not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Overrides JSON must be an object mapping post -> {category, reason}")

    cleaned: Dict[str, Dict[str, str]] = {}
    for key, val in data.items():
        if not isinstance(key, str) or not isinstance(val, dict):
            continue
        category = str(val.get("category", "")).strip().lower()
        reason = str(val.get("reason", "")).strip()
        if category not in {"senior", "non_senior", "ambiguous"}:
            raise ValueError(f"Invalid override category for '{key}': {category}")
        cleaned[key] = {"category": category, "reason": reason or "override"}
    return cleaned


def classify_post(post: str, overrides: Dict[str, Dict[str, str]]) -> ClassificationResult:
    """
    Classify a single post title.
    """
    raw = post or ""
    if raw in overrides:
        cat = overrides[raw]["category"]
        is_senior = cat == "senior"
        return ClassificationResult(
            category=cat,
            is_senior=is_senior,
            match_rule="override",
            reason=overrides[raw]["reason"],
        )

    p = _norm(raw)

    # 1) Hard senior contains checks
    for needle, why in SENIOR_EXACT_OR_CONTAINS:
        if needle in p:
            return ClassificationResult(
                category="senior",
                is_senior=True,
                match_rule=f"contains:{needle}",
                reason=why,
            )

    # 2) Clear non-senior regex patterns
    for pat in NON_SENIOR_PATTERNS:
        if pat.search(raw):
            return ClassificationResult(
                category="non_senior",
                is_senior=False,
                match_rule=f"regex:{pat.pattern}",
                reason="Matches a junior/whip/non-senior pattern.",
            )

    # 3) Ambiguous patterns (flag for review)
    for pat in AMBIGUOUS_PATTERNS:
        if pat.search(raw):
            return ClassificationResult(
                category="ambiguous",
                is_senior=False,
                match_rule=f"regex:{pat.pattern}",
                reason="Often Cabinet-adjacent but not consistently senior; review/override.",
            )

    # 4) Default: ambiguous (conservative)
    return ClassificationResult(
        category="ambiguous",
        is_senior=False,
        match_rule="default",
        reason="No rule matched; review/override if needed.",
    )


def classify_posts_dataframe(posts_df: pd.DataFrame, overrides: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    if "Post" not in posts_df.columns:
        raise ValueError("Expected a 'Post' column in posts CSV.")

    rows: List[Dict[str, object]] = []
    for _, r in posts_df.iterrows():
        post = str(r["Post"])
        res = classify_post(post, overrides)

        row = dict(r)
        row["category"] = res.category
        row["is_senior"] = res.is_senior
        row["match_rule"] = res.match_rule
        row["reason"] = res.reason
        rows.append(row)

    out = pd.DataFrame(rows)
    # Helpful ordering for quick inspection
    sort_cols = [c for c in ["category", "Count", "First Year Used", "Post"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols, ascending=[True] * len(sort_cols)).reset_index(drop=True)
    return out


def apply_classification_to_dataset(
    df: pd.DataFrame,
    post_col: str,
    overrides: Dict[str, Dict[str, str]],
) -> pd.DataFrame:
    if post_col not in df.columns:
        raise ValueError(f"Column '{post_col}' not found in dataset.")

    def _apply_one(x: object) -> Tuple[str, bool, str]:
        res = classify_post(str(x), overrides)
        return res.category, res.is_senior, res.match_rule

    mapped = df[post_col].apply(_apply_one)
    df_out = df.copy()
    df_out["post_category"] = mapped.apply(lambda t: t[0])
    df_out["post_is_senior"] = mapped.apply(lambda t: t[1])
    df_out["post_match_rule"] = mapped.apply(lambda t: t[2])
    return df_out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Classify ministerial post titles into senior/non-senior.")
    p.add_argument(
        "--posts-csv",
        type=Path,
        default=DEFAULT_POSTS_CSV,
        help=f"CSV containing a 'Post' column (default: {DEFAULT_POSTS_CSV}).",
    )
    p.add_argument(
        "--out-csv",
        type=Path,
        default=DEFAULT_OUT_CSV,
        help=f"Where to write the classified posts CSV (default: {DEFAULT_OUT_CSV}).",
    )
    p.add_argument("--overrides-json", type=Path, default=None, help="Optional JSON overrides file.")
    p.add_argument(
        "--apply-to",
        type=Path,
        default=None,
        help=f"Optional dataset to apply mapping to (default: {DEFAULT_APPLY_TO} if provided).",
    )
    p.add_argument(
        "--apply-post-col",
        type=str,
        default="post",
        help="Column in --apply-to dataset that contains the post title (default: post).",
    )
    p.add_argument(
        "--applied-out",
        type=Path,
        default=None,
        help="Output path for applied dataset CSV (default: alongside --apply-to).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    overrides = load_overrides(args.overrides_json)

    posts_df = pd.read_csv(args.posts_csv)
    classified = classify_posts_dataframe(posts_df, overrides)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    classified.to_csv(args.out_csv, index=False)

    # Quick summary for your terminal logs
    counts = classified["category"].value_counts(dropna=False).to_dict()
    print(f"Wrote classified posts: {args.out_csv}")
    print(f"Category counts: {counts}")

    # Optionally apply to a full dataset
    if args.apply_to is not None or DEFAULT_APPLY_TO.exists():
        apply_target = args.apply_to if args.apply_to is not None else DEFAULT_APPLY_TO

        if not apply_target.exists():
            print(f"Apply target not found, skipping apply step: {apply_target}")
            return

        df = pd.read_csv(apply_target)
        applied = apply_classification_to_dataset(df, args.apply_post_col, overrides)

        if args.applied_out is not None:
            applied_out = args.applied_out
        else:
            applied_out = apply_target.parent / f"{apply_target.stem}_classified.csv"

        applied_out.parent.mkdir(parents=True, exist_ok=True)
        applied.to_csv(applied_out, index=False)
        print(f"Wrote applied dataset: {applied_out}")


if __name__ == "__main__":
    main()
