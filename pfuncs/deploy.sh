ADMIN=/home/ec2-user/apache-pulsar-2.4.1/bin/pulsar-admin
cwd=`pwd`

for x in `seq 0 9`
do
  echo Initializing partition $x
 
  # Initialize the Schema for each of these topics involved 
  sed "s/INDEX/$x/g"  config/init_count.yml > tmp.yml
  printer.py tmp.yml
  sed "s/INDEX/$x/g"  config/init_ratio.yml > tmp.yml
  printer.py tmp.yml
 
  # Initialize the Pulsar function workers 
  sed "s/INDEX/$x/g"  config/window_count.yml  > tmp.yml
  $ADMIN functions create --function-config-file $cwd/tmp.yml
  sed "s/INDEX/$x/g"  config/window_ratio.yml  > tmp.yml
  $ADMIN functions create --function-config-file $cwd/tmp.yml

  sleep 3
done
$ADMIN functions create --function-config-file $cwd/config/store_ratio_to_redis.yml
rm tmp.yml
