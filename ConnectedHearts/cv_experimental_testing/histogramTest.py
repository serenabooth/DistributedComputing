import csv
from datetime import datetime
import numpy as np 
import cv2

cap = cv2.VideoCapture('example.mp4')
on = 0
state_ct = 0
i = 0
do_not_run = False

csvfile = open('experiment_synch_data.csv', 'w')
fieldnames = ['time', 'expected_brightness', 'real_brightness']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

writer.writeheader()

while not do_not_run:
    ret, frame = cap.read()

    if frame is None: 
        do_not_run = True

    if not do_not_run:
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        max_bright = hsv_image[0][0][2]
        print max_bright

        if on: 
            writer.writerow({'time': str(i), 'expected_brightness': '0', 'real_brightness': str(max_bright)})
        else:
            writer.writerow({'time': str(i), 'expected_brightness': '255', 'real_brightness': str(max_bright)})

        if state_ct == 120: 
            on = (on + 1) % 2
            state_ct = 0

        state_ct += 1
        i += 1

csvfile.close()
cap.release()
cv2.destroyAllWindows()