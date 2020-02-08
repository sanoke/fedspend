# IMPORTING GOVERNMENT CONTRACT DATA + JOIN WITH LEGISLATOR
# - provided by https://github.com/unitedstates/congress-legislators
# wget https://theunitedstates.io/congress-legislators/legislators-current.csv
# wget https://theunitedstates.io/congress-legislators/legislators-historical.csv

# strategy is to read in legislator JSON,
# parse into several lists, 
# then create a pySpark DataFrame from those lists 

from pyspark.sql import SparkSession 
from pyspark.sql.types import IntegerType
from pyspark.sql.functions import udf, col, expr, broadcast
import sys

from legislators import *

spark = SparkSession \
    .builder \
    .appName("Migration from PostgreSQL to CockroachDB") \
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
    .config('spark.sql.autoBroadcastJoinThreshold', str(5*10**7))
    .getOrCreate()


# pull contract data from postgresql (71+ million rows)
query = "(SELECT t.action_date AS date, " + \
        "t.federal_action_obligation AS amount, " + \
        "n.description AS industry, " + \
        "t.legal_entity_state_code AS state, " + \
        "t.legal_entity_congressional AS district, " + \
        '(CASE WHEN t.legal_entity_country_code = "UNITED STATES" THEN "USA"' + \
        "      ELSE t.legal_entity_country_code) AS country_code " + \
        "FROM transaction_fpds t " + \
        "LEFT JOIN (SELECT * FROM naics WHERE n.year = 2017) n " + \
        "ON n.code = t.naics LIMIT 100000) XXX" 


# read the table from postgresql
try: 
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
except: 
    print("There's an issue with the partition process.", file=sys.stdout) 
    
print("There are " + str(table0.rdd.getNumPartitions()) + " partitions " + \
        "across " + str(rowNum) + " rows.", file=sys.stdout) 


# some light cleaning of date strings to just year
def toYear(s):
    if year < 1000:
        return int(s[-4:])
    else: 
        return int(s[0:4])

# removing the state label from district identifier
def toDist(s):
    if len(s) > 2:
        return int(s[-2:])
    else:
        return int(s)


toYear = udf(toYear, IntegerType())
table0 = table0.withColumn('year', toYear('date'))
table0 = table0.withColumn('district', toDist('district'))

numSplits = 100
tempTable_split = table0.randomSplit( [1.0] * numSplits )

print("Split table " + tab0 + " successfully.")

# for every dataframe in the list...
counter = 1
for df in tempTable_split:
    tab0 = "transaction_fpds"

    # broadcast the smaller legislator dataset to workers 
    # then join to financial data
    combinedTab = df.join(legislators.hint("broadcast"), \
                          on = ['state', 'district', 'year'], \
                          how = 'left_outer')

    # write the result to CDB
    print(tab0 + ': trying to write chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout) 
    writeTable(df, tab0, saveMode="append")
    print(tab0 + ': wrote chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout) 
    counter += 1
