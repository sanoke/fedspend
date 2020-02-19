[GitHub] Airflow implementation

# Apache Airflow 
## Implementation notes

In the three short weeks we had to design and implement this project, I was not able to integrate [Apache Airflow](http://airflow.apache.org), a functionality that would automate monthly updates on US spending data. However this implementation note discusses my thought process around what the implementation would look like. 

-------

Every month, the Department of the Treasury posts a PostgreSQL dump of their entire federal spending database. The goal of this Airflow workflow would be to automate monthly updates to FedSpend based on updates to the source data. 

### Step 1 of 3: Version control
The Treasury posts monthly updates but not on a fixed date. Thus, Airflow will use a regular expression to construct and test the anticipated URL of the database dump. For example, the URL of the February 2020 dump was 
```
https://files.usaspending.gov/database_download/usaspending-db_20200205.zip
```
...so Airflow will take the current month (`mm`) and year (`yyyy`) and test URLs of the form
```
"https://files.usaspending.gov/database_download/usaspending-db_" + \
  yyyy + mm + re.compile("(0[1-9]|[12][0-9]|3[01])") + ".zip"
```
where `re.compile()` is a function from the [`re`](https://docs.python.org/3.7/howto/regex.html) package. 
Once the dump has been downloaded, the two most important tables - `transaction_fpds` containing contract award data and `transaction_fabs` containing grant award data - will be extracted and partitioned to run the [version control procedure](https://github.com/sanoke/fedspend/blob/master/2-data-processing/version_control.md). 
￼
![](https://github.com/sanoke/fedspend/raw/master/img/airflow1.png)

### Step 2 of 3: Append new data
Next, the new data will be selected out of these two tables and appended to our existing tables.

![](https://github.com/sanoke/fedspend/raw/master/img/airflow2.png)
￼

### Step 3 of 3: New agg tables
Finally, new aggregation tables will be calculated and appended to the existing tables, but distinguished with a `snapshot_date`. Aggregations are recalculated in their entirety and not appended because their values depend on contents from the entire table. 
￼
![](https://github.com/sanoke/fedspend/raw/master/img/airflow3.png)
