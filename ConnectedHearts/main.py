#!/usr/bin/python
from hearts import *
from control_pi import *
from multiprocessing.queues import Queue
from multiprocessing import Array, Value
import ctypes
from webcam_pulse.get_pulse import *
from webcam_pulse.lib.check_face_visible import *
from webcam_pulse.lib.device import Camera

camera_obj = Camera(0)

def kill_all_processes(pi, bulbs, fc, app = None):
    pi.terminate()
    fc.terminate()
    if app:
        app.terminate()
    for bulb in bulbs:
        bulb.terminate()

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
App = getPulseApp(args, camera_obj)
App.start()

while True: 
    face_visible = Value('i', 1)
    time.sleep(10)

    while App.bpm == 0 or App.bpm == -1: 
        continue
        #if pulse_val == 0: 
        #    print "Found a face in main"
        #    time.sleep(10)
        #pulse_val = App.bpm

    if App.bpm > 160: 
        App.bpm = 160
    if App.bpm < 50:
        App.bpm = 50
    print "FINISHED with pulse " + str(App.bpm)
    #App.bpm = 70
    bulb_objects_dict = {}

    #print type_of_array.bytes()

    #test_if_queue_works = Queue()
    #print test_if_queue_works

    hosts = ['192.168.1.20', '192.168.1.21']

    uuid_list = Array(ctypes.c_uint64, 13)
    """ 
        One power strip has ip 192.168.1.20; the other, .21
        .20 will control bulbs 0-5
        .21 will control bulbs 6-11
    """
    power_strip_on_list = Array('i', 13)

    #face_check_process = CheckFace(face_visible = face_visible, camera_obj = camera_obj)
    #print "face check!"
    #face_check_process.start()
    #face_check_process.join()

    print "on to the bulbs"
    for i in range(0, 13):
        p = Bulb(id = i, uuid_list = uuid_list, turned_on_list = power_strip_on_list, face_visible = face_visible)
        #print p.uuid
        bulb_objects_dict[p.uuid] = p

    for bulb in bulb_objects_dict.values():
        bulb.register_bulbs(bulb_objects_dict)
        bulb.send_uuid()

    try:
        pi = Pi(bpm = App.bpm, 
                              turned_on_list = power_strip_on_list, 
                              hosts = hosts, 
                              face_visible = face_visible)
        pi.start()

        for bulb in bulb_objects_dict.values():
           bulb.start()
           
        while (App.bpm != -1):
            print "face dere?" +  str(face_visible.value)
            #for bulb in bulb_objects_dict.values():
            #    print "joining!"
            #    bulb.join()

            #pi.join()
            time.sleep(10)
        print "About to shut this down"
        kill_all_processes(pi, bulb_objects_dict.values(), face_check_process)
        time.sleep(5)
        continue
        

    except KeyboardInterrupt:
        kill_all_processes(pi, bulb_objects_dict.values(), face_check_process, App)
        camera_obj.release()



#for bulb in bulb_objects_list:
    #bulb.leader_election()
