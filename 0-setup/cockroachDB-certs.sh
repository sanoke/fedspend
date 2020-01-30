# - # - # - # - # - # - # - # - # - # - # - #
#
#   SETTING UP COCKROACHDB CLUSTER: Certificates
#   (4 nodes)
#   github.com/sanoke/fedspend/wiki/Setting-up:-CockroachDB
#
# - # - # - # - # - # - # - # - # - # - # - #

# - 1 - Install CockroachDB on local machine

# - 2 - Launch the 4 cluster instances

# - 3 - Create a cluster security group and add the instances 

# - 4 - Set up time sync on each node 

# - 5 - Set up load balancing

# - 6 - GENERATE CERTIFICATES AND KEYS FOR EACH NODE (run locally)

mkdir cockroach/certs
mkdir cockroach/my-safe-directory
cockroach cert create-ca --certs-dir=cockroach/certs --ca-key=cockroach/my-safe-directory/ca.key

# - 6.1 certificates for node 1
cockroach cert create-node \
  $CDB_NODE1_PRIVATE_IP \
  $CDB_NODE1_PRIVATE_IP_DNS \
  localhost \
  127.0.0.1 \
  $CDB_BALANCER_PRIVATE_IP \
  --certs-dir=cockroach/certs \
  --ca-key=cockroach/my-safe-directory/ca.key
ssh ubuntu@$CDB_NODE1_PUBLIC_IP_DNS "mkdir certs"
scp cockroach/certs/ca.crt cockroach/certs/node.crt cockroach/certs/node.key ubuntu@$CDB_NODE1_PUBLIC_IP_DNS:~/certs
rm cockroach/certs/node.crt cockroach/certs/node.key  

# 6.2 certificates for node 2  
cockroach cert create-node \
  $CDB_NODE2_PRIVATE_IP \
  $CDB_NODE2_PRIVATE_IP_DNS \
  localhost \
  127.0.0.1 \
  $CDB_BALANCER_PRIVATE_IP \
  --certs-dir=cockroach/certs \
  --ca-key=cockroach/my-safe-directory/ca.key
ssh ubuntu@$CDB_NODE2_PUBLIC_IP_DNS "mkdir certs"
scp cockroach/certs/ca.crt cockroach/certs/node.crt cockroach/certs/node.key ubuntu@$CDB_NODE2_PUBLIC_IP_DNS:~/certs
rm cockroach/certs/node.crt cockroach/certs/node.key    

# 6.3 certificates for node 3
cockroach cert create-node \
  $CDB_NODE3_PRIVATE_IP \
  $CDB_NODE3_PRIVATE_IP_DNS \
  localhost \
  127.0.0.1 \
  $CDB_BALANCER_PRIVATE_IP \
  --certs-dir=cockroach/certs \
  --ca-key=cockroach/my-safe-directory/ca.key
ssh ubuntu@$CDB_NODE3_PUBLIC_IP_DNS "mkdir certs"
scp cockroach/certs/ca.crt cockroach/certs/node.crt cockroach/certs/node.key ubuntu@$CDB_NODE3_PUBLIC_IP_DNS:~/certs
rm cockroach/certs/node.crt cockroach/certs/node.key    

# 6.3 certificates for node 4
cockroach cert create-node \
  $CDB_NODE4_PRIVATE_IP \
  $CDB_NODE4_PRIVATE_IP_DNS \
  localhost \
  127.0.0.1 \
  $CDB_BALANCER_PRIVATE_IP \
  --certs-dir=cockroach/certs \
  --ca-key=cockroach/my-safe-directory/ca.key
ssh ubuntu@$CDB_NODE4_PUBLIC_IP_DNS "mkdir certs"
scp cockroach/certs/ca.crt cockroach/certs/node.crt cockroach/certs/node.key ubuntu@$CDB_NODE4_PUBLIC_IP_DNS:~/certs
rm cockroach/certs/node.crt cockroach/certs/node.key    

# 6.5 create client certificate and key for the root user
cockroach cert create-client \
root \
--certs-dir=cockroach/certs \
--ca-key=cockroach/my-safe-directory/ca.key

# --- upload the CA certificate and client certificate and key 
# ---   to the machine where you will run a sample workload (web UI machine)
ssh ubuntu@$WEBUI_PUBLIC_IP_DNS "mkdir certs"
scp cockroach/certs/ca.crt \
  cockroach/certs/client.root.crt \
  cockroach/certs/client.root.key \
  ubuntu@$WEBUI_PUBLIC_IP_DNS:~/certs