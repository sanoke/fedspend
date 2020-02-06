# - # - # - # - # - # - # - # - # - # - # - #
#
#   SETTING UP POSTGRESQL DATABASE
#   https://github.com/sanoke/fedspend/wiki/Setting-up:-PostgreSQL
#
# - # - # - # - # - # - # - # - # - # - # - #

ssh ubuntu@$POSTGRES_PUBLIC_IP_DNS

# - 0 - MOUNT ADDITIONAL VOLUME
# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html

# ----- hmmm... is the additional volume there? (no)
df -hT

# ----- view available disk devices and their mount points
lsblk

# ----- determine whether there's a file system on the volume (no)
sudo file -s /dev/nvme0n1

# ----- create a file system
sudo mkfs -t xfs /dev/nvme0n1

# ----- create a mount point directory
sudo mkdir /database

# ----- mount the volume at this new directory
sudo mount /dev/nvme0n1 /database

# ----- check that everything is correct
df -hT


# - 1 - INSTALL POSTGRESQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# ----- create a user 'root'
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


# - 2 - CONFIGURE POSTGRESQL TO STORE DATABASE IN ADDITIONAL VOL
#       (not the root volume)

# ----- change owner of mount point
sudo chown -R postgres:postgres /database
sudo -u postgres /usr/lib/postgresql/10/bin/initdb -D /database

# ----- turn off postgresql so we can configure it
sudo service postgresql stop

sudo nano /etc/postgresql/10/main/postgresql.conf
# MODIFIED CONFIGURATIONS
# data_directory = ‘/database’
# shared_buffers = 16GB                 # 25% of 64GB mem available
# max_worker_processes = 16             # 16 vCPUs on this machine
# max_parallel_workers_per_gather = 16  # max
# max_parallel_workers = 16
# effective_cache_size = 48GB           # 75% of 64GB mem available
# listen_addresses = '*'                # so other machines can talk to the DB
# advice on configs:
# https://www.postgresql.org/docs/9.5/runtime-config-query.html
# https://dev.to/pythonmeister/basic-postgresql-tuning-parameters-281
# https://www.2ndquadrant.com/en/blog/postgresql96-parallel-sequential-scan/
# https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server

# authenticate Spark workers by specifying private IPs
# with auth-method `trust`
# https://www.postgresql.org/docs/10/auth-pg-hba-conf.html
sudo nano /etc/postgresql/10/main/pg_hba.conf


# ----- turn postgresql back on
sudo service postgresql start