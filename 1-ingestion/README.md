# Ingestion

The federal spending data were provided within a PostgreSQL database archive file. Ingestion involved restoration of the full database and migration to CockroachDB. 


#### `fedspend-ingest.sh` 
[[Details](https://github.com/sanoke/fedspend/wiki/Data-pipeline:-Ingesting-data)] Instructions for restoring the PostgreSQL archive dump.

#### `migration.py` 
[TO DO] PySpark script for migration of PostgreSQL tables to CockroachDB. 

#### `migrationhelp.py` 
[TO DO] PySpark script containing helper functions and objects for migration; a dependency of `migration.py`. 

