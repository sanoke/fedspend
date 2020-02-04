# - # - # - # - # - # - # - # - # - # - # - #
#
#   CONNECTING SPARK TO DATABASES
#   https://github.com/sanoke/fedspend/wiki/Setting-up:-Connecting-to-Spark
#
# - # - # - # - # - # - # - # - # - # - # - #

ssh ubuntu@$POSTGRES_PUBLIC_IP_DNS

# - 1 - DOWNLOAD JDBC TO CONNECT TO POSTGRES (all nodes and master)
wget https://jdbc.postgresql.org/download/postgresql-42.2.6.jar
sudo mv postgresql-42.2.6.jar /usr/local/spark/jars

scp 1-ingestion/migration.py ubuntu@$POSTGRES_PUBLIC_IP_DNS:~

time spark-submit --driver-memory 48g migration.py > spark-output.txt


# CONNECTING TO COCKROACHDB
# uses the same postgres driver
# (to all spark machines)
sudo apt install python3-pip
pip3 install psycopg2-binary # in production install psycopg2
# [TO DO]