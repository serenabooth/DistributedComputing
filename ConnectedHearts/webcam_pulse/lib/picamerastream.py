from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2, time
import urllib2, base64
import numpy as np
from threading import Thread 

""" Credit: http://www.pyimagesearch.com/2016/01/04/unifying-picamera-and-cv2-videocapture-into-a-single-class-with-opencv/
"""

class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=20):
        """ 
        Create a videostream from a PiCamera

        :param resolution: camera resolution, default to (320x240)
        :type resolution: tuple of ints
        :param framerate: camera framerate, default to 20 (really 16)
        :type framerate: int
        """
        # initialize the camera and stream
        self.camera = PiCamera()
        print " Got camera " + str(self.camera)
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
        """
        Start the thread corresponding to a camera object
        """
        #start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
 
    def update(self):
        """ 
        Continually look for frames from the camera; when stopped, shut down
        """
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
        """ 
        Return the most recent frame
        """
        # return the frame most recently read
        return self.frame

    def stop(self):
        """ 
        Set an environment variable to shutdown camera
        """
        # indicate that the thead should be stopped
        self.stopped = True
