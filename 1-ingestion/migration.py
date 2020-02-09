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

CDBrows = 10**6

numTables = len(pkeys)

# apply a set of functions to each table in the database
# (a list comprehension is potentially better here)
for idx in range(numTables):
    tab0   = pkeys[idx]["table_name"]

    # tables not being migrated for one reason or another
    # (debugging)
    skip_tables = ['transaction_fabs', 'legal_entity', 'financial_accounts_by_awards',
                   'temp_dev3319_transactions_with_diff', 'references_location', 
                   'django_migrations', 'filter_hash', 'django_session', 
                   'rosetta', 'tas_program_activity_object_class_quarterly',
                   'auth_group', 'agency', 'appropriation_account_balances',
                   'ref_city_county_code', 'transaction_delta', 'frec_map']
    select_tables = ['state_data','overall_totals']
    if tab0 not in select_tables:
        print("Skipped table " + tab0)
        continue

    pkey0  = pkeys[idx]["pkey"]
    upperB = int(pkeys[idx]["upper_bound"] * 1.10)

    tempTable = readTable(tab0, pkey0, upperB, numPartitions)

    print("Read in table " + tab0 + " successfully.")

    # if it's one of the big tables (number of rows > 10**6), split it up so CDB can 
    # handle it... seems to put the entire DF into memory before storing
    if upperB > 1.5 * CDBrows:

        numSplits = round( upperB / CDBrows )
        tempTable_split = tempTable.randomSplit( [1.0] * numSplits )

        print("Split table " + tab0 + " successfully.")

        # for every dataframe in the list
        counter = 1
        for df in tempTable_split:
            # write the table to CDB
            print(tab0 + ': trying to write chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout) 
            splitSize = df.count()
            print(tab0 + ' chunk ' + str(counter) + ' of ' + str(numSplits) + ' has ' + str(splitSize) + ' rows to write', file=sys.stdout) 
            writeTable(df, tab0, saveMode="append")
            print(tab0 + ': wrote chunk ' + str(counter) + ' of ' + str(numSplits), file=sys.stdout) 
            counter += 1
            

    else:
        writeTable(tempTable, tab0)
        print(tab0 + ': chunk 1 of 1', file=sys.stdout) 
    
    spark.catalog.clearCache()

    # try:
    #     num_rows = table0.count()
    # except:
    #     err = "There's an issue with running count() on the Dataframe " + tableName + "."
    #     print(err, file=sys.stdout) 
    # print("There are " + str(num_rows) + " rows in table *** " + tableName + " ***", file=sys.stdout)    