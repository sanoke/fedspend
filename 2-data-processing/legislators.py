# IMPORTING LEGISLATOR DATA (JSON) + METADATA
# - provided by https://github.com/unitedstates/congress-legislators
# wget https://theunitedstates.io/congress-legislators/legislators-current.csv
# wget https://theunitedstates.io/congress-legislators/legislators-historical.csv
# OTHER DATA
# - population data
# wget https://www2.census.gov/programs-surveys/acs/summary_file/2018/data/1_year_data_profiles/Congressional_District/DP05.csv
# - mapping of state names to abbreviation
# manual download: https://worldpopulationreview.com/states/state-abbreviations/
# - income data
# wget https://www.irs.gov/pub/irs-soi/17incd.csv
#
# ssh ubuntu@$SPARK_NODE1_PUBLIC_IP_DNS "wget https://theunitedstates.io/congress-legislators/legislators-current.json"
# ssh ubuntu@$SPARK_NODE1_PUBLIC_IP_DNS "wget https://theunitedstates.io/congress-legislators/legislators-historical.json"


from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, \
                              IntegerType, StringType, DateType, ArrayType
import pyspark.sql.functions as F
import time
import sys

spark = SparkSession \
    .builder \
    .appName("Writing analytic contract data to CockroachDB") \
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

# --- CONGRESSIONAL DISTRICT POPULATION DATA
congrPop = spark.read.load('raw data/DP05.csv', \
                           format = 'csv', \
                           header = True)

congrPop.show(truncate = False)

# filter for the total population in each district
# (filter out subgroup population counts)
congrPop = congrPop.filter(congrPop.TITLE == 'Total population') \
                   .filter(congrPop.PROFLN == 1) \
                   .select('GEONAME', 'PRF_ESTIMATE')


# congressional districts are specified as long strings,
# e.g., Congressional District 1 (116th Congress), Alabama
# will put the state in its own field, and the district in its own field
congrPop = congrPop.withColumn('splits1', F.split(congrPop.GEONAME, ', '))
congrPop = congrPop.withColumn('state', congrPop.splits1.getItem(1))

congrPop = congrPop.withColumn('splits2', F.split(congrPop.splits1.getItem(0), '\s+'))
congrPop = congrPop.withColumn('district', congrPop.splits2.getItem(2)) \
                   .withColumnRenamed('PRF_ESTIMATE', 'popSize') \
                   .drop('GEONAME', 'splits1', 'splits2')

# districts called '(at large)' (just one rep) renamed to 1
congrPop = congrPop.withColumn('district', \
                               F.when(congrPop.district == '(at', 1) \
                                .otherwise(congrPop.district))

# cast population size (after removing commas) and district to integers
congrPop.printSchema()
#   +-------+--------+--------+
#   |popSize|state   |district|
#   +-------+--------+--------+
#   |715,346|Alabama |1       |
#   |678,122|Alabama |2       |
#   |708,409|Alabama |3       |
#   ...
congrPop = congrPop.withColumn('popSize', F.regexp_replace('popSize', ',', '')) \
                   .withColumn('popSize', F.col('popSize').cast('Integer')) \
                   .withColumn('district', F.col('district').cast('Integer'))


# state abbreviations
stateAbbr = spark.read.load('raw data/stateAbbrev.csv', \
                            format = 'csv', \
                            header = True) \
                      .drop('Abbrev') \
                      .withColumnRenamed('State', 'state0')

# add the state abbreviations
congrPop = congrPop.join(stateAbbr, \
                         congrPop.state == stateAbbr.state0, \
                         how = 'leftouter')

# validating result of the join... :(
congrPop0.where(F.col("state0").isNull()).show()
#   +-------+-----------+--------+-----+------+----+
#   |popSize|     state0|district|State|Abbrev|Code|
#   +-------+-----------+--------+-----+------+----+
#   |3195153|Puerto Rico|    null| null|  null|null|
#   +-------+-----------+--------+-----+------+----+

# ...cleaning up
congrPop = congrPop.drop('state0') \
                   .withColumnRenamed('Code', 'abbrev')


# --- CONGRESSIONAL DISTRICT INCOME AND TAX DATA
income = spark.read.load('raw data/17incd.csv', \
                         format = 'csv', \
                         header = True)
income = income.select('A06500', 'A04800', 'A11900', 'A02650',
                       'STATE', 'CONG_DISTRICT', 'agi_stub')

