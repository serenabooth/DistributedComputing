from picamerastream import PiVideoStream
import cv2, time
import imutils

vs = PiVideoStream()
vs.start()
time.sleep(2.0)

while True: 
    frame = vs.read()
    #frame = imutils.resize(frame, width=400)
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

cv2.destroyAllWindows()
vs.stop()

