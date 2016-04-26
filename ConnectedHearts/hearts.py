from datetime import datetime
from threading import *
import sys, time, socket, random, Queue
import uuid

# cite: http://stackoverflow.com/questions/19846332/python-threading-inside-a-class
# yay decorators
def threaded(fn):
    """ Creates a new thread to run the function fn """
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class Bulb(Thread):
	def __init__(self, id):
		self.id = id
		self.uuid = uuid.uuid4()
		self.uuid_dict = {}
		self.bulb_list = None
		self.leader = None

		self.uuid_dict[self.uuid] = self

		Thread.__init__(self)

	def register_bulbs(self, all_bulb_objects):
		self.bulb_list = all_bulb_objects

	def empty_uuid_dict(self):
		self.uuid_dict = {}

	def add_uuid(self, bulb, bulb_uuid):
		if bulb_uuid not in self.uuid_dict.values():
			self.uuid_dict[bulb_uuid] = bulb

	def send_uuid(self):
		for bulb in self.bulb_list:
			bulb.add_uuid(self, self.uuid)	

	@threaded
	def first_leader_election(self):
		#print "is this working"
		timeout = time.time() + 20
		while True:
			if time.time() > timeout:
				break
			if len(self.uuid_dict) == 12:
				self.leader = self.uuid_dict[max(self.uuid_dict.keys())]
		self.leader = self.uuid_dict[max(self.uuid_dict.keys())]
		print "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n"

	def run(self):
		print "Hi I'm bulb_" + str(self.id) + "\n"
		self.send_uuid()
		






