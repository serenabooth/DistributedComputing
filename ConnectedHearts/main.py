from hearts import *
from control_pi import *
from multiprocessing.queues import Queue
from multiprocessing import Array
import ctypes

bulb_objects_dict = {}

#print type_of_array.bytes()

#test_if_queue_works = Queue()
#print test_if_queue_works

hosts = ['192.168.1.20', '192.168.1.21']

uuid_list = Array(ctypes.c_uint64, 12)
""" 
    One power strip has ip 192.168.1.20; the other, .21
    .20 will control bulbs 0-5
    .21 will control bulbs 6-11
"""
power_strip_on_list = Array('i', 12)


for i in range(0, 12):
    p = Bulb(id = i, uuid_list = uuid_list, turned_on_list = power_strip_on_list)
    #print p.uuid
    bulb_objects_dict[p.uuid] = p

for bulb in bulb_objects_dict.values():
    bulb.register_bulbs(bulb_objects_dict)
    bulb.send_uuid()

pi = Pi(bpm = 70, turned_on_list = power_strip_on_list, hosts = hosts)
pi.start()

for bulb in bulb_objects_dict.values():
   bulb.start()

for bulb in bulb_objects_dict.values():
  print "joining!"
  bulb.join()

pi.join()

#for bulb in bulb_objects_list:
    #bulb.leader_election()