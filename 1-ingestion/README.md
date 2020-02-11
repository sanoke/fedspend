# Ingestion

The federal spending data were provided within a PostgreSQL database archive file. Ingestion involved restoration of the full database and migration to CockroachDB. 


#### `fedspend-ingest.sh` 
[[Details](https://github.com/sanoke/fedspend/wiki/Data-pipeline:-Ingesting-data)] Instructions for restoring the PostgreSQL archive dump.

#### `migration.py` 
[[Details](https://github.com/sanoke/fedspend/wiki/Data-pipeline:-Migration)] PySpark script for migration of PostgreSQL tables to CockroachDB. 

#### `migrationhelp.py` 
[[Details](https://github.com/sanoke/fedspend/wiki/Data-pipeline:-Migration)] PySpark script containing helper functions and objects for migration; a dependency of `migration.py`. 

