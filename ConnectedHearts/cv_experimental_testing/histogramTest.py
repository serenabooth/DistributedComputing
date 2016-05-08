import csv
from datetime import datetime
import numpy as np 
import cv2
import time

def click_bright_pixels(event, x, y, flags, param):
    global rois
    if event == cv2.EVENT_LBUTTONDOWN:
        rois.append((x, y))

cap = cv2.VideoCapture('example.mp4')
on = 0
state_ct = 0
i = 0
do_not_run = False

rois = []

csvfile = open('experiment_synch_data.csv', 'w')
fieldnames = ['time', 'expected_brightness', 'real_brightness']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
cv2.namedWindow("image")
cv2.setMouseCallback("image", click_bright_pixels)


writer.writeheader()

ret, frame = cap.read()

while True:
    cv2.imshow("image", frame)
    key = cv2.waitKey(1) & 0xFF

    if len(rois) == 13: 
        print rois
        break

while not do_not_run:
    ret, frame = cap.read()

    while len(rois) < 13:
        time.sleep(2)

    if frame is None: 
        do_not_run = True

    if not do_not_run:
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        max_bright = 0

        for j in range(0,len(rois)):
            tmp =  hsv_image[rois[j][1]][rois[j][0]][2]/255.0
            max_bright = max(max_bright, tmp)
        print max_bright

        if on: 
            writer.writerow({'time': str(i), 'expected_brightness': '0', 'real_brightness': str(max_bright)})
        else:
            writer.writerow({'time': str(i), 'expected_brightness': '1', 'real_brightness': str(max_bright)})

        if state_ct == 120: 
            on = (on + 1) % 2
            state_ct = 0

        state_ct += 1
        i += 1

csvfile.close()
cap.release()
cv2.destroyAllWindows()