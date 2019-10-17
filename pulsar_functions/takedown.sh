ADMIN=/home/ec2-user/apache-pulsar-2.4.1/bin/pulsar-admin

for f in `$ADMIN functions list`
do
	$ADMIN functions delete --fqfn public/default/$f
done	
