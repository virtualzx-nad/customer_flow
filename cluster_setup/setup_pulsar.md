Installing a Pulsar cluster
=======

Installation guide at https://pulsar.apache.org/docs/v2.0.1-incubating/deployment/cluster/

VPC setup
----
The VPC setup consists of 3 node ZooKeeper ensemble at `10.0.0.4` to `10.0.0.6`

BookKeepers at `10.0.0.8` to `10.0.0.10`

and Pulsar brokers at `10.0.0.16` to `10.0.0.18` 

The initial minimal setup consists of one instance of for each and an AMI is also created for each node type.

*location of other nodes: Redis `10.0.0.24` to `10.0.0.26`,  
Cassandra `10.0.0.29` to `10.0.0.31`  
and workers `10.0.0.36` and beyond *
Install Pulsar binary
----

For each node, we need to install Pulsar

```bash
wget 'https://www.apache.org/dyn/mirrors/mirrors.cgi?action=download&filename=pulsar/pulsar-2.4.1/apache-pulsar-2.4.1-bin.tar.gz' -O apache-pulsar-2.4.1-bin.tar.gz

tar -xzf apache-pulsar-2.4.1-bin.tar.gz

rm apache-pulsar-2.4.1-bin.tar.gz

```


Setup Zookeeper cluster
----

Create a Amazon Linux2 t2.micro instance and log into the machine.  Install Pulsar binary.  Finally, install ZooKeeper following `https://zookeeper.apache.org/doc/r3.4.10/zookeeperAdmin.html#sc_zkMulitServerSetup`


**Install Java 8**

```bash
sudo yum install -y java-1.8.0-openjdk

java -version
```
> openjdk version "1.8.0_222"
OpenJDK Runtime Environment (build 1.8.0_222-b10)
OpenJDK 64-Bit Server VM (build 25.222-b10, mixed mode)


**Set Java heap size**

Here we set the max heap size in Java to 800M to accomodate a t2.micro instance
```
echo 'export _JAVA_OPTIONS="-Xms400m -Xmx800m"' >> ~/.bashrc
```
*Note that this should be increase for larger instance types!!!*

**Install ZooKeeper**

```bash
wget http://mirror.cogentco.com/pub/apache/zookeeper/zookeeper-3.5.5/apache-zookeeper-3.5.5-bin.tar.gz

tar -xzf apache-zookeeper-3.5.5-bin.tar.gz

rm apache-zookeeper-3.5.5-bin.tar.gz
```

**Configure ZooKeeper**


Note: the below example setup only one node.  The host list and `myid` will need to be changed correspondingly for a larger ensemble. 

Create the data directory
```bash
mkdir /home/ec2-user/data
mkdir /home/ec2-user/data/zookeeper
```

Add the node IP to the config file and set the path to the data directory

```bash
cp apache-zookeeper-3.5.5-bin/conf/zoo_sample.cfg apache-zookeeper-3.5.5-bin/conf/zoo.cfg
echo 'server.1=10.0.0.4:2888:3888' >> /home/ec2-user/apache-zookeeper-3.5.5-bin/conf/zoo.cfg
sed -i 's/dataDir.*/dataDir=\/home\/ec2-user\/data\/zookeeper/g' /home/ec2-user/apache-zookeeper-3.5.5-bin/conf/zoo.cfg
```

Setup the `myid` file in the data directory
```bash
echo 1 > /home/ec2-user/data/zookeeper/myid
```

Add these environmental variables in `~/.bashrc`

```
export ZOOCFGDIR=/home/ec2-user/apache-zookeeper-3.5.5-bin/conf
export ZOOBINDIR=/home/ec2-user/apache-zookeeper-3.5.5-bin/bin
```
**Configure Pulsar for ZooKeeper settings**

```bash
sed -i 's/dataDir.*/dataDir=\/home\/ec2-user\/data\/zookeeper/g' /home/ec2-user/apache-pulsar-2.4.1/conf/zookeeper.conf
echo 'server.1=10.0.0.4:2888:3888' >> /home/ec2-user/apache-pulsar-2.4.1/conf/zookeeper.conf
```

**Start ZooKeeper**
At this point, an image is created. Then the service is started **through pulsar** with 

```bash
/home/ec2-user/apache-pulsar-2.4.1/bin/pulsar-daemon start zookeeper

```

*Note to start ZooKeeper as standalone you can do*
```bash
bash /home/ec2-user/apache-zookeeper-3.5.5-bin/bin/zkServer.sh  start
```

Now start the cluster **once**.

```bash
/home/ec2-user/apache-pulsar-2.4.1/bin/pulsar initialize-cluster-metadata \
  --cluster insight-XZ-pulsar-cluster \
  --zookeeper 10.0.0.4:2181 \
  --configuration-store 10.0.0.4:2181 \
  --web-service-url http://<public-DNS>:8080 \
  --web-service-url-tls https://<public-DNS>:8443 \
  --broker-service-url pulsar://<public-DNS>:6650 \
  --broker-service-url-tls pulsar+ssl://<public-DNS>:6651
```



Setup BookKeeper cluster
----

**Install BookKeeper**
```bash
wget https://archive.apache.org/dist/bookkeeper/bookkeeper-4.8.2/bookkeeper-server-4.8.2-bin.tar.gz

tar -xzf bookkeeper-server-4.8.2-bin.tar.gz

rm bookkeeper-server-4.8.2-bin.tar.gz
```

**Install Java**
```bash
sudo yum install -y java-1.8.0-openjdk

java -version
```

>openjdk version "1.8.0_222"
OpenJDK Runtime Environment (build 1.8.0_222-b10)
OpenJDK 64-Bit Server VM (build 25.222-b10, mixed mode)

```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.222.b10-0.amzn2.0.1.x86_64/jre' >> ~/.bashrc

echo 'export _JAVA_OPTIONS="-Xms400m -Xmx800m"' >> ~/.bashrc
```
*Note the heap size should be increased for any instance type larger than t2.micro!!!*

**Configure BookKeeper to find ZooKeeper servers**

This may or may not be needed but i did it anyways
```bash
sed -i 's/dataDir.*/dataDir=\/home\/ec2-user\/data\/zookeeper/g' /home/ec2-user/bookkeeper-server-4.8.2/conf/zookeeper.conf

sed -i 's/dataLogDir.*/dataDir=\/home\/ec2-user\/data\/zookeeper\/txlog/g' /home/ec2-user/bookkeeper-server-4.8.2/conf/zookeeper.conf
```

**Configure Pulsar settings**

In addition to setting up ZooKeeper setting in Pulsar same as last section (not 100% if necessary), configure Pulsar setting for BookKeepers.
```bash
sed -i 's/zkServers.*/zkServers=10.0.0.4:2181/g' /home/ec2-user/apache-pulsar-2.4.1/conf/bookkeeper.conf
```

Setup Pulsar Broker
----


Set the broker configuration file (`/home/ec2-user/apache-pulsar-2.4.1/conf/broker.conf`) to include the following settings

```
zookeeperServers=10.0.0.4:2181
configurationStoreServers=10.0.0.4:2181
clusterName=insight-XZ-pulsar-cluster
```

Then start the Pulsar broker

```bash
/home/ec2-user/apache-pulsar-2.4.1/bin/pulsar-daemon start broker
```