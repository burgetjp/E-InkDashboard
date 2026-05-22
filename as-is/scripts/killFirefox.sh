#!/bin/bash

PID=`ps -U root -u root u | grep "firefox-esr --headless" | grep -v grep | awk '{print $2}'`

if [[ "" != "$PID" ]]; 
	then
		echo "Found running process: "$PID
  		echo "Killing running Firefox-ESR process: $PID"
  		sudo kill -9 $PID
	else
		echo "No running Firefox-ESR process found."
fi 
