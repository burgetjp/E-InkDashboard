# Readme for eInk Development 
# What scripts do what

dailyClear.py	- Used by other scripts to clear the eInk Display prior to display a new image.  Meant to help with ghosting.
dailyDash.sh	- Script used to pull a screenshot from http://redPi:3000/ or http://redPi:3000/joeHome and populate the eInk display.
dailyEink.py	- Used by other scripts to populate eInk display with an image.  Input is the /path/name of image to display.
dailyImage.sh	- Script used to randomly select an image name and then call dailyEink.py to populate eInk Display with an image.
killFirefox.sh	- Used by other scripts to search for and then kill a hung firefox-esr process.  Not sure what makes it hang, but this should clear the process to allow dailyDash.sh to run properly.  

