import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import glob

# --------------------------------------------------
# Configuration
# --------------------------------------------------

START_YEAR = 1958

# Find the most recent extract directory and load lords_by_year.csv from there
PARLIAMENT_DIR = Path(__file__).parent.parent / "data_sources" / "parliament"
extract_dirs = sorted(
    [p for p in PARLIAMENT_DIR.glob("extract_*") if p.is_dir()],
    key=lambda p: p.stat().st_mtime,
    reverse=True
)
CSV_PATH = extract_dirs[0] / "lords_by_year.csv" if extract_dirs else PARLIAMENT_DIR / "lords_by_year.csv"

# Output to generated_charts directory
CHARTS_DIR = Path(__file__).parent.parent / "generated_charts"
CHARTS_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_FILE = CHARTS_DIR / "lords_membership_by_type_1958_present.png"

KEY_DATES = {
    1958: "Life Peerages Act",
    1983: "Data coverage\nstabilises",
    1999: "House of Lords Act",
    2009: "Supreme Court\n(Law Lords exit)",
    2014: "Lords Reform Act\n(retirement)",
}

# --------------------------------------------------
# Load data
# --------------------------------------------------

df = pd.read_csv(CSV_PATH)
df["year"] = df["year"].astype(int)

# Filter to analysis window
df = df[df["year"] >= START_YEAR].copy()

# --------------------------------------------------
# Construct series
# --------------------------------------------------

df["Hereditary (all recorded)"] = (
    df["Hereditary"].fillna(0)
    + df["Excepted Hereditary"].fillna(0)
    + df["Hereditary of 1st creation"].fillna(0)
)

series_map = {
    "Life Peers": df["Life Peer"],
    "Life Peers (Judicial)": df["Life Peer (judicial)"],
    "Hereditary Peers (all)": df["Hereditary (all recorded)"],
    "Bishops": df["Bishops"],
}

# --------------------------------------------------
# Plot
# --------------------------------------------------

plt.figure(figsize=(13, 7))

for label, series in series_map.items():
    plt.plot(
        df["year"],
        series,
        label=label,
        linewidth=2
    )

# Vertical reform markers
y_max = max(df["total"]) * 1.05

for year, label in KEY_DATES.items():
    if df["year"].min() <= year <= df["year"].max():
        plt.axvline(year, linestyle="--", linewidth=1)
        plt.text(
            year + 0.2,
            y_max,
            label,
            rotation=90,
            va="top",
            fontsize=9
        )

# --------------------------------------------------
# Styling
# --------------------------------------------------

plt.title(
    "Recorded House of Lords Membership by Peer Type (1958–Present)",
    fontsize=14
)
plt.xlabel("Year")
plt.ylabel("Number of Peers (recorded)")

plt.legend(title="Peer type", frameon=False)
plt.grid(True, linestyle=":", alpha=0.6)

plt.ylim(bottom=0, top=y_max)
plt.tight_layout()

# --------------------------------------------------
# Output
# --------------------------------------------------

plt.savefig(OUTPUT_FILE, dpi=300)
plt.show()

print(f"✓ Chart saved to {OUTPUT_FILE}")