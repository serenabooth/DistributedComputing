from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2, time
import urllib2, base64
import numpy as np
from threading import Thread 

class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=20):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True)
 
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

    def start(self):
	# start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
 
    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            if self.stopped:
                self.stream.close() 
                self.rawCapture.close() 
                self.camera.close()
                return 
 
    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thead should be stopped
        self.stopped = True


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
        self.cam = cv2.VideoCapture(camera)
        time.sleep(2)
        self.valid = False
        print "initialized!" 
        try:
            resp = self.cam.read()
            self.shape = resp[1].shape
            self.valid = True
        except:
            self.shape = None
        #self.cam = PiCamera()
        #self.stream = PiRGBArray(self.cam)
        #self.cam_res = (320, 240)

    def get_frame(self):
        if self.valid:
            _,frame = self.cam.read()
        else:
            frame = np.ones((240,320,3), dtype=np.uint8)
            col = (0,256,256)
            cv2.putText(frame, "(Error: Camera not accessible)",
                       (65,220), cv2.FONT_HERSHEY_PLAIN, 2, col)
        return frame

    def release(self):
        self.cam.release()
