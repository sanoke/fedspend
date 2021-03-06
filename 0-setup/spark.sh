# - # - # - # - # - # - # - # - # - # - # - #
#
#   SETTING UP SPARK CLUSTER
#   https://github.com/sanoke/fedspend/wiki/Setting-up:-Spark-cluster
#
# - # - # - # - # - # - # - # - # - # - # - #

# - 1 - Add instances to cluster security group


# - 2 - SET UP THE MASTER NODE
ssh ubuntu@$POSTGRES_PUBLIC_IP_DNS

# ----- install Java 8 and Scala
sudo apt update
sudo apt install openjdk-8-jre-headless
# confirm the version
java -version

sudo apt install scala
scala -version

# ----- setup keyless SSH
sudo apt install openssh-server openssh-client
# create an RSA key pair
cd ~/.ssh
ssh-keygen -t rsa -P ""
# ...when asked for a file name, enter: id_rsa

# ----- install Spark 2.4.4
wget http://apache.claz.org/spark/spark-2.4.4/spark-2.4.4-bin-hadoop2.7.tgz
tar xvf spark-2.4.4-bin-hadoop2.7.tgz
sudo mv spark-2.4.4-bin-hadoop2.7/ /usr/local/spark

# edit the file `~/.bash_profile` 
sudo nano ~/.bash_profile
# ...and add the following: 
export PATH=/usr/local/spark/bin:$PATH
# load the new configuration
source ~/.bash_profile


# - 3 - CREATE A WORKER NODE
#       (below process is repeated for each node)

# ----- install Java 8 and Scala
sudo apt update
sudo apt install openjdk-8-jre-headless
sudo apt install scala

# ----- complete setup of keyless SSH
#       manually copy contents of `~/.ssh/id_rsa.pub` on the master to
#       `~/.ssh/authorized_keys` file in each worker

# test connection by using master to SSH into worker
ssh -i ~/.ssh/id_rsa ubuntu@$SPARK_NODE1_PRIVATE_IP

# ----- install Spark 2.4.4
wget http://apache.claz.org/spark/spark-2.4.4/spark-2.4.4-bin-hadoop2.7.tgz
tar xvf spark-2.4.4-bin-hadoop2.7.tgz
sudo mv spark-2.4.4-bin-hadoop2.7/ /usr/local/spark

# edit the file `~/.bash_profile` 
sudo nano ~/.bash_profile
# ...and add the following: 
export PATH=/usr/local/spark/bin:$PATH
# load the new configuration
source ~/.bash_profile


# - 4 - CONFIGURE MASTER TO TRACK WORKERS
cp /usr/local/spark/conf/spark-env.sh.template /usr/local/spark/conf/spark-env.sh
sudo nano /usr/local/spark/conf/spark-env.sh
# ----- add the following commands to conf/spark-env.sh
export SPARK_MASTER_HOST=$SPARK_MASTER_PRIVATE_IP
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre
export PYSPARK_PYTHON=/usr/bin/python3
export PYSPARK_DRIVER_PYTHON=/usr/bin/python3

# ----- configure the logger to only output warnings 
#       (rather than everything)
cp /usr/local/spark/conf/log4j.properties.template /usr/local/spark/conf/log4j.properties
sudo nano /usr/local/spark/conf/log4j.properties
# replace the line 
# log4j.rootCategory=INFO, console
# with 
# log4j.rootCategory=INFO, console
# https://stackoverflow.com/questions/25193488/how-to-turn-off-info-logging-in-spark


# ----- specify the private IPs of the worker nodes, 
# ----- by listing them within `/usr/local/spark/conf/slaves`


# - 5 - START THE CLUSTER
sh /usr/local/spark/sbin/start-all.sh