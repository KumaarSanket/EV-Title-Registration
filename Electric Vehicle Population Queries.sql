CREATE DATABASE IF NOT EXISTS ev_project;
USE ev_project;

DROP TABLE IF EXISTS ev_registration;

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



USE ev_project;

SET NAMES latin1;
SET SESSION sql_mode = '';
SET GLOBAL sql_mode = '';

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Electric_Vehicle_Title_and_Registration_Activity_20260623.csv'
INTO TABLE ev_registration
CHARACTER SET latin1
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(cafv_type, vin_10, dol_vehicle_id, model_year, make, model,
 primary_use, @elec_range, odometer_reading, odometer_description,
 new_or_used, @sale_price_raw, @sale_date_raw, transaction_type,
 @txn_date_raw, txn_year, @county_raw, city, @state_raw,
 @postal_raw, cafv_eligibility,
 @meets_range, @meets_sale_date, @meets_sale_price,
 battery_range_req, purchase_date_req, sale_price_req,
 ev_fee_paid, @transport_raw, @hybrid_raw,
 @geoid_raw, @leg_dist_raw, electric_utility)
SET
    electric_range      = NULLIF(@elec_range, ''),
    sale_price          = CAST(REPLACE(REPLACE(TRIM(@sale_price_raw),'$',''),',','') AS DECIMAL(12,2)),
    sale_date           = NULLIF(STR_TO_DATE(NULLIF(TRIM(@sale_date_raw),''), '%M %d, %Y'), '0000-00-00'),
    transaction_date    = STR_TO_DATE(TRIM(@txn_date_raw), '%M %d, %Y'),
    county              = NULLIF(TRIM(@county_raw), ''),
    state               = NULLIF(TRIM(@state_raw), ''),
    postal_code         = NULLIF(LPAD(TRIM(SUBSTRING_INDEX(TRIM(@postal_raw),'.','1')),5,'0'),'00000'),
    meets_range_req     = IF(TRIM(@meets_range)='True', 1, 0),
    meets_sale_date_req = IF(TRIM(@meets_sale_date)='True', 1, 0),
    meets_sale_price_req = IF(TRIM(@meets_sale_price)='True', 1, 0),
    transport_fee_paid  = NULLIF(TRIM(@transport_raw), ''),
    hybrid_fee_paid     = NULLIF(TRIM(@hybrid_raw), ''),
    geoid_2020          = NULLIF(TRIM(SUBSTRING_INDEX(TRIM(@geoid_raw),'.','1')),''),
    legislative_district = NULLIF(TRIM(SUBSTRING_INDEX(TRIM(@leg_dist_raw),'.','1')),'');
    
    SELECT COUNT(*) FROM ev_registration;
-- Should show: 1,772,617 ✅

USE ev_project;
TRUNCATE TABLE ev_registration;

-- Clean 1 — Remove 62 exact duplicates:
-- See how many duplicates exist
SELECT COUNT(*) - COUNT(DISTINCT
    CONCAT(vin_10,'|',dol_vehicle_id,'|',transaction_type,'|',
           COALESCE(transaction_date,''),'|',sale_price))
AS duplicate_check
FROM ev_registration;

-- Remove duplicates keeping lowest id
DELETE e1 FROM ev_registration e1
INNER JOIN ev_registration e2
WHERE e1.id > e2.id
  AND e1.vin_10 = e2.vin_10
  AND e1.dol_vehicle_id = e2.dol_vehicle_id
  AND e1.transaction_type = e2.transaction_type
  AND COALESCE(e1.transaction_date,'1900-01-01') = COALESCE(e2.transaction_date,'1900-01-01')
  AND e1.sale_price = e2.sale_price;

-- Verify
SELECT COUNT(*) FROM ev_registration;
-- Should show ~1,772,555 (62 fewer) ✅

SHOW PROCESSLIST;
KILL 21;

-- Clean 2 — Add indexes for query speed:
CREATE INDEX idx_make          ON ev_registration(make);
CREATE INDEX idx_model         ON ev_registration(model);
CREATE INDEX idx_year          ON ev_registration(model_year);
CREATE INDEX idx_txn_year      ON ev_registration(txn_year);
CREATE INDEX idx_county        ON ev_registration(county);
CREATE INDEX idx_city          ON ev_registration(city);
CREATE INDEX idx_txn_type      ON ev_registration(transaction_type);
CREATE INDEX idx_txn_date      ON ev_registration(transaction_date);
CREATE INDEX idx_cafv_type     ON ev_registration(cafv_type);
CREATE INDEX idx_dol           ON ev_registration(dol_vehicle_id);

SHOW INDEX FROM ev_registration;

-- Check dates converted correctly
SELECT sale_date, transaction_date
FROM ev_registration
WHERE sale_date IS NOT NULL LIMIT 5;

-- Check sale price cleaned
SELECT sale_price FROM ev_registration
WHERE sale_price > 0 LIMIT 5;

-- Check booleans converted
SELECT DISTINCT meets_range_req,
       meets_sale_date_req,
       meets_sale_price_req
FROM ev_registration;
-- Should show only 0 and 1 ✅

-- Check postal code formatted
SELECT postal_code FROM ev_registration
WHERE postal_code IS NOT NULL LIMIT 5;
-- Should show 98110, 98052 etc. ✅


