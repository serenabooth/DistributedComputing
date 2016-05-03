import cv2, time
import urllib2, base64
import numpy as np
from threading import Thread 

class ipCamera(object):

    def __init__(self,url, user = None, password = None):
        self.url = url
        auth_encoded = base64.encodestring('%s:%s' % (user, password))[:-1]

        self.req = urllib2.Request(self.url)
        self.req.add_header('Authorization', 'Basic %s' % auth_encoded)

    def get_frame(self):
        response = urllib2.urlopen(self.req)
        img_array = np.asarray(bytearray(response.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_array, 1)
        return frame

class Camera(object):

    def __init__(self, camera = 0):
        if camera == 0: 
            from picamerastream import PiVideoStream

            print "trying to make camera"
            self.cam = PiVideoStream()
            print "made object"
            self.cam.start()
            time.sleep(2)
            self.valid = False
            print "initialized!" 
            try:
                resp = self.cam.read()
                self.shape = resp[1].shape
                self.valid = True
            except:
                self.shape = None
            self.is_pi_cam = True
        else: 
            self.cam = cv2.VideoCapture(0)
            if not self.cam:
                self.valid = False
                raise Exception("Camera not accessible")
 
            self.valid=True
            self.is_pi_cam = False
            self.shape = self.get_frame().shape


    def get_frame(self):
        if self.valid and self.is_pi_cam:
            frame = self.cam.read()
        elif self.valid and not self.is_pi_cam: 
            _, frame = self.cam.read()
        else:
            frame = np.ones((240,320,3), dtype=np.uint8)
            col = (0,256,256)
            cv2.putText(frame, "(Error: Camera not accessible)",
                       (65,220), cv2.FONT_HERSHEY_PLAIN, 2, col)
        return frame

    def release(self):
        self.cam.stop()
