# - # - # - # - # - # - # - # - # - # - # - #
#
#   SETTING UP SPARK CLUSTER
#   https://github.com/sanoke/fedspend/wiki/Data-pipeline:-Ingesting-data
#
# - # - # - # - # - # - # - # - # - # - # - #

# - 1 - DOWNLOAD ARCHIVE DUMP FILE FROM S3
# ----- log into the root account
sudo -u root -i
https://sanoke-insight-fedspend-projectdata.s3-us-west-2.amazonaws.com/usaspending-db_20200110.zip
sudo apt install awscli
aws configure
# a prompt will appear;
# enter the keys that were generated when IAM profile was first created 

# ----- so we can run the restore process in the background
#     - detach with CTRL+B D
#     - reattach with tmux attach -t pg-restore
#     - close completely with CTRL+D
tmux new -s pg-restore

# ----- download the archive file and unzip it
cd /database 
aws s3 cp s3://sanoke-insight-fedspend-projectdata/usaspending-db_20200110.zip usaspending-db_20200110.zip
sudo apt install unzip
unzip usaspending-db_20200110.zip -d usaspending-db_20200110


# - 2 - RESTORE AND INSPECT THE DATABASE
# ----- after we configured the database location in postgresql.conf, the 
# ----- record of the root user was lost, so we'lll recreate it
sudo -u postgres createuser root
sudo -u postgres createdb root

# ----- start psql to grant the privleges
sudo -u postgres psql
# or 
sudo -u postgres /usr/bin/psql

# ----- add SUPERUSER privleges 
# (sql) ALTER USER root WITH ENCRYPTED PASSWORD '<enter-password>';
# (sql) GRANT ALL PRIVILEGES ON DATABASE root TO root;
# (sql) ALTER USER root WITH SUPERUSER CREATEDB CREATEROLE;

# ----- now to restore the database
pg_restore --list usaspending-db_20200110 | sed '/MATERIALIZED VIEW DATA/D' > restore.list
# ----- the step below takes 5.3 hours to complete 
pg_restore --jobs 16 --dbname postgresql://root:'<enter-password>'@localhost:5432/root --verbose --exit-on-error --use-list restore.list usaspending-db_20200110

# view a list of our restored tables
psql --dbname postgresql://root:'<enter-password>'@localhost:5432/root --command 'ANALYZE VERBOSE;' --echo-all --set ON_ERROR_STOP=on --set VERBOSITY=verbose --set SHOW_CONTEXT=always
pg_restore --list usaspending-db_20200110 | grep "MATERIALIZED VIEW DATA" > refresh.list