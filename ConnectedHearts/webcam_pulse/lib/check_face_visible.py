from device import Camera
from processors_noopenmdao import findFaceGetPulse
import cv2
import time
import os 

class CheckFace(object): 

    def __init__(self, camera_obj):
        self.cam = camera_obj
        dpath = "/home/serena/DistributedComputing/ConnectedHearts/webcam_pulse/haarcascade_frontalface_alt.xml"
        self.face_cascade = cv2.CascadeClassifier(dpath)


    def check_if_face_is_visible(self):
        """ 
        Given a camera (self.cam), view 10 frames and see if a face is visible, 
        via Haar Classifier, in 3 or more of the frames. If so, return true. Else, false.

        :return: Boolean
        """

        ct = 0 
        time.sleep(10)
        print "CHECK IF FACE IS VISIBLE"
        for i in range(0,10):
            frame = self.cam.get_frame()       
            gray = cv2.equalizeHist(cv2.cvtColor(frame,
                                                  cv2.COLOR_BGR2GRAY))
            detected = list(self.face_cascade.detectMultiScale(gray,
                                                               scaleFactor=1.1,
                                                               minNeighbors=4,
                                                               minSize=(
                                                                   50, 50),
                                                               flags=cv2.CASCADE_SCALE_IMAGE))
            print "len of faces: " + str(len(detected))
            if len(detected) > 0: 
                ct += 1
        return ct >= 3
