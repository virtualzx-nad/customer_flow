Setting up a Redis cluster
========

Install gcc compiler
----
```bash
sudo yum -y update
sudo yum install -y gcc
```

Download and compile Redis
----
```bash
curl -O http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
rm redis-stable.tar.gz

cd redis-stable
sudo make distclean
sudo make
```
>...  
>...  
INSTALL redis-check-aof  
Hint: It's a good idea to run 'make test' ;)  
make[1]: Leaving directory `/home/ec2-user/redis-stable/src'

Optional: test the installation as suggested.
```bash
sudo yum install -y tcl
sudo make test
```
*Note: First time it didn't work and gave an error message `READONLY You can't write against a read only replica`.  But ran the tests a second time the test passes.  It is not clear why.*

>\o/ All tests passed without errors!  
Cleanup: may take some time... OK  
make[1]: Leaving directory `/home/ec2-user/redis-stable/src'


Install and configure Redis
----
Copy the executable files to a directory within the search path. Create a directory for redis and copy config files to it.
```bash
sudo cp src/redis-server src/redis-cli /usr/local/bin/
sudo mkdir /etc/redis
sudo chown ec2-user:ec2-user /etc/redis
sudo cp redis.conf /etc/redis/redis.conf
```

Adjust the config file
```bash
sed -i 's/^bind.*/# bind 127.0.0.1/g' /etc/redis/redis.conf
sed -i 's/^dir.*/dir \/etc\/redis/g' /etc/redis/redis.conf
sed -i 's/^daemonize.*/daemonize yes/g' /etc/redis/redis.conf
sed -i 's/^protected-mode.*/protected-mode no/g' /etc/redis/redis.conf
sed -i 's/^pidfile.*/pidfile \/etc\/redis\/redis.pid/g' /etc/redis/redis.conf
sed -i 's/^logfile.*/logfile \/etc\/redis\/redis_log/g' /etc/redis/redis.conf
echo 'maxmemory 800mb' >> /etc/redis/redis.conf
echo 'maxmemory-policy noeviction' >> /etc/redis/redis.conf
```

Optional tune-ups
----
Set the Redis service to auto-start on startup


```bash
sudo wget https://gist.githubusercontent.com/feliperohdee/d04126b0b727e2a0ef5eee04542794df/raw/4531d1809639fe00bef81985fe076f6a004471be/redis-server
sudo mv redis-server /etc/init.d
sudo chmod 755 /etc/init.d/redis-server
sudo chkconfig --add redis-server
sudo chkconfig --level 345 redis-server on
```

Adjust linux memory handling to void caching to disk and make Redis faster
```bash
wget https://gist.githubusercontent.com/feliperohdee/d04126b0b727e2a0ef5eee04542794df/raw/5c540f2165eb8beb3c62360507ed3dbe6ab71f38/disable-transparent-hugepages
sudo mv disable-transparent-hugepages /etc/init.d
sudo chmod 755 /etc/init.d/disable-transparent-hugepages
sudo chkconfig --add disable-transparent-hugepages

echo 'vm.overcommit_memory = 1' | sudo tee -a /etc/sysctl.conf
echo 'vm.swappiness = 0' | sudo tee -a /etc/sysctl.conf
```

Start Redis
---
Start the service
```bash
sudo service redis-server start
```

Ping it to see if it is running (you see a PONG )
```bash
redis-cli ping 
```
>PONG