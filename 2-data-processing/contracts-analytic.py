# IMPORTING GOVERNMENT CONTRACT DATA + JOIN WITH LEGISLATOR
# - provided by https://github.com/unitedstates/congress-legislators
# wget https://theunitedstates.io/congress-legislators/legislators-current.json
# wget https://theunitedstates.io/congress-legislators/legislators-historical.json
# scp 2-data-processing/*.py ubuntu@$POSTGRES_PUBLIC_IP_DNS:~
# tmux set-option -g history-limit 5000 \; new-session
# time spark-submit --driver-memory 48g contracts-analytic.py > spark-output.txt
# scp ubuntu@$POSTGRES_PUBLIC_IP_DNS:spark-output.txt ./setup-scripts

# strategy is to read in legislator JSON,
# parse into several lists,
# then create a pySpark DataFrame from those lists

from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType
from pyspark.sql.functions import udf, col, expr, broadcast
import sys

from legislators import *

spark = SparkSession \
    .builder \
    .appName("Writing gov contract data to CockroachDB") \
    .master("spark://10.0.0.10:7077") \
    .config("spark.jars", "/usr/local/spark/jars/postgresql-42.2.6.jar") \
    .config('spark.executor.memory', '24g') \
    .config('spark.executor.cores', '8') \
    .config('spark.driver.cores','12') \
    .config('spark.default.parallelism', '100') \
    .config('spark.history.retainedApplications', '10') \
    .config('spark.network.timeout', '300s') \
    .config('spark.executor.heartbeatInterval', '60s') \
    .config('spark.task.maxFailures', '4') \
    .config('spark.sql.autoBroadcastJoinThreshold', str(5*10**7)) \
    .getOrCreate()


# pull contract data from postgresql (71+ million rows)
query = "(SELECT ROW_NUMBER() OVER(ORDER BY (SELECT NULL)) AS rno, " + \
        "t.action_date AS year, " + \
        "t.federal_action_obligation AS amount, " + \
        "t.legal_entity_state_code AS state, " + \
        "t.legal_entity_congressional AS district, " + \
        "t.naics AS code, " + \
        "t.legal_entity_country_code AS country_code " + \
        "FROM transaction_fpds t) XXX"

# read the table from postgresql
table0 = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", query) \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .option("partitionColumn", "rno") \
    .option("lowerBound", 0).option("upperBound", 72*10**6) \
    .option("numPartitions", 200) \
    .load() \
    .cache()

# loading a second table of labels that i want to join to
query2 = "(SELECT code, description FROM naics WHERE year = 2017 AND char_length(code) = 4) XXX"
industry_labels = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", query2) \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .load()
# clean up the industry code
def toIndus(code):
    try:
        return code[0:4]
    except:
        return None
toIndus = udf(toIndus, StringType())
table0 = table0.withColumn('code', toIndus('code'))

industry_labels.createOrReplaceTempView("industry_labels")
table0.createOrReplaceTempView("table0")
table0 = broadcast(spark.table("industry_labels")).join(spark.table("table0"), "code", "right_outer")

# loading a third table of state data that i want to join to
query3 = "(SELECT code AS state, name AS state_name, population, median_household_income " + \
         "FROM state_data WHERE year = 2010) XXX"
state_data = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", query3) \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .load()
state_data.createOrReplaceTempView("state_data")
table0.createOrReplaceTempView("table0")
table0 = broadcast(spark.table("state_data")) \
         .join(spark.table("table0"), "state", "right_outer")


# some light cleaning of date strings to just year
def toYear(s):
    try:
        year = int(s[-4:])
        if year < 1300:
            int(s[0:4])
    except:
        try: 
            year = int(s[0:4])
        except: 
            year = None
    return(year)

# removing the state label from district identifier
def toDist(s):
    try:
        if len(s) > 2:
            return int(s[-2:])
        else:
            return int(s)
    except:
        return None

# consolidating 'usa' versus 'united states'
def toUSA(s):
    try:
        if s == 'USA':
            return 'UNITED STATES'
        else:
            return s
    except:
        return s


toYear = udf(toYear, StringType())
toDist = udf(toDist, StringType())
toUSA = udf(toUSA, StringType())
table0 = table0.withColumn('year', toYear('year'))
table0 = table0.withColumn('district', toDist('district'))
table0 = table0.withColumn('country_code', toUSA('country_code'))

