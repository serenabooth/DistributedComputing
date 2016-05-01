from device import Camera
from processors_noopenmdao import findFaceGetPulse
#import cv2
import time
import os 
from multiprocessing import Array, Process

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class CheckFace(Process): 

    def __init__(self, face_visible):
        super(CheckFace, self).__init__()
        self.face_visible = face_visible
        self.cam = None
        #self.cam = Camera(0)
        #self.cam.start()
        dpath = resource_path("webcam_pulse/haarcascade_frontalface_alt.xml")
        self.face_cascade = cv2.CascadeClassifier(dpath)


    def check_if_face_is_visible(): 
        while not self.face_visible:
            time.sleep(5)
            ct = 0 

            for i in range(0,50):
                frame = self.cam.getFrame()
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
                self.face_visible = 1
    
    def check_for_faces(self):
        self.check_if_face_is_visible()
        self.cam.release()

    def run(self):
        #time.sleep(60)
        print "trying for camera"
        self.cam = Camera(0)
        print "got camera"
        self.check_for_faces()

        #self.check_if_face_is_visible()
        #self.cam.release()
