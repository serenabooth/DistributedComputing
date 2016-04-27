from hearts import *

bulb_objects_list = []

for i in range(1, 13):
	p = Bulb(id = i)
	bulb_objects_list.append(p)

for bulb in bulb_objects_list:
	bulb.register_bulbs(bulb_objects_list)
	bulb.send_uuid()

for bulb in bulb_objects_list:
	bulb.start()

for bulb in bulb_objects_list:
	bulb.join()

#for bulb in bulb_objects_list:
	#bulb.leader_election()