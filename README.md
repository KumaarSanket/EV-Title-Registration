# EV-Title-Registration

# 🔋 EV Title & Registration Activity Dashboard

![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Records](https://img.shields.io/badge/Records-1.77M-00C896?style=for-the-badge)
![Size](https://img.shields.io/badge/File%20Size-930MB-EF4444?style=for-the-badge)

> Data Analytics · K.S. · Tools: MySQL → Power BI
![EV Title & Registration Dashboard](EV%20Title%20%26%20Registration%20Dashboard.jpeg)
> **Note: Excel was NOT used — 930MB file required Python EDA + direct MySQL import**

![EV Title & Registration Dashboard 2](EV%20Title%20%26%20Registration%20Dashboard%20%282%29.jpeg)
![EV Title & Registration Dashboard 3](EV%20Title%20%26%20Registration%20Dashboard%20%283%29.jpeg)
![EV Title & Registration Dashboard 4](EV%20Title%20%26%20Registration%20Dashboard%20%284%29.jpeg)

---

## 📌 Project Overview

Conducted Python-based EDA on a 930MB, 1,772,617-row Washington State EV registration file — identifying 10 data quality issues including currency text, date strings, boolean text, latin-1 encoding, and float postal codes. • Imported all records into MySQL via LOAD DATA INFILE with inline @variable transformations resolving every issue in a single command. • Created 10 performance indexes and executed 7 SQL queries surfacing Tesla's 40.90% market dominance, King County's 55.50% geographic concentration, and 2023 as peak adoption year. • Built a 3-page Power BI dashboard (23 visuals) revealing 79.61% BEV dominance and only 4.99% CAFV tax compliance.

---

## 🎯 Problem Statement

Washington State's EV Title and Registration data spanning 2010–2026 existed as a 930MB raw CSV with 1.77M transaction records and multiple data quality issues — too large for Excel and requiring careful MySQL engineering to import, clean, and analyze without a pre-existing reporting layer for adoption trends, market share, or compliance status.

---

## 🎯 Objectives

- Perform Python EDA on a 930MB file to determine optimal processing path
- Import 1.77M records into MySQL with inline transformations — no Excel
- Create performance indexes and execute 7 analytical queries + 1 VIEW
- Build a 3-page Power BI dashboard with 8 DAX measures and 23 visuals
- Surface adoption trends, market share, geographic distribution, and compliance insights

---

## 📁 Dataset

| Attribute | Detail |
|-----------|--------|
| **Name** | Electric Vehicle Title and Registration Activity |
| **Source** | [Washington State Government — data.wa.gov](https://data.wa.gov) |
| **Format** | CSV (.csv) — 930 MB |
| **Records** | 1,772,617 rows · 33 columns |
| **Encoding** | latin-1 (not ASCII) |
| **Unique Vehicles** | 377,329 (DOL Vehicle ID) |
| **Excel Used** | **NO** — file too large; EDA confirmed direct MySQL import |

### Python EDA — 10 Issues Found & Resolved at Import

| # | Issue | Resolution |
|---|-------|-----------|
| 1 | Sale Price as `"$74,100"` text | `REPLACE($,'')+REPLACE(,,'')` → DECIMAL |
| 2 | Sale Date as `"May 06, 2013"` text | `STR_TO_DATE(@raw,'%M %d, %Y')` |
| 3 | Transaction Date as `"July 28, 2025"` text | `STR_TO_DATE(@raw,'%M %d, %Y')` |
| 4 | 3 boolean columns as `True`/`False` | `IF(@raw='True',1,0)` |
| 5 | Postal Code as float `98052.0` | `LPAD(SUBSTRING_INDEX(@raw,'.',1),5,'0')` |
| 6 | latin-1 encoding | `CHARACTER SET latin1` |
| 7 | MySQL strict mode rejecting dates | `SET SESSION sql_mode=''` |
| 8 | Connection timeout (Error 2013) | Increased timeout to 60,000 sec |
| 9 | $0 Sale Price (77.2%) | **Kept** — valid for renewals |
| 10 | Electric Range = 0 (45.3%) | **Kept** — valid for some PHEVs |

> **62 exact duplicates found** — deliberately NOT removed. Self-join DELETE ran 6,316 seconds without completing (1.77M × 1.77M comparison complexity). 0.0035% of data = zero dashboard impact. Engineering judgement: skip rather than burn hours for negligible gain.

---

## 🛠️ Tools & Technologies

| Tool | Phase | Purpose |
|------|-------|---------|
| **Python** | Pre-import | 30-check EDA script — nulls, dtypes, encoding, duplicates |
| **MySQL 8.0** | Phase 1 | LOAD DATA INFILE, 10 indexes, 7 queries, 1 VIEW |
| **MySQL Workbench** | Phase 1 | Schema, timeout config, query execution |
| **Power BI Desktop** | Phase 2 | Live MySQL connection, DAX, 3-page dashboard |
| **DAX** | Phase 2 | 8 measures using DISTINCTCOUNT for transaction-log data |

---

## ⚙️ PHASE 1 — MySQL

### Table Schema

```sql
CREATE DATABASE IF NOT EXISTS ev_project;
USE ev_project;

CREATE TABLE ev_registration (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    cafv_type               VARCHAR(60),
    vin_10                  VARCHAR(10),
    dol_vehicle_id          BIGINT,
    model_year              SMALLINT,
    make                    VARCHAR(50),
    model                   VARCHAR(50),
    primary_use             VARCHAR(50),
    electric_range          SMALLINT,
    odometer_reading        INT,
    odometer_description    VARCHAR(60),
    new_or_used             VARCHAR(5),
    sale_price              DECIMAL(12,2),
    sale_date               DATE,
    transaction_type        VARCHAR(50),
    transaction_date        DATE,
    txn_year                SMALLINT,
    county                  VARCHAR(50),
    city                    VARCHAR(50),
    state                   CHAR(2),
    postal_code             CHAR(5),
    cafv_eligibility        VARCHAR(50),
    meets_range_req         TINYINT(1),
    meets_sale_date_req     TINYINT(1),
    meets_sale_price_req    TINYINT(1),
    battery_range_req       VARCHAR(50),
    purchase_date_req       VARCHAR(80),
    sale_price_req          VARCHAR(80),
    ev_fee_paid             VARCHAR(20),
    transport_fee_paid      VARCHAR(20),
    hybrid_fee_paid         VARCHAR(20),
    geoid_2020              VARCHAR(15),
    legislative_district    VARCHAR(5),
    electric_utility        VARCHAR(150)
);
```

### LOAD DATA INFILE — Single Command, 14 Transformations

```sql
SET SESSION sql_mode = '';

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Electric_Vehicle_Title_and_Registration_Activity_20260623.csv'
INTO TABLE ev_registration
CHARACTER SET latin1
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(cafv_type, vin_10, dol_vehicle_id, model_year, make, model,
 primary_use, @elec_range, odometer_reading, odometer_description,
 new_or_used, @sale_price_raw, @sale_date_raw, transaction_type,
 @txn_date_raw, txn_year, @county_raw, city, @state_raw, @postal_raw,
 cafv_eligibility, @meets_range, @meets_sale_date, @meets_sale_price,
 battery_range_req, purchase_date_req, sale_price_req, ev_fee_paid,
 @transport_raw, @hybrid_raw, @geoid_raw, @leg_dist_raw, electric_utility)
SET
    electric_range       = NULLIF(@elec_range, ''),
    sale_price           = CAST(REPLACE(REPLACE(TRIM(@sale_price_raw),'$',''),',','') AS DECIMAL(12,2)),
    sale_date            = IF(TRIM(@sale_date_raw)='', NULL, STR_TO_DATE(TRIM(@sale_date_raw),'%M %d, %Y')),
    transaction_date     = STR_TO_DATE(TRIM(@txn_date_raw),'%M %d, %Y'),
    county               = NULLIF(TRIM(@county_raw), ''),
    state                = NULLIF(TRIM(@state_raw), ''),
    postal_code          = NULLIF(LPAD(TRIM(SUBSTRING_INDEX(TRIM(@postal_raw),'.','1')),5,'0'),'00000'),
    meets_range_req      = IF(TRIM(@meets_range)='True',1,0),
    meets_sale_date_req  = IF(TRIM(@meets_sale_date)='True',1,0),
    meets_sale_price_req = IF(TRIM(@meets_sale_price)='True',1,0),
    transport_fee_paid   = NULLIF(TRIM(@transport_raw), ''),
    hybrid_fee_paid      = NULLIF(TRIM(@hybrid_raw), ''),
    geoid_2020           = NULLIF(TRIM(SUBSTRING_INDEX(TRIM(@geoid_raw),'.','1')),''),
    legislative_district = NULLIF(TRIM(SUBSTRING_INDEX(TRIM(@leg_dist_raw),'.','1')),'');

-- Result: 1,772,617 rows in 135 seconds (after timeout fix)
```

### 10 Performance Indexes

```sql
CREATE INDEX idx_make      ON ev_registration(make);
CREATE INDEX idx_model     ON ev_registration(model);
CREATE INDEX idx_year      ON ev_registration(model_year);
CREATE INDEX idx_txn_year  ON ev_registration(txn_year);
CREATE INDEX idx_county    ON ev_registration(county);
CREATE INDEX idx_city      ON ev_registration(city);
CREATE INDEX idx_txn_type  ON ev_registration(transaction_type);
CREATE INDEX idx_txn_date  ON ev_registration(transaction_date);
CREATE INDEX idx_cafv_type ON ev_registration(cafv_type);
CREATE INDEX idx_dol       ON ev_registration(dol_vehicle_id);
```

### 7 Analytical Queries

```sql
-- Q1: Overall KPIs
SELECT COUNT(*) total_transactions, COUNT(DISTINCT dol_vehicle_id) unique_vehicles,
       COUNT(DISTINCT make) unique_makes, COUNT(DISTINCT model) unique_models,
       COUNT(DISTINCT county) counties_covered, MIN(txn_year) earliest_year, MAX(txn_year) latest_year,
       SUM(CASE WHEN cafv_type LIKE '%Battery%' THEN 1 ELSE 0 END) bev_txns,
       SUM(CASE WHEN cafv_type LIKE '%Plug%' THEN 1 ELSE 0 END) phev_txns
FROM ev_registration;
-- 1,772,617 · 377,329 · 50 makes · 202 models · 477 counties · 2010-2026

-- Q2: Transaction Type Breakdown
SELECT transaction_type, COUNT(*) total_txns,
       ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM ev_registration),2) pct_share
FROM ev_registration GROUP BY transaction_type ORDER BY total_txns DESC;
-- Renewal 854,334 (48.20%) · Orig Reg 375,417 (21.18%) · Orig Title 367,346 (20.72%)

-- Q3: Top 10 Makes
SELECT make, COUNT(DISTINCT dol_vehicle_id) unique_vehicles,
       ROUND(COUNT(DISTINCT dol_vehicle_id)*100.0/(SELECT COUNT(DISTINCT dol_vehicle_id) FROM ev_registration),2) market_share_pct,
       ROUND(AVG(NULLIF(electric_range,0)),1) avg_range
FROM ev_registration GROUP BY make ORDER BY unique_vehicles DESC LIMIT 10;
-- Tesla 154,341 (40.90%, 236mi) · Nissan 27,620 (7.32%) · Chevrolet 26,890 (7.13%)

-- Q4: Adoption Trend by Model Year
SELECT model_year, COUNT(DISTINCT dol_vehicle_id) unique_vehicles,
       SUM(CASE WHEN cafv_type LIKE '%Battery%' THEN 1 ELSE 0 END) bev_count,
       SUM(CASE WHEN cafv_type LIKE '%Plug%' THEN 1 ELSE 0 END) phev_count
FROM ev_registration GROUP BY model_year ORDER BY model_year;
-- 2010: 57 → 2023 peak: 75,105 → 2026 (partial): 26,799

-- Q5: Top 10 Counties
SELECT county, COUNT(DISTINCT dol_vehicle_id) unique_vehicles,
       ROUND(COUNT(DISTINCT dol_vehicle_id)*100.0/(SELECT COUNT(DISTINCT dol_vehicle_id) FROM ev_registration),2) pct_share
FROM ev_registration WHERE county IS NOT NULL GROUP BY county ORDER BY unique_vehicles DESC LIMIT 10;
-- King 209,431 (55.50%) · Snohomish 55,251 (14.64%) · Pierce 39,640 (10.51%)

-- Q6: Top 10 Models
SELECT make, model, cafv_type, COUNT(DISTINCT dol_vehicle_id) unique_vehicles,
       ROUND(AVG(NULLIF(electric_range,0)),1) avg_range,
       ROUND(AVG(CASE WHEN sale_price>0 THEN sale_price END),0) avg_sale_price
FROM ev_registration GROUP BY make,model,cafv_type ORDER BY unique_vehicles DESC LIMIT 10;
-- Model Y 75,131 ($52,058, 291mi) · Model 3 53,652 ($44,084, 236mi) · Leaf 24,514 ($19,843, 95mi)

-- Q7: CAFV Eligibility
SELECT cafv_eligibility, COUNT(*) total,
       ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM ev_registration),2) pct,
       ROUND(AVG(electric_range),1) avg_range
FROM ev_registration GROUP BY cafv_eligibility ORDER BY total DESC;
-- Not Met: 1,684,152 (95.01%) · Eligible: 88,465 (4.99%)

-- VIEW: vw_ev_summary (pre-aggregated for Power BI)
CREATE OR REPLACE VIEW vw_ev_summary AS
SELECT cafv_type, make, model, model_year, transaction_type, txn_year, county, city,
    CASE WHEN electric_range IS NULL OR electric_range=0 THEN '00-Unknown'
         WHEN electric_range<50 THEN '01-Under 50mi'
         WHEN electric_range<100 THEN '02-50 to 99mi'
         WHEN electric_range<200 THEN '03-100 to 199mi'
         WHEN electric_range<300 THEN '04-200 to 299mi'
         ELSE '05-300mi+' END AS range_bucket,
    new_or_used, cafv_eligibility, COUNT(*) txn_count,
    COUNT(DISTINCT dol_vehicle_id) vehicle_count,
    ROUND(AVG(CASE WHEN sale_price>0 THEN sale_price END),2) avg_sale_price,
    ROUND(AVG(NULLIF(electric_range,0)),1) avg_range
FROM ev_registration
GROUP BY cafv_type,make,model,model_year,transaction_type,txn_year,county,city,
         range_bucket,new_or_used,cafv_eligibility;
```

---

## 📐 DAX Measures (Power BI)

```dax
Total Transactions = COUNTROWS(ev_registration)              -- 1,772,617
Unique Vehicles = DISTINCTCOUNT(ev_registration[dol_vehicle_id])  -- 377,329
BEV Vehicles = CALCULATE([Unique Vehicles], cafv_type="Battery Electric Vehicle (BEV)")  -- 300,390
PHEV Vehicles = CALCULATE([Unique Vehicles], cafv_type="Plug-in Hybrid Electric Vehicle (PHEV)")  -- 76,920
BEV Share % = DIVIDE([BEV Vehicles],[Unique Vehicles])*100    -- 79.61%
Avg Electric Range = AVERAGEX(FILTER(...,electric_range>0),electric_range)  -- 116.97 mi
Avg Sale Price = AVERAGEX(FILTER(...,sale_price>0),sale_price)  -- $48,720
New Vehicle Registrations = CALCULATE([Unique Vehicles], new_or_used="New")
```

> ⚠️ **Key Note:** `dol_vehicle_id` is NOT unique per row — same vehicle has multiple transactions (Renewal, Transfer, etc). Always use `DISTINCTCOUNT()` for vehicle counts, never `COUNTROWS()`.

---

## 📊 3-Page Dashboard (23 Visuals)

### Page 1 — Fleet Overview (11 visuals)
6 KPI cards (Transactions, Vehicles, BEV, PHEV, Avg Range, Avg Price) · EV Type donut · Top Makes bar · Transaction Type bar · 2 Slicers

### Page 2 — Adoption Trends (6 visuals)
Adoption line chart by model year · BEV vs PHEV column chart · Transactions by year column · Top Models bar · 2 Slicers

### Page 3 — Geographic Distribution & Compliance (6 visuals)
Top Counties bar · Range Bucket bar (from VIEW) · CAFV Eligibility donut · New vs Used donut · 2 Slicers

---

## 📈 Key Insights & Results

### Fleet Composition
- **377,329 unique vehicles** · **1,772,617 transactions** · BEV **79.61%** vs PHEV **20.38%**
- Avg Electric Range: **116.97 mi** · Avg Sale Price: **$48,720**

### Manufacturer Market Share
| Rank | Make | Unique Vehicles | Share | Avg Range |
|------|------|-----------------|-------|-----------|
| 1 | **TESLA** | 154,341 | **40.90%** | 236.0 mi |
| 2 | NISSAN | 27,620 | 7.32% | 94.9 mi |
| 3 | CHEVROLET | 26,890 | 7.13% | 118.2 mi |
| 4 | FORD | 20,633 | 5.47% | 25.9 mi |
| 5 | KIA | 17,961 | 4.76% | 86.2 mi |

### Top Models
| Make | Model | Vehicles | Avg Range | Avg Price |
|------|-------|----------|-----------|-----------|
| Tesla | **Model Y** | 75,131 | 291.0 mi | $52,058 |
| Tesla | Model 3 | 53,652 | 236.2 mi | $44,084 |
| Nissan | Leaf | 24,514 | 94.9 mi | $19,843 |
| Tesla | Model S | 13,133 | 222.5 mi | $65,530 |

### Geographic Concentration
| County | Vehicles | Share |
|--------|----------|-------|
| **King** | 209,431 | **55.50%** |
| Snohomish | 55,251 | 14.64% |
| Pierce | 39,640 | 10.51% |
| Clark | 26,819 | 7.11% |

> Top 4 counties = **87.76%** of entire WA EV fleet

### Adoption Timeline
- 2010: 57 vehicles → **2023 peak: 75,105** new registrations (1,317x growth)
- Steepest growth: 2020→2023 = **331.6% increase** in 3 years

### Compliance & Transaction Mix
- CAFV Eligible: only **88,465 (4.99%)** · Not Met: **1,684,152 (95.01%)**
- Registration Renewal: **854,334 (48.20%)** — most common transaction type
- New: 56.06% · Used: 43.94%

---

## 📊 KPI Summary

| KPI | Value | KPI | Value |
|-----|-------|-----|-------|
| Total Transactions | **1,772,617** | Unique Vehicles | **377,329** |
| BEV Vehicles | 300,390 (79.61%) | PHEV Vehicles | 76,920 (20.38%) |
| Avg Electric Range | **116.97 mi** | Avg Sale Price | **$48,720** |
| #1 Make | Tesla (40.90%) | #1 Model | Tesla Model Y |
| #1 County | King (55.50%) | Peak Year | 2023 — 75,105 |
| CAFV Eligible | 4.99% | Top Transaction | Renewal (48.20%) |
| Unique Makes | 50 | Counties Covered | 477 |

---

## ⚡ Challenges & Solutions

**Challenge 1 — 930MB File Too Large for Excel**
Python EDA performed instead — identified all 10 issues before any SQL written. Confirmed direct MySQL import path.

**Challenge 2 — Connection Timeout Doubling Data (Error 2013)**
First import appeared to fail but continued server-side → 3,545,234 rows (2x). Fixed: TRUNCATE + increase timeout to 60,000 sec + reimport.

**Challenge 3 — Duplicate DELETE Running 6,316 Seconds**
Self-join on 1.77M rows = 3.1 trillion comparisons. Decision: skip — 0.0035% impact = negligible vs hours of downtime.

**Challenge 4 — Index Creation Time**
10 indexes on 1.77M rows expected 25-65 min. Fixed: increased timeout, batch-ran all 10, monitored via SHOW PROCESSLIST.

**Challenge 5 — $0 Price / Zero Range Handling**
77.2% $0 prices and 45.3% zero ranges are valid (renewals, unreported PHEV data) — NOT missing data. Kept as-is; filtered only in specific analytical queries.

---

## 🎓 Skills Learned

- **Python EDA-First Methodology** — Tool selection from data evidence on a 930MB file
- **Large File MySQL Import** — LOAD DATA INFILE vs LOCAL INFILE; server upload folder method
- **Connection Timeout Engineering** — Understanding server-side continuation after client disconnect
- **Computational Complexity Judgement** — Recognising self-join DELETE intractability; cost-benefit skip decision
- **Zero vs NULL Semantics** — Distinguishing valid business zeros from missing data
- **Index Strategy** — 10 targeted indexes reducing multi-minute queries to seconds
- **Transaction Log Modelling** — DISTINCTCOUNT() over COUNTROWS() for non-unique ID columns

---

## 🎨 Custom Theme

`Electric_Future_EV_Theme.json` — Apply via **View → Themes → Browse for themes**

| Element | Color | Meaning |
|---------|-------|---------|
| Canvas | `#001A1A` — Deep Teal Black | EV/tech identity |
| Visuals | `#002626` — Dark Teal | Premium dark panels |
| KPI Borders + Numbers | `#00E5A0` — Electric Green | EV brand color |
| Data Color 1 | `#00E5A0` Green · `#00B4D8` Blue | Electric/charging theme |

---

## 📂 Repository Structure

```
ev-registration-dashboard/
│
├── 📊 EV_Registration_Dashboard.pbix
├── 📁 EDA/
│   └── EV_Analysis_Report.txt              # Python EDA output
├── 📁 MySQL/
│   ├── create_table.sql
│   ├── load_data.sql
│   ├── create_indexes.sql
│   └── analytical_queries.sql
├── 📁 Theme/
│   └── Electric_Future_EV_Theme.json
├── 📄 EV_Registration_Portfolio_Documentation.pdf
└── 📄 README.md
```

---

## 🚀 How to Use

```
1. Download dataset from data.wa.gov (Electric Vehicle Title and Registration Activity)
2. Copy CSV to MySQL Uploads folder (LOCAL INFILE may be restricted)
3. Run MySQL scripts in order: create_table → load_data → create_indexes → queries
4. Open EV_Registration_Dashboard.pbix in Power BI Desktop
5. Update MySQL connection if prompted → Refresh
6. Apply theme: View → Themes → Browse → select JSON file
7. Use slicers to explore by make, county, year, or transaction type
```

---


*Data Analytics · K.S. · Tools: MySQL + Power BI · Source: data.wa.gov*
