"""
Analyze the 'post' field from cabinet_ministers.csv and generate a summary
showing each unique post, count of occurrences, first year used, and last year used.

Outputs:
- data_sources/parliament/most recent output/post_field_analysis.csv
"""

from pathlib import Path
import pandas as pd


# Find the most recent cabinet ministers extract
EXTRACT_BASE_DIR = Path("data_sources/parliament/most recent extract")
if EXTRACT_BASE_DIR.exists():
    INPUT_CSV = EXTRACT_BASE_DIR / "cabinet_ministers.csv"
else:
    INPUT_CSV = Path("data_sources/parliament/extract_20260115_125959/cabinet_ministers.csv")

OUTPUT_DIR = Path("data_sources/parliament/most recent output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def analyze_posts() -> None:
    """Analyze the post field and generate summary statistics."""
    
    print(f"Loading cabinet ministers from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    # Convert start_date to datetime
    df["start_date"] = pd.to_datetime(df["start_date"])
    
    # Extract year from start_date
    df["year"] = df["start_date"].dt.year
    
    # Group by post field
    post_analysis = df.groupby("post").agg(
        count=("post", "size"),
        first_year=("year", "min"),
        last_year=("year", "max")
    ).reset_index()
    
    # Sort by count descending, then by first_year
    post_analysis = post_analysis.sort_values(["count", "first_year"], ascending=[False, True]).reset_index(drop=True)
    
    # Rename columns for clarity
    post_analysis.columns = ["Post", "Count", "First Year Used", "Last Year Used"]
    
    # Save to CSV
    output_path = OUTPUT_DIR / "post_field_analysis.csv"
    post_analysis.to_csv(output_path, index=False)
    
    print(f"\nAnalysis complete!")
    print(f"Total unique posts: {len(post_analysis)}")
    print(f"\nTop 30 most common posts:")
    print(post_analysis.head(30).to_string(index=False))
    
    print(f"\nBottom 20 least common posts:")
    print(post_analysis.tail(20).to_string(index=False))
    
    print(f"\nFull results saved to: {output_path}")


if __name__ == "__main__":
    analyze_posts()
