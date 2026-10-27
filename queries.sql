-- ============================================================================
-- vgsales-analysis / queries.sql
-- SQL equivalents of every step performed in clean_and_explore.py
-- Dialect: standard ANSI SQL (tested mentally on PostgreSQL / MySQL 8+).
-- Assumes a table `vgsales` loaded from vgsales.csv with columns:
--   rank, name, platform, year, genre, publisher,
--   na_sales, eu_sales, jp_sales, other_sales, global_sales
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. DATA QUALITY
-- ----------------------------------------------------------------------------
-- Row count and coverage
SELECT
    COUNT(*)                                   AS total_rows,
    COUNT(DISTINCT platform)                   AS platforms,
    COUNT(DISTINCT publisher)                  AS publishers,
    COUNT(DISTINCT genre)                      AS genres,
    MIN(year)                                  AS min_year,
    MAX(year)                                  AS max_year
FROM vgsales;

-- Missing values that would distort a time-series analysis
SELECT
    SUM(CASE WHEN year      IS NULL THEN 1 ELSE 0 END) AS missing_year,
    SUM(CASE WHEN publisher IS NULL THEN 1 ELSE 0 END) AS missing_publisher,
    SUM(CASE WHEN global_sales < 0 THEN 1 ELSE 0 END)  AS negative_sales
FROM vgsales;


-- ----------------------------------------------------------------------------
-- 2. HEADLINE KPIs (cleaned window: 1980-2016, year present)
-- ----------------------------------------------------------------------------
SELECT
    ROUND(SUM(global_sales), 1) AS total_global_sales_m,
    COUNT(*)                    AS titles,
    COUNT(DISTINCT platform)    AS platforms,
    COUNT(DISTINCT publisher)   AS publishers
FROM vgsales
WHERE year BETWEEN 1980 AND 2016;


-- ----------------------------------------------------------------------------
-- 3. YEARLY TREND + PEAK YEAR
-- ----------------------------------------------------------------------------
SELECT
    year,
    ROUND(SUM(global_sales), 2) AS global_sales_m
FROM vgsales
WHERE year BETWEEN 1980 AND 2016
GROUP BY year
ORDER BY year;

-- Peak year only
SELECT
    year,
    ROUND(SUM(global_sales), 2) AS global_sales_m
FROM vgsales
WHERE year BETWEEN 1980 AND 2016
GROUP BY year
ORDER BY global_sales_m DESC
LIMIT 1;


-- ----------------------------------------------------------------------------
-- 4. TOP 10 PUBLISHERS + MARKET SHARE
--    Uses a window function to compute share without a self-join.
-- ----------------------------------------------------------------------------
WITH publisher_sales AS (
    SELECT
        publisher,
        SUM(global_sales) AS sales_m
    FROM vgsales
    WHERE year BETWEEN 1980 AND 2016
    GROUP BY publisher
)
SELECT
    publisher,
    ROUND(sales_m, 2)                                            AS global_sales_m,
    ROUND(100.0 * sales_m / SUM(sales_m) OVER (), 1)             AS share_of_total_pct,
    RANK() OVER (ORDER BY sales_m DESC)                          AS sales_rank
FROM publisher_sales
ORDER BY sales_m DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- 5. GENRE x REGION MATRIX
-- ----------------------------------------------------------------------------
SELECT
    genre,
    ROUND(SUM(na_sales),    1) AS na_sales,
    ROUND(SUM(eu_sales),    1) AS eu_sales,
    ROUND(SUM(jp_sales),    1) AS jp_sales,
    ROUND(SUM(other_sales), 1) AS other_sales,
    ROUND(SUM(na_sales + eu_sales + jp_sales + other_sales), 1) AS total_sales
FROM vgsales
WHERE year BETWEEN 1980 AND 2016
GROUP BY genre
ORDER BY total_sales DESC;


-- ----------------------------------------------------------------------------
-- 6. REGIONAL SHARE PER GENRE (%)
--    Answers: which genres over-index in Japan vs North America?
-- ----------------------------------------------------------------------------
WITH genre_region AS (
    SELECT
        genre,
        SUM(na_sales)    AS na,
        SUM(eu_sales)    AS eu,
        SUM(jp_sales)    AS jp,
        SUM(other_sales) AS other
    FROM vgsales
    WHERE year BETWEEN 1980 AND 2016
    GROUP BY genre
)
SELECT
    genre,
    ROUND(100.0 * na / (na + eu + jp + other), 1) AS na_pct,
    ROUND(100.0 * eu / (na + eu + jp + other), 1) AS eu_pct,
    ROUND(100.0 * jp / (na + eu + jp + other), 1) AS jp_pct,
    ROUND(100.0 * other / (na + eu + jp + other), 1) AS other_pct
FROM genre_region
ORDER BY jp_pct DESC;


-- ----------------------------------------------------------------------------
-- 7. PLATFORM LIFECYCLE
--    Sales, title count, first/last year and active span per platform.
-- ----------------------------------------------------------------------------
SELECT
    platform,
    ROUND(SUM(global_sales), 1)          AS global_sales_m,
    COUNT(*)                             AS titles,
    MIN(year)                            AS first_year,
    MAX(year)                            AS last_year,
    MAX(year) - MIN(year) + 1            AS active_years
FROM vgsales
WHERE year BETWEEN 1980 AND 2016
GROUP BY platform
ORDER BY global_sales_m DESC
LIMIT 15;


-- ----------------------------------------------------------------------------
-- 8. TOP TITLE PER PLATFORM
--    Correlated subquery pattern - useful for "best-seller by dimension".
-- ----------------------------------------------------------------------------
SELECT
    v.platform,
    v.name,
    v.year,
    v.global_sales
FROM vgsales v
WHERE v.year BETWEEN 1980 AND 2016
  AND v.global_sales = (
        SELECT MAX(v2.global_sales)
        FROM vgsales v2
        WHERE v2.platform = v.platform
          AND v2.year BETWEEN 1980 AND 2016
  )
ORDER BY v.platform;


-- ----------------------------------------------------------------------------
-- 9. LONG FORMAT (pivot equivalent, for BI tools)
--    Mirrors outputs/vgsales_long.csv used by the Tableau dashboard.
-- ----------------------------------------------------------------------------
SELECT rank, name, platform, year, genre, publisher, 'North America' AS region, na_sales    AS sales FROM vgsales
UNION ALL
SELECT rank, name, platform, year, genre, publisher, 'Europe'        AS region, eu_sales    AS sales FROM vgsales
UNION ALL
SELECT rank, name, platform, year, genre, publisher, 'Japan'         AS region, jp_sales    AS sales FROM vgsales
UNION ALL
SELECT rank, name, platform, year, genre, publisher, 'Rest of World' AS region, other_sales AS sales FROM vgsales;


-- ----------------------------------------------------------------------------
-- 10. RUNNING TOTAL OF GLOBAL SALES BY YEAR
--     Window-function example: cumulative market size over time.
-- ----------------------------------------------------------------------------
SELECT
    year,
    ROUND(SUM(global_sales), 2) AS yearly_sales_m,
    ROUND(SUM(SUM(global_sales)) OVER (ORDER BY year), 2) AS cumulative_sales_m
FROM vgsales
WHERE year BETWEEN 1980 AND 2016
GROUP BY year
ORDER BY year;
