#   HELPER FUNCTIONS AND OBJECTS FOR POSTGRESQL MIGRATION

from pyspark.sql import SparkSession 
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

# dynamically determine names of all tables in DB
tables = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", "information_schema.tables") \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .load() \
    .filter("table_schema = 'public' AND table_type='BASE TABLE'")

# dynamically determine name of PK in each table  
keys = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", "information_schema.key_column_usage") \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .load() 

# helper table to combine table names with their PK
constraints = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", "information_schema.table_constraints") \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .load()     


query = "(SELECT reltuples as approx_cnt, relname as table_name FROM pg_class) XXX"

# approximate the # of rows in each table
rowNum = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", query) \
    .option("user", "root") \
    .option("password", "RWwuvdj75Me4") \
    .load()

# register the above DataFrames as a SQL temporary view
tables.createOrReplaceTempView("tables")    
keys.createOrReplaceTempView("keys")
constraints.createOrReplaceTempView("constraints")
rowNum.createOrReplaceTempView("rowNum")


# join the individual pieces of information into one table
# (this listing assumes every table in the DB has a primary key)
pkeys = spark.sql("SELECT k.table_name, k.column_name as pkey, " + \
                  "r.approx_cnt as upper_bound " + \
                  "FROM keys as k " + \
                  "LEFT JOIN constraints as c " + \
                  "ON c.constraint_name = k.constraint_name " + \
                  "RIGHT JOIN tables as t " + \
                  "ON t.table_name = k.table_name " + \
                  "RIGHT JOIN rowNum as r " + \
                  "ON r.table_name = k.table_name " + \
                  "WHERE c.constraint_type = 'PRIMARY KEY'").collect()



# function to read a table from postgresql 
def readTable(tableName, pkey, rowNum, numPartitions):
    query = "(SELECT ROW_NUMBER() OVER(ORDER BY (SELECT NULL)) AS rno, * from " + \
            tableName + ") XXX"
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
        .option("lowerBound", 0).option("upperBound", rowNum) \
        .option("numPartitions", numPartitions) \
        .load() \
        .cache()
    except: 
        print("There's an issue with the partition process.", file=sys.stdout) 
        
    print("There are " + str(table0.rdd.getNumPartitions()) + " partitions " + \
          "across " + str(rowNum) + " rows.", file=sys.stdout) 

    return table0


# function to write a table to cockroachDB    
def writeTable(table0, tableName, saveMode="error"):
    # have to repartition the table b/c cockroachDB can't take too many rows
    # at a time, max is around 1000
    # https://forum.cockroachlabs.com/t/whats-the-best-way-to-do-bulk-insert/58
    cluster   = 'jdbc:postgresql://10.0.0.13:26257/fedspend'
    table0.write \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", cluster) \
    .option("dbtable", tableName) \
    .option("user", "migrater") \
    .option("password", "RWwuvdj75Me4") \
    .save(mode=saveMode)