-- Query 1 — Overall KPIs:
SELECT
    COUNT(*)                                               AS total_transactions,
    COUNT(DISTINCT dol_vehicle_id)                        AS unique_vehicles,
    COUNT(DISTINCT make)                                   AS unique_makes,
    COUNT(DISTINCT model)                                  AS unique_models,
    COUNT(DISTINCT county)                                 AS counties_covered,
    MIN(txn_year)                                         AS earliest_year,
    MAX(txn_year)                                         AS latest_year,
    SUM(CASE WHEN cafv_type LIKE '%Battery%' THEN 1 ELSE 0 END) AS bev_txns,
    SUM(CASE WHEN cafv_type LIKE '%Plug%' THEN 1 ELSE 0 END)    AS phev_txns,
    SUM(CASE WHEN cafv_type LIKE '%Hydrogen%' THEN 1 ELSE 0 END) AS hydrogen_txns
FROM ev_registration;


-- Query 2 — Transaction Type Breakdown:
SELECT
    transaction_type,
    COUNT(*)                                               AS total_txns,
    ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM ev_registration),2) AS pct_share
FROM ev_registration
GROUP BY transaction_type
ORDER BY total_txns DESC;


-- Query 3 — Top 10 Makes by Registrations:
SELECT
    make,
    COUNT(DISTINCT dol_vehicle_id)                        AS unique_vehicles,
    COUNT(*)                                               AS total_txns,
    ROUND(COUNT(DISTINCT dol_vehicle_id)*100.0/
        (SELECT COUNT(DISTINCT dol_vehicle_id) FROM ev_registration),2) AS market_share_pct,
    ROUND(AVG(NULLIF(electric_range,0)),1)                AS avg_electric_range
FROM ev_registration
GROUP BY make
ORDER BY unique_vehicles DESC
LIMIT 10;


-- Query 4 — EV Adoption Trend by Year (Original Registrations Only):
SELECT
    model_year,
    COUNT(DISTINCT dol_vehicle_id)                        AS unique_vehicles,
    SUM(CASE WHEN cafv_type LIKE '%Battery%' THEN 1 ELSE 0 END) AS bev_count,
    SUM(CASE WHEN cafv_type LIKE '%Plug%' THEN 1 ELSE 0 END)    AS phev_count,
    ROUND(AVG(NULLIF(electric_range,0)),1)                AS avg_range
FROM ev_registration
WHERE transaction_type IN ('Original Registration','Original Title')
  AND model_year BETWEEN 2010 AND 2026
GROUP BY model_year
ORDER BY model_year;


-- Query 5 — Top 10 Counties:
SELECT
    county,
    COUNT(DISTINCT dol_vehicle_id)                        AS unique_vehicles,
    ROUND(COUNT(DISTINCT dol_vehicle_id)*100.0/
        (SELECT COUNT(DISTINCT dol_vehicle_id) FROM ev_registration),2) AS pct_share,
    COUNT(DISTINCT make)                                   AS makes_available
FROM ev_registration
WHERE county IS NOT NULL
GROUP BY county
ORDER BY unique_vehicles DESC
LIMIT 10;


-- Query 6 — Top 10 Models:
SELECT
    make, model, cafv_type,
    COUNT(DISTINCT dol_vehicle_id)                        AS unique_vehicles,
    ROUND(AVG(NULLIF(electric_range,0)),1)                AS avg_range,
    ROUND(AVG(CASE WHEN sale_price > 0
              THEN sale_price END),0)                     AS avg_sale_price
FROM ev_registration
GROUP BY make, model, cafv_type
ORDER BY unique_vehicles DESC
LIMIT 10;

-- Query 7 — CAFV Eligibility Analysis:
SELECT
    cafv_eligibility,
    COUNT(*) AS total,
    ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM ev_registration),2) AS pct,
    ROUND(AVG(electric_range),1) AS avg_range
FROM ev_registration
GROUP BY cafv_eligibility ORDER BY total DESC;


-- Query 8 — Create Analytical VIEW:
CREATE OR REPLACE VIEW vw_ev_summary AS
SELECT
    cafv_type,
    make,
    model,
    model_year,
    transaction_type,
    txn_year,
    county,
    city,
    CASE
        WHEN electric_range IS NULL  THEN '00-Unknown'
        WHEN electric_range = 0      THEN '00-Unknown'
        WHEN electric_range < 50     THEN '01-Under 50mi'
        WHEN electric_range < 100    THEN '02-50 to 99mi'
        WHEN electric_range < 200    THEN '03-100 to 199mi'
        WHEN electric_range < 300    THEN '04-200 to 299mi'
        ELSE                              '05-300mi+'
    END                                                    AS range_bucket,
    new_or_used,
    cafv_eligibility,
    COUNT(*)                                               AS txn_count,
    COUNT(DISTINCT dol_vehicle_id)                        AS vehicle_count,
    SUM(CASE WHEN sale_price > 0 THEN 1 ELSE 0 END)      AS actual_sales,
    ROUND(AVG(CASE WHEN sale_price > 0
              THEN sale_price END),2)                     AS avg_sale_price,
    ROUND(AVG(NULLIF(electric_range,0)),1)                AS avg_range
FROM ev_registration
GROUP BY cafv_type, make, model, model_year, transaction_type,
         txn_year, county, city, range_bucket,
         new_or_used, cafv_eligibility;