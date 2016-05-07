import numpy as numpy
import cv2

cap = cv2.VideoCapture(0)

sub_rects = [[0,50,0,50]]

frame_id = 0
last_dark_frame = 0


while cap.isOpened(): 
    _, frame = cap.read()

    cv2.imshow('frame', frame[200:250,200:250])
    cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()
