#!/bin/bash

cd "$(dirname "$0")";

#debuging path and user running command
#pwd
#whoami

# Check if Dashboard is online
TEST=`wget -NS redPi:3000/joeHome 2>&1|grep "HTTP/"|awk '{print $2}'`
rm joeHome
echo $TEST
