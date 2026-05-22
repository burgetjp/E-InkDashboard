#!/bin/bash

cd "$(dirname "$0")";

#debuging path and user running command
#pwd
#whoami

# Check if Dashboard is online
#STATUS=`wget -q  -O /home/red/Dev/logs/pingHtml.log redpi:3000/joeHome | grep '200' /tmp/foo | wc -l`

STATUS=`wget -NS redPi:3000/joeHome 2>&1|grep "HTTP/"|awk '{print $2}'`
# Cleanup html file
rm joeHome

if [[ 200 -eq $STATUS ]];
	then
		echo "Then Triggered"
		# Search and kill any running firefox-esr processes
		/home/red/Dev/scripts/killFirefox.sh
		# Create screenshot of Joe Home Dashboard
		firefox --headless --screenshot --window-size=800,500 http://redPi:3000/joeHome
		# Clear E Ink display to prevent ghosting on the display
		/home/red/Dev/scripts/dailyClear.py
		# Call Daily eInk script with the screenshot to display on the E Ink display
		/home/red/Dev/scripts/dailyEink.py screenshot.png
		# Cleanup screenshot file
		rm screenshot.png
	else
		# Call Daily eInk script to display error screen
		echo "Else Triggered"
		/home/red/Dev/scripts/dailyEink.py /home/red/Pimoroni/inky/examples/7color/CalvinHobbes.jpg
fi
