# scp 1-ingestion/migration* ubuntu@$POSTGRES_PUBLIC_IP_DNS:~
# tmux set-option -g history-limit 5000 \; new-session
# tmux attach 
# time spark-submit --driver-memory 48g migration.py > spark-output.txt
# scp ubuntu@ec2-44-230-69-206.us-west-2.compute.amazonaws.com:~/spark-output.txt .
# https://stackoverflow.com/questions/41085238/what-is-the-meaning-of-partitioncolumn-lowerbound-upperbound-numpartitions-pa

from migrationhelp import *

CDB_clusters = ['10.0.0.4', '10.0.0.6', '10.0.0.24', '10.0.0.23']

# 64 cores * 3 partitions per core + sauce
numPartitions = 200 

numTables = len(pkeys)
clusterIPs = [CDB_clusters[idx%4] for idx in range(numTables)]
  
# apply a set of functions to each table in the database
# (a list comprehension is potentially better here)
for idx in range(numTables):
    tab0   = pkeys[idx]["table_name"]
    pkey0  = pkeys[idx]["pkey"]
    upperB = int(pkeys[idx]["upper_bound"] * 1.10)

    tempTable = readTable(tab0, pkey0, upperB, numPartitions)

    writeTable(tempTable, tab0, clusterIPs[idx])
    
    spark.catalog.clearCache()