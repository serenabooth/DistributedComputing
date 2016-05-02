from device import Camera
from processors_noopenmdao import findFaceGetPulse
import cv2
import time
import os 

class CheckFace(object): 

    def __init__(self, camera_obj):
        self.cam = camera_obj
        #self.cam = Camera(0)
        #self.cam.start()
        dpath = "/home/serena/DistributedComputing/ConnectedHearts/webcam_pulse/haarcascade_frontalface_alt.xml"
        self.face_cascade = cv2.CascadeClassifier(dpath)


    def check_if_face_is_visible(self):
        ct = 0 
        time.sleep(10)
        print "CHECK IF FACE IS VISIBLE"
        for i in range(0,10):
            frame = self.cam.get_frame()
            cv2.imshow("Frame", frame)
            cv2.waitKey(0)          
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


    
    # def check_for_faces(self):
    #     self.check_if_face_is_visible()

    # def run(self):
    #     #time.sleep(60)
    #     print "got camera"
    #     self.check_for_faces()

        #self.check_if_face_is_visible()
        #self.cam.release()
