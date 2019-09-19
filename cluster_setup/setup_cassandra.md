Setting up a Cassandra cluster
======

*Note we intend to place Cassandra nodes in the IP range `10.0.0.29` to `10.0.0.31`*


Install Java 8
----

```bash
sudo yum install -y java-1.8.0-openjdk

java -version
```
> openjdk version "1.8.0_222"
OpenJDK Runtime Environment (build 1.8.0_222-b10)
OpenJDK 64-Bit Server VM (build 25.222-b10, mixed mode)

```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.222.b10-0.amzn2.0.1.x86_64/jre' >> ~/.bashrcecho '' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

Download and install Cassandra
----
Download and uncompress the tar ball
```bash
http://mirrors.gigenet.com/apache/cassandra/3.11.4/apache-cassandra-3.11.4-bin.tar.gz

tar -xzf apache-cassandra-3.11.4-bin.tar.gz

rm apache-cassandra-3.11.4-bin.tar.gz
```

Modify `cd apache-cassandra-3.11.3/conf/cassandra.yaml` file to set 

* `cluster_name`: Name of the cluster
* `listen_address`: Private IP
* `rpc_address`: Private IP
* `seed_provider`: Add the list IPs of all the nodes in the `seeds` block.
* `endpoint_snitch`: Ec2Snitch

Them comment out the settings in `cassandra-rackdc.properties`
*(This means no special datacenter and rack configurations)*

Start Cassandra
------
```bash
/usr/ec2-user/apache-cassandra-3.11.3/bin/cassandra
```

