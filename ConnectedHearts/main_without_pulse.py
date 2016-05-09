#!/usr/bin/python
from hearts import *
from control_pi import *
from multiprocessing.queues import Queue
from multiprocessing import Array, Value
import ctypes
#from webcam_pulse.get_pulse import *
#from webcam_pulse.lib.check_face_visible import *
#from webcam_pulse.lib.device import Camera

is_on_pi = 1

#camera_obj = Camera(is_on_pi)

def kill_all_processes(pi, bulbs, app = None):
    pi.terminate()
    if app:
        app.terminate()
    for bulb in bulbs:
        bulb.terminate()
""" 
#Get pulse! 
parser = argparse.ArgumentParser(description='Webcam pulse detector.')
parser.add_argument('--serial', default=None,
                    help='serial port destination for bpm data')
parser.add_argument('--baud', default=None,
                    help='Baud rate for serial transmission')
parser.add_argument('--udp', default=None,
                    help='udp address:port destination for bpm data')

args = parser.parse_args()

# Outer while loop to catch errors"""
while True: 
    face_visible = Value('i', 1)
    """#time.sleep(10)

    # Perform this _once_ initially
    pulse_val = 0; # App.main_loop()
    App = getPulseApp(args, camera_obj)

    # Generate a pulse
    while pulse_val == 0 or pulse_val == -1: 
        pulse_val = App.main_loop()
        time.sleep(1.0/16.0)
        #if pulse_val == 0: 
        #    print "Found a face in main"
        #    time.sleep(10)
        #pulse_val = App.bpm

    if pulse_val > 160: 
        pulse_val = 160
    if pulse_val < 50:
        pulse_val = 50
    print "FINISHED with pulse " + str(pulse_val)"""
    pulse_val = 70

    #print type_of_array.bytes()

    #test_if_queue_works = Queue()
    #print test_if_queue_works

    hosts = ['192.168.1.20', '192.168.1.21']
    
        #One power strip has ip 192.168.1.20; the other, .21
        #.20 will control bulbs 0-5
        #.21 will control bulbs 6-11
    power_strip_on_list = Array('i', 13)

    #face_check_process = CheckFace(camera_obj = camera_obj)
    #print "face check!"
    #face_check_process.start()
    #face_check_process.join()

    print "on to the bulbs"
    bulb_objects_list = []
    for i in range(0, 13):
        if i % 2: 
            host_powerstrip = hosts[0]
        else:
            host_powerstrip = hosts[1]
        p = Bulb(id = i, 
                    turned_on_list = power_strip_on_list, 
                    bpm = pulse_val, 
                    host = host_powerstrip)
        bulb_objects_list.append(p)

    for bulb in bulb_objects_list:
        bulb.register_bulbs(bulb_objects_list)
        bulb.send_uuid(bulb_objects_list)

    try:
        """pi = Pi(bpm = App.bpm, 
                              turned_on_list = power_strip_on_list, 
                              hosts = hosts, 
                              face_visible = face_visible)
        #pi.start()"""

        for bulb in bulb_objects_list:
           bulb.start()
           
        while (face_visible):
            print "face dere?" +  str(face_visible.value)

            time.sleep(15)

        print "About to shut this down"
        pulse_val = 0
        kill_all_processes(pi, bulb_objects_list)
        time.sleep(5)
        #continue
        

    except KeyboardInterrupt:
        kill_all_processes(pi, bulb_objects_list, App)
        camera_obj.release()



#for bulb in bulb_objects_list:
    #bulb.leader_election()
