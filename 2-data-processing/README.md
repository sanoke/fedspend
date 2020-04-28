# Data Processing

These scripts are used to extract and aggregate contract data from the federal spending PostgreSQL database. The spending data are joined to legislator data, which is extracted from a JSON file. Finally, the aggregation tables are written to CockroachDB. 

All of the above are done in PySpark. 


#### `congressional_pop.py`
[source](https://www.census.gov/programs-surveys/acs/data/summary-file.html) 

[source](https://www2.census.gov/programs-surveys/acs/summary_file/2018/data/?#)
[source](https://www2.census.gov/programs-surveys/acs/summary_file/2018/data/README_2018_FTP_Archives.pdf)


#### `legislators.py`
[[Details](https://github.com/sanoke/fedspend/wiki/Data-pipeline:-Ingesting-data#historical-legislator-data)] PySpark script for ingesting [legislator information](https://github.com/unitedstates/congress-legislators); loaded as a module within federal spending processing.

#### `contracts.py`, `grants.py` 
PySpark script for joining federal spending *contract* (payment for goods or service) and *grant* (provision of money to serve a public purpose) data to legislator data, and writing to CockroachDB. No aggregation done in these script, to allow a data scientist some analytic flexibility. 

#### `contracts-analytic.py` 
PySpark script for joining federal spending contract data to legislator data, and calculating aggregations. This script generates the tables that support the FedSpend UI. 

#### `USAspendingGlossary.xlsx`
Reference document from [USASpending.gov](http://www.usaspending.gov) to understand the terminology used within the federal spending dataset. 

####  `version_control.md`
Some notes on what version control would look like

####  `airflow.md`
Some notes on what an automated workflow implementation would look like