# filter for aggregated amounts
# (not broken out by AGI)
income = income.filter(income.CONG_DISTRICT != 0) \
               .filter(income.agi_stub == 'Total')

# from documentation guide
# https://www.irs.gov/pub/irs-soi/17incddocguide.docx
income = income.withColumn('total_fed_taxes_due', income.A06500.cast(IntegerType())) \
               .withColumn('total_income', income.A02650.cast(IntegerType())) \
               .withColumn('taxable_income', income.A04800.cast(IntegerType())) \
               .withColumn('total_overpayment', income.A11900.cast(IntegerType())) \
               .withColumnRenamed('CONG_DISTRICT', 'district') \
               .withColumnRenamed('STATE', 'state_abbrev')
income = income.drop('A06500', 'A04800', 'A11900', 'A02650', 'agi_stub')
income.printSchema()


# --- CONGRESSIONAL DISTRICT LEGISLATOR DATA
# NOTE manually placed JSON on each worker
lc0 = spark.read.option('multiline','true') \
                .json('raw data/legislators-current.json')

lh0 = spark.read.option('multiline','true') \
                .json('raw data/legislators-historical.json')

# lc.printSchema()
# root
#  |-- bio: struct (nullable = true)
#  |    |-- birthday: string (nullable = true)
#  |    |-- gender: string (nullable = true)
#  |-- family: array (nullable = true)
#  |    |-- element: struct (containsNull = true)
#  |    |    |-- name: string (nullable = true)
#  |    |    |-- relation: string (nullable = true)
#  |-- id: struct (nullable = true)
#  |    |-- ballotpedia: string (nullable = true)
#  |    |-- bioguide: string (nullable = true)
#  |    |-- cspan: long (nullable = true)
#  |    |-- fec: array (nullable = true)
#  |    |    |-- element: string (containsNull = true)
#  |    |-- google_entity_id: string (nullable = true)
#  |    |-- govtrack: long (nullable = true)
#  |    |-- house_history: long (nullable = true)
#  |    |-- icpsr: long (nullable = true)
#  |    |-- lis: string (nullable = true)
#  |    |-- maplight: long (nullable = true)
#  |    |-- opensecrets: string (nullable = true)
#  |    |-- thomas: string (nullable = true)
#  |    |-- votesmart: long (nullable = true)
#  |    |-- wikidata: string (nullable = true)
#  |    |-- wikipedia: string (nullable = true)
#  |-- leadership_roles: array (nullable = true)
#  |    |-- element: struct (containsNull = true)
#  |    |    |-- chamber: string (nullable = true)
#  |    |    |-- end: string (nullable = true)
#  |    |    |-- start: string (nullable = true)
#  |    |    |-- title: string (nullable = true)
#  |-- name: struct (nullable = true)
#  |    |-- first: string (nullable = true)
#  |    |-- last: string (nullable = true)
#  |    |-- middle: string (nullable = true)
#  |    |-- nickname: string (nullable = true)
#  |    |-- official_full: string (nullable = true)
#  |    |-- suffix: string (nullable = true)
#  |-- other_names: array (nullable = true)
#  |    |-- element: struct (containsNull = true)
#  |    |    |-- last: string (nullable = true)
#  |-- terms: array (nullable = true)
#  |    |-- element: struct (containsNull = true)
#  |    |    |-- address: string (nullable = true)
#  |    |    |-- caucus: string (nullable = true)
#  |    |    |-- class: long (nullable = true)
#  |    |    |-- contact_form: string (nullable = true)
#  |    |    |-- district: long (nullable = true)
#  |    |    |-- end: string (nullable = true)
#  |    |    |-- end-type: string (nullable = true)
#  |    |    |-- fax: string (nullable = true)
#  |    |    |-- how: string (nullable = true)
#  |    |    |-- office: string (nullable = true)
#  |    |    |-- party: string (nullable = true)
#  |    |    |-- party_affiliations: array (nullable = true)
#  |    |    |    |-- element: struct (containsNull = true)
#  |    |    |    |    |-- end: string (nullable = true)
#  |    |    |    |    |-- party: string (nullable = true)
#  |    |    |    |    |-- start: string (nullable = true)
#  |    |    |-- phone: string (nullable = true)
#  |    |    |-- rss_url: string (nullable = true)
#  |    |    |-- start: string (nullable = true)
#  |    |    |-- state: string (nullable = true)
#  |    |    |-- state_rank: string (nullable = true)
#  |    |    |-- type: string (nullable = true)
#  |    |    |-- url: string (nullable = true)

