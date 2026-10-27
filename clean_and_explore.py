"""
vgsales-analysis
================
End-to-end data quality check + exploratory analysis on the VGChartz
video game sales dataset (16,598 titles, 1980-2016).

Run:
    python clean_and_explore.py

Outputs (printed to console and written to ./outputs/):
    01_yearly_sales.csv        - global sales by year
    02_top_publishers.csv      - top 10 publishers by global sales
    03_genre_region.csv        - genre x region sales matrix (wide)
    04_platform_lifecycle.csv  - sales and active span per platform
    05_region_share.csv        - global regional split
    vgsales_long.csv           - tidy long format (one row per game x region)
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / "vgsales.csv"
OUT_DIR = BASE_DIR / "outputs"

REGION_COLS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
REGION_LABELS = {
    "NA_Sales": "North America",
    "EU_Sales": "Europe",
    "JP_Sales": "Japan",
    "Other_Sales": "Rest of World",
}
YEAR_MIN, YEAR_MAX = 1980, 2016
TOP_N = 10


# ---------------------------------------------------------------------------
# 1. Load + data quality check
# ---------------------------------------------------------------------------
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print("=" * 70)
    print("1. DATA QUALITY CHECK")
    print("=" * 70)
    print(f"Rows loaded            : {len(df):,}")
    print(f"Columns                : {list(df.columns)}")
    print(f"Duplicate Rank values  : {df['Rank'].duplicated().sum()}")
    print(f"Duplicate game names   : {df['Name'].duplicated().sum()}")
    print(f"Year range (raw)       : {df['Year'].min():.0f} - {df['Year'].max():.0f}")
    print(f"Rows with missing Year : {df['Year'].isna().sum()}")
    print(f"Rows with missing Pub. : {df['Publisher'].isna().sum()}")
    print("\nMissing values per column:")
    print(df.isna().sum().to_string())
    return df


# ---------------------------------------------------------------------------
# 2. Clean
# ---------------------------------------------------------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.copy()

    # Year is stored as float because of the missing values -> keep the
    # analysis window explicit instead of silently dropping everything.
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)

    # A handful of records sit outside the VGChartz coverage window; they are
    # kept in the raw file but excluded from time-series analysis.
    df = df[df["Year"].between(YEAR_MIN, YEAR_MAX)]

    # Defensive: sales figures should never be negative.
    for col in REGION_COLS + ["Global_Sales"]:
        df = df[df[col] >= 0]

    print("\n" + "=" * 70)
    print("2. CLEANING")
    print("=" * 70)
    print(f"Rows dropped           : {before - len(df):,} (missing year / out of range / negative sales)")
    print(f"Rows kept              : {len(df):,}")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. Analysis
# ---------------------------------------------------------------------------
def kpis(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("3. HEADLINE KPIs")
    print("=" * 70)
    print(f"Total global sales     : {df['Global_Sales'].sum():,.1f} M copies")
    print(f"Titles                 : {len(df):,}")
    print(f"Distinct platforms     : {df['Platform'].nunique()}")
    print(f"Distinct publishers    : {df['Publisher'].nunique()}")
    print(f"Distinct genres        : {df['Genre'].nunique()}")


def yearly_sales(df: pd.DataFrame) -> pd.DataFrame:
    yearly = (
        df.groupby("Year", as_index=False)["Global_Sales"]
        .sum()
        .rename(columns={"Global_Sales": "Global_Sales_M"})
        .sort_values("Year")
    )
    peak = yearly.loc[yearly["Global_Sales_M"].idxmax()]
    print("\n" + "=" * 70)
    print("4. YEARLY TREND")
    print("=" * 70)
    print(f"Peak year              : {int(peak['Year'])} ({peak['Global_Sales_M']:.1f} M copies)")
    print(yearly.tail(10).to_string(index=False))
    return yearly


def top_publishers(df: pd.DataFrame) -> pd.DataFrame:
    pub = (
        df.groupby("Publisher", as_index=False)["Global_Sales"]
        .sum()
        .rename(columns={"Global_Sales": "Global_Sales_M"})
        .sort_values("Global_Sales_M", ascending=False)
        .head(TOP_N)
    )
    pub["Share_of_total_%"] = (pub["Global_Sales_M"] / df["Global_Sales"].sum() * 100).round(1)
    print("\n" + "=" * 70)
    print(f"5. TOP {TOP_N} PUBLISHERS")
    print("=" * 70)
    print(pub.to_string(index=False))
    return pub


def genre_region(df: pd.DataFrame) -> pd.DataFrame:
    genre = df.groupby("Genre", as_index=False)[REGION_COLS].sum()
    genre["Global_Sales"] = genre[REGION_COLS].sum(axis=1)
    genre = genre.sort_values("Global_Sales", ascending=False).drop(columns="Global_Sales")
    for col in REGION_COLS:
        genre[col] = genre[col].round(1)

    print("\n" + "=" * 70)
    print("6. GENRE x REGION (M copies)")
    print("=" * 70)
    print(genre.to_string(index=False))

    print("\nRegional share per genre (%):")
    share = genre.copy()
    totals = share[REGION_COLS].sum(axis=1)
    for col in REGION_COLS:
        share[col] = (share[col] / totals * 100).round(1)
    print(share.to_string(index=False))
    return genre


def platform_lifecycle(df: pd.DataFrame) -> pd.DataFrame:
    life = (
        df.groupby("Platform")
        .agg(
            Global_Sales_M=("Global_Sales", "sum"),
            Titles=("Name", "count"),
            First_Year=("Year", "min"),
            Last_Year=("Year", "max"),
        )
        .reset_index()
    )
    life["Active_Years"] = life["Last_Year"] - life["First_Year"] + 1
    life = life.sort_values("Global_Sales_M", ascending=False).head(15)
    life["Global_Sales_M"] = life["Global_Sales_M"].round(1)

    print("\n" + "=" * 70)
    print("7. PLATFORM LIFECYCLE (top 15)")
    print("=" * 70)
    print(life.to_string(index=False))
    return life


def region_share(df: pd.DataFrame) -> pd.DataFrame:
    totals = df[REGION_COLS].sum()
    share = pd.DataFrame(
        {
            "Region": [REGION_LABELS[c] for c in REGION_COLS],
            "Sales_M": totals.values.round(1),
            "Share_%": (totals.values / totals.sum() * 100).round(1),
        }
    )
    print("\n" + "=" * 70)
    print("8. GLOBAL REGIONAL SPLIT")
    print("=" * 70)
    print(share.to_string(index=False))
    return share


def to_long_format(df: pd.DataFrame) -> pd.DataFrame:
    """Tidy format: one row per game x region — the shape Tableau needs for a
    stacked bar chart (equivalent to a pivot in Tableau Desktop)."""
    long_df = df.melt(
        id_vars=["Rank", "Name", "Platform", "Year", "Genre", "Publisher"],
        value_vars=REGION_COLS,
        var_name="Region",
        value_name="Sales",
    )
    long_df["Region"] = long_df["Region"].map(REGION_LABELS)
    return long_df


# ---------------------------------------------------------------------------
# 4. Export
# ---------------------------------------------------------------------------
def export(df: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    if not OUT_DIR.exists():
        OUT_DIR.mkdir(parents=True)
    for filename, table in tables.items():
        table.to_csv(OUT_DIR / filename, index=False, encoding="utf-8-sig")

    long_df = to_long_format(df)
    long_df.to_csv(OUT_DIR / "vgsales_long.csv", index=False, encoding="utf-8-sig")

    print("\n" + "=" * 70)
    print("9. EXPORTED FILES")
    print("=" * 70)
    for path in sorted(OUT_DIR.glob("*.csv")):
        print(f"{path.name:<28} {path.stat().st_size / 1024:>8.1f} KB")
    print(f"\nLong format rows       : {len(long_df):,} (games x 4 regions)")


def main() -> None:
    raw = load_data(RAW_PATH)
    df = clean_data(raw)

    kpis(df)
    yearly = yearly_sales(df)
    publishers = top_publishers(df)
    genre = genre_region(df)
    lifecycle = platform_lifecycle(df)
    regions = region_share(df)

    export(
        df,
        {
            "01_yearly_sales.csv": yearly,
            "02_top_publishers.csv": publishers,
            "03_genre_region.csv": genre,
            "04_platform_lifecycle.csv": lifecycle,
            "05_region_share.csv": regions,
        },
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
