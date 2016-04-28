from hearts import *
from multiprocessing.queues import Queue
from multiprocessing import Array
import ctypes

bulb_objects_dict = {}
#print type_of_array.bytes()

test_if_queue_works = Queue()
print test_if_queue_works

uuid_list = Array(ctypes.c_uint64, 12)

for i in range(1, 13):
	p = Bulb(id = i, uuid_list = uuid_list)
	print p.uuid
	bulb_objects_dict[p.uuid] = p

for bulb in bulb_objects_dict.values():
	bulb.register_bulbs(bulb_objects_dict)
	bulb.send_uuid()
	#bulb.send_uuid()

#for bulb in bulb_objects_dict.values():
#	bulb.send_msg_to_leader(str(bulb.id))

for bulb in bulb_objects_dict.values():
	bulb.start()

for bulb in bulb_objects_dict.values():
	bulb.join()

#for bulb in bulb_objects_list:
	#bulb.leader_election()