# --- PARSING AND CLEANING!
lc = lc0.select(F.col('name.first').alias('name_first'), \
                F.col('name.last').alias('name_last'), \
                F.col('bio.gender').alias('gender'), \
                F.to_date('bio.birthday', format='yyyy-MM-dd').alias('birthday'), \
                F.explode('terms').alias('terms'))

lc = lc.withColumn('typeOfRep', lc.terms.type)
lc = lc.withColumn('party', lc.terms.party)
lc = lc.withColumn('url', lc.terms.url)
lc = lc.withColumn('abbr', lc.terms.state)
lc = lc.withColumn('dist', lc.terms.district)
lc = lc.withColumn('start', F.to_date(lc.terms.start, format='yyyy-MM-dd'))
lc = lc.withColumn('end', F.to_date(lc.terms.end, format='yyyy-MM-dd'))
lc = lc.drop('terms')

lh = lh0.select(F.col('name.first').alias('name_first'), \
                F.col('name.last').alias('name_last'), \
                F.col('bio.gender').alias('gender'), \
                F.to_date('bio.birthday', format='yyyy-MM-dd').alias('birthday'), \
                F.explode('terms').alias('terms'))

lh = lh.withColumn('typeOfRep', lh.terms.type)
lh = lh.withColumn('party', lh.terms.party)
lh = lh.withColumn('url', lh.terms.url)
lh = lh.withColumn('abbr', lh.terms.state)
lh = lh.withColumn('dist', lh.terms.district)
lh = lh.withColumn('start', F.to_date(lh.terms.start, format='yyyy-MM-dd'))
lh = lh.withColumn('end', F.to_date(lh.terms.end, format='yyyy-MM-dd'))
lh = lh.drop('terms')

# unify the 'current' and 'historical' data
ll = lc.union(lh)


# a bit more cleaning
ll = ll.withColumn('gender', F.when(ll.gender == 'F', 'female')
                              .when(ll.gender == 'M', 'male')
                              .otherwise('other'))
ll = ll.withColumn('typeOfRep', F.when(ll.typeOfRep == 'rep', 'House Representative')
                                 .when(ll.typeOfRep == 'sen', 'Senator')
                                 .otherwise('unknown'))


# create a row for every year between 'start' and 'end'
# so that the data can be plotted longitudinally
ll = ll.withColumn('time', F.datediff(ll.end, ll.start) / 365)
ll = ll.withColumn('time', F.round('time').cast('Integer'))

# UDF to create an array of integers, that we can then .explode()
def termYrs(time):
    return list(range(time))

udf_termYrs = F.udf(termYrs, ArrayType(IntegerType()))
ll = ll.withColumn('range', udf_termYrs(ll.time))
ll = ll.withColumn('yr', F.explode(ll.range))
ll = ll.withColumn('year', F.expr('date_add(start, yr*365)'))
ll = ll.withColumn('year', F.year('year'))
ll = ll.drop('range', 'yr', 'start', 'end', 'time')


# bring in the population data
ll = ll.join(congrPop, \
             (ll.abbr == congrPop.abbrev) & (ll.dist == congrPop.district), \
             how = 'leftouter')
ll = ll.drop('abbrev', 'district')

# bring in the income and tax data
ll = ll.join(income, \
             (ll.abbr == income.state_abbrev) & (ll.dist == income.district), \
             how = 'leftouter')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


# function to write table to cockroachDB
def writeTable(db, table0, tableName, saveMode="error"):
    # have to repartition the table b/c cockroachDB can't take too many rows
    # at a time, max is around 1000
    # https://forum.cockroachlabs.com/t/whats-the-best-way-to-do-bulk-insert/58
    # cluster   = 'jdbc:postgresql://10.0.0.17:26257/fedspend'
    table0.write \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", db) \
    .option("dbtable", tableName) \
    .option("user", "migrater") \
    .option("password", PASSWORD_STRING) \
    .save(mode=saveMode)



# another function to write joined table to cockroachDB,
# but writes in chunks
def writeSplits(table, tableName, numSplits=10):
    tempTable_split = table.randomSplit( [1.0] * numSplits )
    print("Split table " + tableName + " successfully.")

    # for every dataframe in the list...
    counter = 1
    for df in tempTable_split:
        # write the result to CDB
        print(tableName + ': writing chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout)
        writeTable(df, tableName, saveMode="append")
        print(tableName + ': wrote chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout)
        print("...giving CDB a short break.")
        time.sleep(10)
        counter += 1
