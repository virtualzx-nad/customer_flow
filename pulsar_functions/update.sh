ADMIN=/home/ec2-user/apache-pulsar-2.4.1/bin/pulsar-admin
cwd=`pwd`

for x in `seq 0 9`
do
  # Initialize the Pulsar function workers 
  sed "s/INDEX/$x/g"  config/window_count.yml  > tmp.yml
  $ADMIN functions update --function-config-file $cwd/tmp.yml
  sed "s/INDEX/$x/g"  config/window_ratio.yml  > tmp.yml
  $ADMIN functions update --function-config-file $cwd/tmp.yml

done
$ADMIN functions update --function-config-file $cwd/config/store_ratio_to_redis.yml
rm tmp.yml
