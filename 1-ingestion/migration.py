# scp 1-ingestion/migration.py ubuntu@$POSTGRES_PUBLIC_IP_DNS:~
# tmux set-option -g history-limit 5000 \; new-session
# tmux attach 
# time spark-submit --driver-memory 48g migration.py > output.txt

from pyspark.sql import SparkSession 
import sys

CDB_clusters = ['10.0.0.4', '10.0.0.6', '10.0.0.24', '10.0.0.23']

# hardcoding isn't a great idea, but it is 
# not easy to determine a table size in Spark
# table sizes were calculated independently in PostgreSQL
# --- small tables are 150MB-1GB
# --- medium tables are 1-10GB
# --- large tables are 10GB+
# --- tiny tables everything else
# --- 60 tables total, < 64MB chunks
smallTab = ['duns', 'recipient_lookup', 'historic_parent_duns',
            'tas_program_activity_object_class_quarterly', 
            'financial_accounts_by_program_activity_object_class']
medTab = ['financial_accounts_by_awards', 'subaward',
          'broker_subaward', 'summary_award_recipient',
          'temp_dev3319_transactions_with_diff', ]
largeTab = ['transaction_fabs', 'transaction_normalized',
            'awards', 'legal_entity', 'transaction_fpds',
            'references_location', ]
  
def migrate(tableName, clusterIP):
    if tableName in smallTab:
        chunkSize = 100
    elif tableName in medTab:
        chunkSize = 1000
    elif tableName in largeTab:
        chunkSize = 11000
    else:
        chunkSize = 1

    table0 = spark.read \
        .format("jdbc") \
        .option("driver", "org.postgresql.Driver") \
        .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
        .option("dbtable", tableName) \
        .option("user", "root") \
        .option("password", "RWwuvdj75Me4") \
        .load() \
        .repartition(chunkSize)
    
    num_rows = table0.count()
    print(tableName, file=sys.stdout)
    print("There are " + str(num_rows) + " rows in table *** " + tableName + " ***", file=sys.stdout)

    print(table0.rdd.getNumPartitions(), file=sys.stdout) 
    # clusterIP = 'cockroachDB-balancer-4fdf4e82f5f5453f.elb.us-west-2.amazonaws.com'
    cluster   = 'jdbc:postgresql://' + clusterIP + ':26257/fedspend'    
    # cluster   = clusterIP + ':26257/fedspend'

    table0.write \
        .format("jdbc") \
        .option("driver", "org.postgresql.Driver") \
        .option("url", cluster) \
        .option("dbtable", tableName) \
        .option("user", "migrater") \
        .option("password", "RWwuvdj75Me4") \
        .save()
    print(tableName + '_M', file=sys.stdout)


# - # - # - # - # - # - # - # - # - # - # - # 

spark = SparkSession \
    .builder \
    .appName("Migration from PostgreSQL to CockroachDB") \
    .master("spark://10.0.0.10:7077") \
    .config("spark.jars", "/usr/local/spark/jars/postgresql-42.2.6.jar") \
    .config('spark.executor.memory', '13g') \
    .config('spark.executor.cores', '4') \
    .config('spark.driver.cores','12') \
    .config('spark.default.parallelism', '100') \
    .config('spark.history.retainedApplications', '10') \
    .config('spark.network.timeout', '300s') \
    .config('spark.executor.heartbeatInterval', '20s') \
    .getOrCreate()

print(spark.sparkContext.getConf().getAll())

tableNames0 = spark.read \
    .format("jdbc") \
    .option("driver", "org.postgresql.Driver") \
    .option("url", 'jdbc:postgresql://10.0.0.10:5432/root') \
    .option("dbtable", "information_schema.tables") \
    .option("user", "root") \
    .option("password", "<enter-password>") \
    .load() \
    .filter("table_schema = 'public' AND table_type='BASE TABLE'") \
    .select('table_name').collect()    

# for loop not the best idea, with more time
# i'd try a list comprehension
tabNames = [tableNames0[t]["table_name"] for t in range(len(tableNames0))]

tabNames.insert(0, tabNames.pop(mylist.index('references_location')))

clusterIPs = [CDB_clusters[idx%4] for idx in range(len(tableNames0))]

tabANDcluster = list(zip(tabNames, clusterIPs))

print(tabANDcluster)

# print(tabNames)

migratedTables = [migrate(item[0], item[1]) for item in tabANDcluster]
# migratedTables = [migrate(table) for table in tabNames]