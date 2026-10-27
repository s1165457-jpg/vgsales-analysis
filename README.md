# vgsales-analysis

Exploratory analysis of 16,000+ video game titles (VGChartz, 1980–2016) — data quality checks, KPI reporting, regional genre preferences, and platform lifecycle analysis.

**Interactive dashboard (Tableau Public):** `<ADD_TABLEAU_PUBLIC_LINK_HERE>`

---

## Dataset

|         |                                                                                                                             |
| ------- | --------------------------------------------------------------------------------------------------------------------------- |
| Source  | VGChartz via [Kaggle — Video Game Sales](https://www.kaggle.com/datasets/gregorut/videogamesales)                           |
| Rows    | 16,598 titles                                                                                                               |
| Columns | `Rank`, `Name`, `Platform`, `Year`, `Genre`, `Publisher`, `NA_Sales`, `EU_Sales`, `JP_Sales`, `Other_Sales`, `Global_Sales` |
| Unit    | Millions of copies sold                                                                                                     |

## Questions

1. How clean is the dataset, and which records should be excluded before analysis?
2. How did global sales evolve between 1980 and 2016, and when was the peak?
3. Which publishers dominate the market, and how concentrated is it?
4. Do regional audiences prefer different genres?
5. Which platforms had the longest and most valuable lifecycles?

## Key findings

**Market size.** After cleaning, 16,323 titles remain, totalling **8,820.0 M copies** across 31 platforms, 576 publishers and 12 genres.

**Peak year = 2008.** Global sales reached **678.9 M copies** in 2008, driven by the Wii / DS / PS3 generation, before declining steadily to 70.9 M in 2016 (a partial year in this dataset).

**Publisher concentration.** Nintendo alone accounts for **20.2%** of all copies sold (1,784.4 M), followed by Electronic Arts (12.4%) and Activision (8.2%). The top 10 publishers cover roughly **70%** of the market.

**Regional genre preferences differ sharply.**

| Genre        |    NA |    EU |    JP |  JP share |
| ------------ | ----: | ----: | ----: | --------: |
| Action       | 861.8 | 516.5 | 158.6 |      9.2% |
| Shooter      | 575.2 | 310.4 |  38.2 |  **3.7%** |
| Role-Playing | 326.5 | 187.6 | 350.2 | **37.9%** |

Japan over-indexes heavily on Role-Playing (37.9% of that genre's sales vs 35.3% in North America) and almost ignores Shooters — a useful signal for region-specific release and marketing decisions.

**Platform lifecycle.** PS2 is the highest-selling platform at **1,233.5 M copies across 2,127 titles (2000–2011)**, followed by Xbox 360 (969.6 M) and PS3 (949.4 M). Platform lifecycles cluster at **10–12 years**, with the exception of PC (32 years, long tail).

**Regional split.** North America 49.2%, Europe 27.3%, Japan 14.6%, Rest of World 9.0%.

## Repository structure

```
vgsales-analysis/
├── vgsales.csv                  # raw dataset
├── clean_and_explore.py         # data quality checks + analysis + export
├── queries.sql                  # equivalent SQL for each analysis step
├── requirements.txt
├── outputs/                     # generated tables (ready for BI tools)
│   ├── 01_yearly_sales.csv
│   ├── 02_top_publishers.csv
│   ├── 03_genre_region.csv
│   ├── 04_platform_lifecycle.csv
│   ├── 05_region_share.csv
│   └── vgsales_long.csv         # tidy format: one row per game × region
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python clean_and_explore.py
```

The script prints every check and summary table to the console and writes the cleaned aggregates to `outputs/`.

## Data quality notes

- **271 rows** have a missing `Year` and **58 rows** a missing `Publisher`; rows without a year are excluded from time-series analysis.
- The raw file contains years up to **2020** (out of the VGChartz coverage window) and a small number of pre-1980 records; the analysis window is restricted to **1980–2016**.
- **5,105 duplicate game names** are expected — the same title appears once per platform (e.g. *FIFA* on PS2, PS3, Xbox 360).
- `Global_Sales` does not always equal the sum of the four regional columns exactly, due to rounding in the source.
- Known anomaly: the DS platform shows a first sale year of 1985, before the hardware launched — a source labelling error retained for transparency rather than silently corrected.

## Tools

Python (pandas), SQL, Tableau Public.
