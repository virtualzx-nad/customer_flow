#!/bin/sh
#
# pulsar-zookeeper  ZooKeeper service for Pulsar 
#
# chkconfig: 345 99 01
# description: Start the ZooKeeper cluster for Pulsar 

usage() {
    cat <<EOF
Usage: pulsar-zookeeper (start|stop)
EOF
}
export _JAVA_OPTIONS="-Xms400m -Xmx800m"
PULSAR_HOME=/home/ec2-user/apache-pulsar-2.4.1/
command=zookeeper


if [ -f "$PULSAR_HOME/conf/pulsar_env.sh" ]
then
    . "$PULSAR_HOME/conf/pulsar_env.sh"
fi

PULSAR_LOG_DIR=${PULSAR_LOG_DIR:-"$PULSAR_HOME/logs"}
PULSAR_LOG_APPENDER=${PULSAR_LOG_APPENDER:-"RollingFile"}
PULSAR_STOP_TIMEOUT=${PULSAR_STOP_TIMEOUT:-30}
PULSAR_PID_DIR=${PULSAR_PID_DIR:-$PULSAR_HOME/bin}

if [ $# = 0 ]; then
    usage
    exit 1
elif [ $# = 1 ]; then
    if [ $1 == "--help" -o $1 == "-h" ]; then
        usage
        exit 1
    fi
fi

startStop=$1
shift

export PULSAR_LOG_DIR=$PULSAR_LOG_DIR
export PULSAR_LOG_APPENDER=$PULSAR_LOG_APPENDER
export PULSAR_LOG_FILE=pulsar-$command-$HOSTNAME.log

pid=$PULSAR_PID_DIR/pulsar-$command.pid
out=$PULSAR_LOG_DIR/pulsar-$command-$HOSTNAME.out
logfile=$PULSAR_LOG_DIR/$PULSAR_LOG_FILE

rotate_out_log ()
{
    log=$1;
    num=5;
    if [ -n "$2" ]; then
       num=$2
    fi
    if [ -f "$log" ]; then # rotate logs
        while [ $num -gt 1 ]; do
            prev=`expr $num - 1`
            [ -f "$log.$prev" ] && mv "$log.$prev" "$log.$num"
            num=$prev
        done
        mv "$log" "$log.$num";
    fi
}

mkdir -p "$PULSAR_LOG_DIR"

case $startStop in
  (start)
    if [ -f $pid ]; then
      if kill -0 `cat $pid` > /dev/null 2>&1; then
        echo ZooKeeper running as process `cat $pid`.  Stop it first.
        exit 1
      fi
    fi

    rotate_out_log $out
    echo starting pulsar-$command, logging to $logfile
    pulsar=$PULSAR_HOME/bin/pulsar
    nohup $pulsar $command "$@" > "$out" 2>&1 < /dev/null &
    echo $! > $pid
    sleep 1; head $out
    sleep 2;
    if ! ps -p $! > /dev/null ; then
      exit 1
    fi
    ;;

  (stop)
    if [ -f $pid ]; then
      TARGET_PID=$(cat $pid)
      if kill -0 $TARGET_PID > /dev/null 2>&1; then
        echo "stopping pulsar-$command"
        kill $TARGET_PID

        count=0
        location=$PULSAR_LOG_DIR
        while ps -p $TARGET_PID > /dev/null;
         do
          echo "Shutdown is in progress... Please wait..."
          sleep 1
          count=`expr $count + 1`

          if [ "$count" = "$PULSAR_STOP_TIMEOUT" ]; then
                break
          fi
         done

        if [ "$count" != "$PULSAR_STOP_TIMEOUT" ]; then
            echo "Shutdown completed."
        fi

        if kill -0 $TARGET_PID > /dev/null 2>&1; then
              fileName=$location/$command.out
              $JAVA_HOME/bin/jstack $TARGET_PID > $fileName
              echo "Thread dumps are taken for analysis at $fileName"
              if [ "$1" == "-force" ]
              then
                 echo "forcefully stopping $command"
                 kill -9 $TARGET_PID >/dev/null 2>&1
                 echo Successfully stopped the process
              else
                 echo "WARNNING :  $command is not stopped completely."
                 exit 1
              fi
        fi
      else
        echo "no $command to stop"
      fi
      rm $pid
    else
      echo no "$command to stop"
    fi
    ;;

  (*)
    usage
    exit 1
    ;;
esac
