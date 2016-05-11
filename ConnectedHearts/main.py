# defined within codebase
from Bulb import *
from Pi import *
from webcam_pulse.get_pulse import *
from webcam_pulse.lib.check_face_visible import *
from webcam_pulse.lib.device import Camera

# external libraries
import signal
from multiprocessing.queues import Queue
from multiprocessing import Array, Value

import ctypes

# set this to 1 if running with a webcam! 
not_on_pi = 0

# Open the camera _once_
# Resource must be given up by running camera_obj.release()
camera_obj = Camera(not_on_pi)

def kill_all_processes(pi, bulbs):
    """ 
    For each process passed in, terminate those processes

    :param pi: A process corresponding to an SSH connection
    :type pi: a Pi object
    :param bulbs: A list of processes corresponding to # bulbs
    :type bulbs: A list of processes
    """
    try: 
        os.killpg(0, signal.SIGINT)
    except KeyboardInterrupt:
        print "Living!" 
    #pi.terminate()
    #for bulb in bulbs:
    #    bulb.terminate()

""" 
Get pulse! 
"""
parser = argparse.ArgumentParser(description='Webcam pulse detector.')
parser.add_argument('--serial', default=None,
                    help='serial port destination for bpm data')
parser.add_argument('--baud', default=None,
                    help='Baud rate for serial transmission')
parser.add_argument('--udp', default=None,
                    help='udp address:port destination for bpm data')

args = parser.parse_args()

# Outer while loop to catch errors
while True: 
    
    os.setpgrp()

    hosts = ['192.168.1.20', '192.168.1.21']

    """ 
        One power strip has ip 192.168.1.20; the other, .21
        x.x.x.20 will control bulbs 0-5
        x.x.x.21 will control bulbs 6-11
    """
    power_strip_on_list = Array('i', 13)

    # Create a "CheckFace" object, in webcam_pulse/lib/check_face_visible.py
    face_check_process = CheckFace(camera_obj = camera_obj)

    # Start a process to request all bulbs to turn off.
    # Pi process defined in control_pi.py
    pi = Pi(hosts = hosts)
    pi.start()
    pi.join()
    # Processes are dead; continue.

    # Use camera to get a pulse from a face
    # Perform this _once_ initially
    pulse_val = 0; 
    App = getPulseApp(args, camera_obj)

    # Generate a pulse
    while pulse_val == 0 or pulse_val == -1: 
       pulse_val = App.main_loop()
       time.sleep(1.0/16.0)
       pulse_val = App.bpm

    # Clamp the pulse
    if pulse_val > 160: 
        pulse_val = 160
    if pulse_val < 50:
        pulse_val = 50 

    print "FINISHED with pulse " + str(pulse_val)

    print "On to the bulbs:"
    bulb_objects_list = []
    for i in range(0, 13):
        
        # Make a process for each bulb
        p = Bulb(id = i, 
                    turned_on_list = power_strip_on_list,
                    bpm = pulse_val,
                    host = hosts[1] if i % 2 else hosts[0])
        
        # Store reference in list            
        bulb_objects_list.append(p)

    # Provide a pointer to the whole list of bulbs to all Bulbs
    for bulb in bulb_objects_list:
        bulb.register_bulbs(bulb_objects_list)
        bulb.send_uuid(bulb_objects_list)
    # At this point, each Bulb has 
    # - a uuid
    # - a mapping between uuid and bulb reference in bulb_object_list
    # - an election queue, upon which each bulb has put its uuid


    try:
        # Perform leader election
        for bulb in bulb_objects_list:
            bulb.start()
        
        # Only break if face isn't visible 
        while (face_check_process.check_if_face_is_visible()):
            time.sleep(30)

        # Shut down and restart!
        print "About to shut this down"
        pulse_val = 0
        kill_all_processes(pi, bulb_objects_list)
        time.sleep(5)        

    except KeyboardInterrupt:
        # User quit
        kill_all_processes(pi, bulb_objects_list)
        camera_obj.release()
