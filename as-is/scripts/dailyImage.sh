#!/bin/bash

# Define array of image names
arr[0]="image0.jpg"
arr[1]="image1.jpg"
arr[2]="image2.jpg"
arr[3]="image3.jpg"
arr[4]="image4.jpg"
arr[5]="image5.jpg"
arr[6]="image6.jpg"
arr[7]="image7.jpg"
arr[8]="image8.jpg"
arr[9]="image9.jpg"

#echo ${arr[RANDOM%${#arr[@]}]}

# Define IMAGE var to contain image name for display
IMAGE=${arr[RANDOM%${#arr[@]}]}
#echo $IMAGE

# Call display api to clear display
/home/red/Dev/scripts/dailyClear.py
# Call display api to send random image to the display
/home/red/Dev/scripts/dailyEink.py /home/red/Dev/images/$IMAGE
