-- date
action_date (min)

-- amount
federal_action_obligation

-- who is giving the money
awarding_sub_tier_agency_c
awarding_sub_tier_agency_n
awarding_agency_code
awarding_agency_name

-- recipient
naics
(join to naics table, column 'description' where year = max year)

-- id 
piid
nonnull parent_award_id


-- location
legal_entity_state_code
legal_entity_congressional
legal_entity_country_code






-- read in and process X rows at a time, then write
-- group by month, year, industry