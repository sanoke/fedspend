# Version control
## Implementation notes

In the three short weeks we had to design and implement this project, I was not able to include a version control procedure, that would accommodate monthly updates on US spending data. However this implementation note discusses my thought process around what version control would look like. 

-------

Every month, the Department of the Treasury posts a PostgreSQL dump of their entire federal spending database. Consider the dump posted in January 2020, on which the FedSpend app is based (yellow in _posted Jan 2020_). **Say we want to update our app with data from the February 2020 dump.**

![](https://github.com/sanoke/fedspend/raw/master/img/data.png)
￼

The **naïve way** to update our database would be to overwrite it with the new dump posted.

The **better way** is to extract the new data (green) and append it to our existing database. While we hope the carryover data in the new dump (yellow in _posted Feb 2020_) is the same as the data from the prior dump (yellow in _posted Jan 2020_), a *version control* procedure would allow us to make an evidence-based statement on this similarity. 

### [Idea 1] Compare versions with joins :weary:
We'd need to join about 200 million rows on an alphanumeric key (the contract / grant award number) and timestamp, then compare values (e.g., contract amounts) between the two tables. Such a process is very time- and resource-heavy. 

### [Idea 2] Compare versions with a hash function
More time- and resource-efficient is the application of a hash function to the column containing the transaction amounts. In particular we can use [MurmurHash3](https://en.wikipedia.org/wiki/MurmurHash) via the `hash()` function in Spark SQL. We can then compare the hash value between the old data (yellow in _posted Jan 2020_) and the new data (yellow in _posted Feb 2020_) to determine whether there's been a change. The drawback is that this procedure will tell us whether there's been a change, but not where. 
