# FedSpend 
[[Slides](https://docs.google.com/presentation/d/1KTjFM93Z1USEoJl7P9blTCVDJaPI7bXSucENJ3FTMcg/edit?usp=sharing)] [[UI](http://engineerdata.xyz)]


A tool to see where federal money is going with additional information on associated legislators.

<hr/>

## Overview

Companies are interested in the distribution of US federal spending on government contracts, across industries and across states, to direct investment or expansion decisions. Taxpayers are also interested because this is their money being spent on their behalf, and the spending should be in line with their priorities.

While federal laws [mandate](https://www.usaspending.gov/#/about) the public accessibility of federal spending data, available exploratory tools are focused on individual payments and the data are provided without context. [FedSpend](http://engineerdata.xyz) is designed to address this gap in accessibility, by linking federal payments to the recipient's House and Senate representatives. The data are aggregated to abstract away government peculiarities and presented via UI with additional state demographic information. 

<hr/>

## Data
Federal spending data are provided by the US Government as a [PostgreSQL dump archive file](https://files.usaspending.gov/database_download/), updated monthly. 


Every row in the federal spending dataset is an _obligation_ (i.e., promise to pay). _Outlays_ (i.e., actual payments) are not included. Additional contract funding modifications, such as the increase or decrease of a contract obligation, are entered as an additional row in the dataset with the adjustment amount. See an example below. 

| Date  | NAICS code | Recipient | Amount | District | State | 
| ------------- | ------------- |  -- | -- | -- | -- |
| 2019  | [519130](https://www.naics.com/naics-code-description/?code=519130)  | Bojack Horseman Inc. | $45,000 | 36 |  CA | 
| 2019  | 519130  | Bojack Horseman Inc. | -$20,000 | 36 | CA | 
| 2019  | 519130  | Bojack Horseman Inc. | $5,000 | 36 | CA | 

_In this example, the total value of the contract is $30,000._
  
Historical and current House of Representatives and Senate data are [provided](https://github.com/unitedstates/congress-legislators) as a public resource, maintained by a community of interested persons. These data are linked to government contracts by year and city/state of the recipient. 


## Installation
An overview is provided here, while full details are in the [wiki](https://github.com/sanoke/fedspend/wiki).
1. Set up a PostgreSQL database and restore the full database (~600GB) from the archive file (~60GB).
2. Set up a CockroachDB cluster.
3. Set up a Spark cluster for the migration of data from PostgreSQL to CockroachDB.
4. Migrate each table (~60 tables) from PostgreSQL to CockroachDB via Spark.
5. Calculate aggregate tables from PostgreSQL using Spark and save to CockroachDB.
6. Set up a web server with Apache and UI with Flask.
7. Set up Airflow to run the data pipeline + version control, and refresh the UI. 

## Architecture
![](https://github.com/sanoke/fedspend/raw/master/img/architecture.png)

## Engineering challenges

### Choosing a database to migrate to
The data come prepackaged in a PostgreSQL database, which is in itself a stable choice but there are several modern options to choose from. Prioritizing _pattern flexibility_ and _efficiency_ over _infinite scale_, the [PIE theorem](https://www.alexdebrie.com/posts/choosing-a-database-with-pie/) dictates that another relational database is the right choice. CockroachDB was chosen because of its built-in distributed computing and its resilency. 

### Version control

![](https://github.com/sanoke/fedspend/raw/master/img/data.png)

Consider the database dump posted in February 2020. Rather than overwriting our existing data with the new archive dump, we select out and append the new data (green), then conduct a version control procedure on the carryover data (yellow). The goal is to check whether that carryover data -- which we expect to be identical -- is in fact identical. A hash function is applied on the obligation column in both versions and its output noted.

