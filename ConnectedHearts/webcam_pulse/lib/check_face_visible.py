from device import Camera
from processors_noopenmdao import findFaceGetPulse
import cv2
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class CheckFace(object): 

    def __init__(self, face_visible):
        self.face_visible = face_visible
        self.cam = Camera(0)
        dpath = resource_path("webcam_pulse/haarcascade_frontalface_alt.xml")
        self.face_cascade = cv2.CascadeClassifier(dpath)


    def check_if_face_is_visible(): 
        while not self.face_visible:
            time.sleep(60)
            ct = 0 

            for i in range(0,50):
                frame = self.cam.getFrame()
                gray = cv2.equalizeHist(cv2.cvtColor(frame,
                                                      cv2.COLOR_BGR2GRAY))
                detected = list(self.face_cascade.detectMultiScale(gray,
                                                                   scaleFactor=1.3,
                                                                   minNeighbors=4,
                                                                   minSize=(
                                                                       50, 50),
                                                                   flags=cv2.CASCADE_SCALE_IMAGE))
                if len(detected) > 0: 
                    ct += 1
            if ct < 30:
                self.face_visible = 1

    def run(self):
        self.check_if_face_is_visible()
        self.cam.release()
