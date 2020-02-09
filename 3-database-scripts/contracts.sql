-- CONTRACT DATA --
-- CREATING ANALYTIC SUMMARIES IN COCKROACHDB

-- [intermediate table]
-- pulling contract data directly from federal source
-- (71+ million rows, each is a contract action)
SELECT *
FROM (
    SELECT ROW_NUMBER() OVER(ORDER BY (SELECT NULL)) AS rno,
        t.action_date AS year,
        t.federal_action_obligation AS amount,
        t.legal_entity_state_code AS state,
        t.legal_entity_congressional AS district,
        t.naics AS code,
        t.legal_entity_country_code AS country_code
        FROM transaction_fpds t  )
AS govcontract_data


-- [intermediate table]
-- pulling state data directly from federal source
-- (these data were joined to the contract data)
SELECT code AS state,
       name AS state_name,
       population,
       median_household_income
  FROM state_data
  WHERE year = 2010  -- census year


-- [intermediate table]
-- pulling industry assignments directly from federal source
-- - an NAICS code assigns a business to an industry,
-- - where more digits = more niche; needed rough groupings
-- - so selected first 4 characters
-- - (corresponding to about 300 categories)
-- (these data were joined to the contract data)
SELECT code,
       description  -- name of industry
  FROM naics
 WHERE year = 2017
   AND char_length(code) = 4


-- [analytic table]
-- legislator: total $ by year, industry
-- - within Spark, each contract was associated
-- - to a legislator by the location of the recipient.
-- - 'combined_tab' is the contract data joined to state and NAICS data
-- - 'typeofrep' is 'rep' for House rep and 'sen' for senator
SELECT firstname AS firstname,
       lastname AS lastname,
       MAX(typeofrep) AS typeofrep,
       MAX(party) AS party,
       MAX(district) AS district,
       MAX(state_name) AS state_name,
       MAX(population) AS population,
       MAX(median_household_income) AS med_hh_income,
       SUM(amount) AS amount,
       year,
       description
 FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='rep')
GROUP BY year, firstname, lastname, description
ORDER BY year, firstname, lastname, description


-- [analytic table]
-- industry: total $ by year, state, party
-- - 'combined_tab' is the contract data joined to state and NAICS data
-- - 'typeofrep' is 'rep' for House rep and 'sen' for senator
SELECT SUM(amount) AS amount,
       MAX(state_name) AS state_name,
       MAX(population) AS population,
       MAX(median_household_income) AS med_hh_income,
       year, description, state, party
  FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='rep')
 WHERE description IS NOT NULL
GROUP BY description, year, state, party
ORDER BY description, year, state, party


-- [analytic table]
-- state: total $ and money/people ratio by year, state, party
-- - 'combined_tab' is the contract data joined to state and NAICS data
-- - 'typeofrep' is 'rep' for House rep and 'sen' for senator
SELECT SUM(amount) AS amount,
       MAX(state_name) AS state_name,
       MAX(population) AS population,
       MAX(median_household_income) AS med_hh_income,
       SUM(round(amount / population * 1.0,6)) AS contract_pp,
       SUM(round(amount / median_household_income,6)) AS contract_pd,
       year, state, party
 FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='rep')
GROUP BY year, state, party
ORDER BY year, state, party