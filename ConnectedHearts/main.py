from hearts import *

bulb_objects_dict = {}

for i in range(1, 13):
	bulb_objects_dict["bulb_" + str(i)] = Bulb(i, 8000+(i))
	bulb_objects_dict["bulb_" + str(i)].id = i

bulb_objects_list = bulb_objects_dict.values()

for bulb in bulb_objects_list:
	bulb.register_bulbs(bulb_objects_list)

for bulb in bulb_objects_list:
	bulb.start()

for bulb in bulb_objects_list:
	bulb.first_leader_election()