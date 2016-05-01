from device import Camera
from processors_noopenmdao import findFaceGetPulse
import cv2
import time
import os 
from multiprocessing import Array, Process

class CheckFace(Process): 

    def __init__(self, face_visible, camera_obj):
        super(CheckFace, self).__init__()
        self.face_visible = face_visible
        self.cam = camera_obj
        #self.cam = Camera(0)
        #self.cam.start()
        dpath = "/home/serena/DistributedComputing/ConnectedHearts/webcam_pulse/haarcascade_frontalface_alt.xml"
        self.face_cascade = cv2.CascadeClassifier(dpath)


    def check_if_face_is_visible(self): 
        print str(self.face_visible)
        print "is face visible? " + str(self.face_visible == 0)
        print "is face visible? " + str(self.face_visible == 1)
        while self.face_visible.value:
            time.sleep(5)
            ct = 0 
            print "CHECK IF FACE IS VISIBLE"
            for i in range(0,50):
                frame = self.cam.get_frame()
                gray = cv2.equalizeHist(cv2.cvtColor(frame,
                                                      cv2.COLOR_BGR2GRAY))
                detected = list(self.face_cascade.detectMultiScale(gray,
                                                                   scaleFactor=1.1,
                                                                   minNeighbors=4,
                                                                   minSize=(
                                                                       50, 50),
                                                                   flags=cv2.CASCADE_SCALE_IMAGE))
                if len(detected) > 0: 
                    ct += 1
            if ct < 30:
                self.face_visible.value = 0
    
    def check_for_faces(self):
        self.check_if_face_is_visible()

    def run(self):
        #time.sleep(60)
        print "got camera"
        self.check_for_faces()

        #self.check_if_face_is_visible()
        #self.cam.release()
