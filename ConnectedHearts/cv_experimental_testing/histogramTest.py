import csv, cv2

""" 
USE THIS TO ANALYZE VIDEOS
"""

# open files (data in and data out)
cap = cv2.VideoCapture('example.mp4')
csvfile = open('experiment_synch_data.csv', 'w')

# global variables
i = 0
rois = []

def click_bright_pixels(event, x, y, flags, param):
    """
    Callback function for mouseover of a cv2 window. User should click on 13 points in the video corresponding to bulbs. 

    :param event: cv2 event (e.g. mouseclick, EVENT_LBUTTONDOWN).
    :type event: cv2 event identifier
    :param x: x coordinate
    :type x: int 
    :param y: y coordinate
    :type y: int
    :param flags: cv2 flags
    :type flags: cv2 flag identifiers
    :param param: (possible out of date) cv2 paramaters
    :type param: None
    :return: None.
    """
    global rois
    if event == cv2.EVENT_LBUTTONDOWN and len(rois) < 13:
        rois.append((x, y))

# write first line of data out
fieldnames = ['time', 'expected_brightness', 'real_brightness']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
writer.writeheader()

# set up cv2 window with data from video
cv2.namedWindow("image")
cv2.setMouseCallback("image", click_bright_pixels)
ret, frame = cap.read()
while True:
    cv2.imshow("image", frame)
    key = cv2.waitKey(1) & 0xFF

    if len(rois) == 13: 
        print rois
        break

# run until video is over
while True:
    # exit loop
    if frame is None: 
        break

    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    max_bright = 0
    # look at 13 pixels corresponding to bulb brightnesses; take max
    for j in range(0,len(rois)):
        max_bright +=  hsv_image[rois[j][1]][rois[j][0]][2]/255.0
    max_bright = max_bright / len(rois)

    # expected values alternate between all off and all on (1 second in each state)
    writer.writerow({'time': str(i), 
                     'real_brightness': str(max_bright)})

    i += 1

    ret, frame = cap.read()


csvfile.close()
cap.release()
cv2.destroyAllWindows()
