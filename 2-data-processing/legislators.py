# IMPORTING LEGISLATOR DATA (JSON) + PARSING
# - provided by https://github.com/unitedstates/congress-legislators
# wget https://theunitedstates.io/congress-legislators/legislators-current.csv
# wget https://theunitedstates.io/congress-legislators/legislators-historical.csv

# strategy is to read in legislator JSON,
# parse into several lists, 
# then create a pySpark DataFrame from those lists 

from pyspark.sql import SparkSession 
from pyspark.sql.types import IntegerType
from pyspark.sql.functions import udf, col, expr
import sys

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
    .getOrCreate()

# read in the JSON file, parse into lists
lc = spark.read.option('multiline','true').json('legislators-current.json').collect()
firstName = []
lastName  = []
typeOfRep = []
party     = []
state     = []
district  = []
year      = []
# for every legislator...
for l in lc:
    # ...and every term...
    for t in l['terms']:
        y = 0
        term_length = int(t['end'][0:4]) - int(t['start'][0:4])
        # ...and for each year in the term
        while y < term_length:
            firstName.append(l['name']['first'])
            lastName.append(l['name']['last'])
            typeOfRep.append(t['type'])
            party.append(t['party'])
            state.append(t['state'])
            district.append(t['district'])
            year.append(int(t['start'][0:4]) + y)


# repeat for file containing historical reps
lh = spark.read.option('multiline','true').json('legislators-historical.json').collect()
# for every legislator...
for l in lc:
    # ...and every term...
    for t in l['terms']:
        # we don't need data for legislators before 2000
        if int(t['start'][0:4] < 2000: 
            pass
        y = 0
        term_length = int(t['end'][0:4]) - int(t['start'][0:4])
        # ...and for each year in the term
        while y < term_length:
            firstName.append(l['name']['first'])
            lastName.append(l['name']['last'])
            typeOfRep.append(t['type'])
            party.append(t['party'])
            state.append(t['state'])
            district.append(t['district'])
            year.append(int(t['start'][0:4]) + y)


# finally, combine our lists into a DataFrame
legislators = spark.createDataFrame(zip(firstName, lastName, typeOfRep, party,
                                        state, district, year), 
                                    schema=['firstName', 'lastName', 'typeOfRep',
                                            'party', 'state', 'district', 'year']).show()
