import csv
from datetime import datetime
import numpy as np 
import cv2

cap = cv2.VideoCapture('example.mp4')
on = 0
state_ct = 0
i = 0

while cap.isOpened(): 
    with open('experiment_synch_data.csv', 'w') as csvfile:
        ret, frame = cap.read()
        
        if frame == None: 
            break

        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        max_bright = hsv_image[0][0][2]
        print hsv_image[0]



        fieldnames = ['time', 'expected_brightness_value', 'experiment_max_brightness']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

   
        if on: 
            writer.writerow({'time': str(i), 'expected_brightness_value': '0', 'experiment_max_brightness': str(max_bright)})
        else:
            writer.writerow({'time': str(i), 'expected_brightness_value': '255', 'experiment_max_brightness': str(max_bright)})

        if state_ct == 120: 
            on = (on + 1) % 2
            state_ct = 0

        state_ct += 1
        i += 1

cap.release()
cv2.destroyAllWindows()