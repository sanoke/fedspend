-- CONTRACT DATA -- 
-- CREATING ANALYTIC SUMMARIES IN COCKROACHDB
-- pull contract data for a specific legislator
-- (quoting column names to preserve case)

-- legislator totals by year
CREATE TABLE contract_legis_by_year AS
    SELECT year, 
           SUM(amount) AS total_obl,
           MAX(state) AS state,
           MAX(district) AS district,
           MAX("firstName") AS first_name,
           MAX("lastName") AS last_name,
           MAX("typeOfRep") AS type_rep,
           MAX("party") AS party
      FROM (
        SELECT DISTINCT * FROM govcontract_data)
    GROUP BY year;

-- state totals by year and party
CREATE TABLE contract_legis_by_year AS
    SELECT year, 
           SUM(amount) AS total_obl,
           MAX(state) AS state,
           MAX(district) AS district,
           MAX("firstName") AS first_name,
           MAX("lastName") AS last_name,
           MAX("typeOfRep") AS type_rep,
           MAX("party") AS party
      FROM (
        SELECT DISTINCT * FROM govcontract_data)
    GROUP BY year;