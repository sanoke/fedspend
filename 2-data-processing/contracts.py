# IMPORTING GOVERNMENT CONTRACT DATA + JOIN WITH LEGISLATOR
# - provided by https://github.com/unitedstates/congress-legislators
# wget https://theunitedstates.io/congress-legislators/legislators-current.json
# wget https://theunitedstates.io/congress-legislators/legislators-historical.json
# scp 2-data-processing/*.py ubuntu@$POSTGRES_PUBLIC_IP_DNS:~
# tmux set-option -g history-limit 5000 \; new-session
# time spark-submit --driver-memory 48g contracts.py > sparrk-output.txt

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
        "FROM transaction_fpds t ) XXX" 

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
query2 = "(SELECT code, description FROM naics WHERE year = 2017) XXX"
industry_labels = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", query2) \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .load()
industry_labels.createOrReplaceTempView("industry_labels")
table0.createOrReplaceTempView("table0")
table0 = broadcast(spark.table("industry_labels")).join(spark.table("table0"), "code", "left_outer")

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
def usa(s):
    try: 
        if s == 'USA':
            return 'UNITED STATES'
        else:
            return s
    except:
        return s       


toYear = udf(toYear, StringType())
toDist = udf(toDist, StringType())
usa = udf(usa, StringType())
table0 = table0.withColumn('year', toYear('year'))
table0 = table0.withColumn('district', toDist('district'))
table0 = table0.withColumn('country_code', usa('country_code'))

numSplits = 100
tempTable_split = table0.randomSplit( [1.0] * numSplits )

print("Split table successfully.")

# for every dataframe in the list...
counter = 1
for df in tempTable_split:
    tab0 = "govcontract_data"

    # broadcast the smaller legislator dataset to workers 
    # then join to financial data
    combinedTab = df.join(legislators.hint("broadcast"), \
                          on = ['state', 'district', 'year'], \
                          how = 'left_outer')

    # write the result to CDB
    writeTable(combinedTab, tab0, saveMode="append")
    print(tab0 + ': wrote chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout) 
    counter += 1