# broadcast the smaller legislator dataset to workers
# then join to financial data
combined_tab = table0.join(legislators.hint("broadcast"), \
                          on = ['state', 'district', 'year'], \
                          how = 'left_outer')
combined_tab.createOrReplaceTempView("combined_tab")

# WRITE A FEW ANALYTIC DATASETS
# - legislator: total $, by year, industry
query2r = "(SELECT firstname AS firstname, " + \
                 "lastname AS lastname, " + \
                 "MAX(typeofrep) AS typeofrep, " + \
                 "MAX(party) AS party, " + \
                 "MAX(district) AS district, " + \
                 "MAX(state_name) AS state_name, " + \
                 "MAX(population) AS population, " + \
                 "MAX(median_household_income) AS med_hh_income, " + \
                 "SUM(amount) AS amount, " + \
                 "year, description " + \
          "FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='rep') " + \
          "GROUP BY year, firstname, lastname, description " + \
          "ORDER BY year, firstname, lastname, description )"
legis_by_year_HR = spark.sql(query2r)
writeSplits(legis_by_year_HR, 'legis_by_year_HR')

query2s = "(SELECT firstname AS firstname, " + \
                 "lastname AS lastname, " + \
                 "MAX(typeofrep) AS typeofrep, " + \
                 "MAX(party) AS party, " + \
                 "MAX(district) AS district, " + \
                 "MAX(state_name) AS state_name, " + \
                 "MAX(population) AS population, " + \
                 "MAX(median_household_income) AS med_hh_income, " + \
                 "SUM(amount) AS amount, " + \
                 "year, description " + \
          "FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='sen') " + \
          "GROUP BY year, firstname, lastname, description " + \
          "ORDER BY year, firstname, lastname, description )"
legis_by_year_SEN = spark.sql(query2s)
writeSplits(legis_by_year_SEN, 'legis_by_year_SEN')


# - industry: total $ by year, state, by party
query3r = "(SELECT SUM(amount) AS amount, " + \
                 "MAX(state_name) AS state_name, " + \
                 "MAX(population) AS population, " + \
                 "MAX(median_household_income) AS med_hh_income, " + \
                 "year, description, state, party " + \
          "FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='rep') " + \
          "WHERE description IS NOT NULL " + \
          "GROUP BY description, year, state, party " + \
          "ORDER BY description, year, state, party )"
indus_by_year_HR = spark.sql(query3r)
writeSplits(indus_by_year_HR, 'indus_by_year_HR')

query3s = "(SELECT SUM(amount) AS amount, " + \
                 "MAX(state_name) AS state_name, " + \
                 "MAX(population) AS population, " + \
                 "MAX(median_household_income) AS med_hh_income, " + \
                 "year, description, state, party " + \
          "FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='sen') " + \
          "WHERE description IS NOT NULL " + \
          "GROUP BY description, year, state, party " + \
          "ORDER BY description, year, state, party )"
indus_by_year_SEN = spark.sql(query3s)
writeSplits(indus_by_year_SEN, 'indus_by_year_SEN')


# - states: total $ and money/people ratio by year
query4r = "(SELECT SUM(amount) AS amount, " + \
                 "MAX(state_name) AS state_name, " + \
                 "MAX(population) AS population, " + \
                 "MAX(median_household_income) AS med_hh_income, " + \
                 "SUM(round(amount / population * 1.0,6)) AS contract_pp, " + \
                 "SUM(round(amount / median_household_income,6)) AS contract_pd, " + \
                 "year, state, party " + \
          "FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='rep') " + \
          "GROUP BY year, state, party " + \
          "ORDER BY year, state, party )"
state_by_year_HR = spark.sql(query4r)
writeSplits(state_by_year_HR, 'state_by_year_HR')

query4s = "(SELECT SUM(amount) AS amount, " + \
                 "MAX(state_name) AS state_name, " + \
                 "MAX(population) AS population, " + \
                 "MAX(median_household_income) AS med_hh_income, " + \
                 "SUM(round(amount / population * 1.0,6)) AS contract_pp, " + \
                 "SUM(round(amount / median_household_income,6)) AS contract_pd, " + \
                 "year, state, party " + \
          "FROM (SELECT DISTINCT * FROM combined_tab WHERE typeofrep='rep') " + \
          "GROUP BY year, state, party " + \
          "ORDER BY year, state, party )"
state_by_year_SEN = spark.sql(query4s)
writeSplits(state_by_year_SEN, 'state_by_year_SEN')