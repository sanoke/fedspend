# - # - # - # - # - # - # - # - # - # - # - #
#
#   SETTING UP SPARK CLUSTER
#   https://github.com/sanoke/fedspend/wiki/Setting-up:-Spark-cluster
#
# - # - # - # - # - # - # - # - # - # - # - #

# - 1 - Add instances to cluster security group

# - 2 - SET UP THE MASTER NODE
ssh ubuntu@$SPARK_MASTER_PUBLIC_IP_DNS

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

# edit the file `~/.bash_profile` and add the following text: 
# export PATH=/usr/local/spark/bin:$PATH

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
#       ~/.ssh/authorized_keys file in each worker

# test connection by using master to SSH into worker
ssh -i ~/.ssh/id_rsa ubuntu@$NODE1_PRIVATE_IP

# ----- install Spark 2.4.4
wget http://apache.claz.org/spark/spark-2.4.4/spark-2.4.4-bin-hadoop2.7.tgz
tar xvf spark-2.4.4-bin-hadoop2.7.tgz
sudo mv spark-2.4.4-bin-hadoop2.7/ /usr/local/spark

# edit the file `~/.bash_profile` and add the following text: 
# export PATH=/usr/local/spark/bin:$PATH

# load the new configuration
source ~/.bash_profile


# - 4 - CONFIGURE MASTER TO TRACK WORKERS
cp /usr/local/spark/conf/spark-env.sh.template /usr/local/spark/conf/spark-env.sh
# ----- add the following commands to conf/spark-env.sh
# export SPARK_MASTER_HOST=10.0.0.26
# export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre


# - 5 - START THE CLUSTER
sh /usr/local/spark/sbin/start-all.sh