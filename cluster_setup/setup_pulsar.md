Installing a Pulsar cluster
=======

Installation guide at https://pulsar.apache.org/docs/v2.0.1-incubating/deployment/cluster/

VPC setup
----
The VPC setup consists of 3 node ZooKeeper ensemble at `10.0.0.4` to `10.0.0.6`

BookKeepers at `10.0.0.8` to `10.0.0.10`

and Pulsar brokers at `10.0.0.16` to `10.0.0.18` 

The initial minimal setup consists of one instance of for each and an AMI is also created for each node type.

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


**Increase Java heap size**

Here we increase the max heap size in Java to 800M
```
echo 'export _JAVA_OPTIONS="-Xms400m -Xmx800m"' >> ~/.bashrc
```
*Note that this is setup for t2.micro and should be increase for larger instance types!!!*

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
echo 'server.1=10.0.0.4:2888:3888' >> apache-zookeeper-3.5.5-bin/conf/zoo.cfg
sed -i 's/dataDir.*/dataDir=\/home\/ec2-user\/data\/zookeeper/g' apache-zookeeper-3.5.5-bin/conf/zoo.cfg
```

Setup the `myid` file in the data directory
```bash
echo 1 > /home/ec2-user/data/zookeeper/myid
```

**Configure Pulsar for ZooKeeper settings**

```bash
sed -i 's/dataDir.*/dataDir=\/home\/ec2-user\/data\/zookeeper/g' apache-pulsar-2.4.1/conf/zookeeper.conf
echo 'server.1=10.0.0.4:2888:3888' >> apache-pulsar-2.4.1/conf/zookeeper.conf
```

**Start ZooKeeper**
At this point, an image is created. Then the service is started **through pulsar** with 

```bash

```