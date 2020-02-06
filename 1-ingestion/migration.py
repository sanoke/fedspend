# scp 1-ingestion/migration* ubuntu@$POSTGRES_PUBLIC_IP_DNS:~
# tmux set-option -g history-limit 5000 \; new-session
# tmux attach 
# time spark-submit --driver-memory 48g migration.py > spark-output.txt
# scp ubuntu@$POSTGRES_PUBLIC_IP_DNS:~/spark-output.txt .
# https://stackoverflow.com/questions/41085238/what-is-the-meaning-of-partitioncolumn-lowerbound-upperbound-numpartitions-pa

from migrationhelp import *

# 64 cores * 3 partitions per core + sauce
# (for reading data)
numPartitions = 200

# rows that CDB can take in one write (heuristic)
CDBrows = 10**6

numTables = len(pkeys)
  
# apply a set of functions to each table in the database
# (a list comprehension is potentially better here)
for idx in range(numTables):
    tab0   = pkeys[idx]["table_name"]
    pkey0  = pkeys[idx]["pkey"]
    upperB = int(pkeys[idx]["upper_bound"] * 1.10)

    tempTable = readTable(tab0, pkey0, upperB, numPartitions)

    # if it's one of the big tables (number of rows > 10**6), split it up so CDB can 
    # handle it... seems to put the entire DF into memory before storing
    if upperB > 1.5 * CDBrows:

        numSplits = round(upperB / CDBrows)
        tempTable_split = tempTable.randomSplit( [1.0] * numSplits )

        # for every dataframe in the list
        for df in tempTable_split:
            # write the table to CDB
            writeTable(df, tab0, saveMode="append")

    else:
        writeTable(tempTable, tab0)
    
    spark.catalog.clearCache()

    # try:
    #     num_rows = table0.count()
    # except:
    #     err = "There's an issue with running count() on the Dataframe " + tableName + "."
    #     print(err, file=sys.stdout) 
    # print("There are " + str(num_rows) + " rows in table *** " + tableName + " ***", file=sys.stdout)    