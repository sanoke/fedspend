# IMPORTING GOVERNMENT GRANT DATA + JOIN WITH LEGISLATOR
# - provided by https://github.com/unitedstates/congress-legislators
# wget https://theunitedstates.io/congress-legislators/legislators-current.json
# wget https://theunitedstates.io/congress-legislators/legislators-historical.json
# scp 2-data-processing/*.py ubuntu@$POSTGRES_PUBLIC_IP_DNS:~
# tmux set-option -g history-limit 5000 \; new-session
# time spark-submit --driver-memory 48g grants.py > sparrk-output.txt

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
    .appName("Writing gov grant data to CockroachDB") \
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

# pull grant data from postgresql (60 million rows)
query = "(SELECT ROW_NUMBER() OVER(ORDER BY (SELECT NULL)) AS rno, " + \
        "t.action_date AS year, " + \
        "t.federal_action_obligation AS amount, " + \
        "t.legal_entity_state_code AS state, " + \
        "t.legal_entity_congressional AS district, " + \
        "t.cfda_title AS industry, " + \
        "t.legal_entity_country_code AS country_code " + \
        "FROM transaction_fabs t ) XXX" 

# read the table from postgresql
table0 = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", query) \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .option("partitionColumn", "rno") \
    .option("lowerBound", 0).option("upperBound", 60*10**6) \
    .option("numPartitions", 200) \
    .load() \
    .cache()


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

      
toYear = udf(toYear, StringType())

table0 = table0.withColumn('year', toYear('year'))


numSplits = 100
tempTable_split = table0.randomSplit( [1.0] * numSplits )

print("Split table successfully.")

# for every dataframe in the list...
counter = 1
for df in tempTable_split:
    tab0 = "govgrant_data"

    # broadcast the smaller legislator dataset to workers 
    # then join to financial data
    combinedTab = df.join(legislators.hint("broadcast"), \
                          on = ['state', 'district', 'year'], \
                          how = 'left_outer')

    # write the result to CDB
    writeTable(combinedTab, tab0, saveMode="append")
    print(tab0 + ': wrote chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout) 
    counter += 1
