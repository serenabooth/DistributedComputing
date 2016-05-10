from datetime import datetime
import threading
import sys, time, socket, random
import uuid
from multiprocessing import Array, Process, Value, Lock
from multiprocessing.queues import Queue
import ctypes 
from control_bulb import *


# cite: http://stackoverflow.com/questions/19846332/python-threading-inside-a-class
# yay decorators
def threaded(fn):
    """ 
    Creates a new thread to run the function fn. Use by writing "@threaded" 
    above function to thread.

    fn: function 
    returns: None 
    """
    def wrapper(*args, **kwargs):
       threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class BulbQueue(Queue):
    """ 
    Bulbqueueinherits from multiprocessing.Queue, but has the added 
    functionality that it keeps track of its size while putting and getting 
    elements from the queue. Multiprocessing.Queue makes no guarantees when
    calling its size method.
    """
    def __init__(self):
        super(BulbQueue, self).__init__()
        self.queuesize = 0

    def empty(self):
        return super(BulbQueue, self).empty()

    def size(self):
        queuesize = self.queuesize
        return queuesize

    def get(self):
        if not self.empty():
            self.queuesize -= 1
            return super(BulbQueue, self).get() 
        else:
            return None

    def put(self, item):
        super(BulbQueue, self).put(item)
        self.queuesize += 1

class Bulb(Process):
    """ Creates a Bulb process which will runs leader election """
    def __init__(self, id, turned_on_list, bpm, host):
        super(Bulb, self).__init__()
        self.id = id
        self.uuid = random.randint(1,2**64-1)
        #self.uuid = self.id
        self.uuid_dict = {}
        self.bulb_objects_list = None
        self.bulbs_in_election = None
        self.leader = None
        self.leader_id = Value('i', -1)
        self.election_q = BulbQueue()
        self.state_q = BulbQueue()
        self.ping_time = random.randint(1,12)
        self.max_timeout = 15
        self.turned_on_list = turned_on_list
        self.bpm = bpm
        self.host = host

    def register_bulbs(self, bulb_objects_list):
        self.bulb_objects_list = bulb_objects_list
        self.create_uuid_dict()

    def send_uuid(self, bulbs):
        for bulb in bulbs:
            bulb.election_q.put(self.uuid)

    def create_uuid_dict(self):
        for bulb in self.bulb_objects_list:
            self.uuid_dict[bulb.uuid] = bulb

    def get_max_uuid(self):
        curr_max = self.election_q.get()
        while (self.election_q.size() > 0):
            curr_item = self.election_q.get()
            if (curr_item > curr_max):
                curr_max = curr_item
        return curr_max

    def print_q(self, q):
        q_contents = []
        while not q.empty():
            q_contents.append(q.get())
        return q_contents

    def empty_q(self, q):
        while not q.empty():
            q.get()

    def send_new_election_msg(self):
        self.bulbs_in_election = [bulb for bulb in self.bulb_objects_list 
                                    if bulb.uuid > self.uuid 
                                    and bulb.uuid != self.uuid]
        for bulb in self.bulbs_in_election:
            bulb.election_q.put("New election from: " + str(self.uuid))

    def set_bulbs_in_new_election(self, uuid):
        self.bulbs_in_election = [bulb for bulb in self.bulb_objects_list 
                                    if bulb.uuid >= uuid 
                                    and bulb.uuid != self.uuid]

    def first_leader_election(self):
        timeout = time.time() + 1
        while time.time() < timeout:
            if self.election_q.size() == 13:
                break
        self.leader = self.uuid_dict[self.get_max_uuid()]
        self.leader_id.value = self.leader.id
        print "Leader id: " + str(self.leader_id.value) + "\n"
        print "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n"
        if self.leader.id == self.id:
            print ("Hi, I'm the leader: " + str(self.id) + " Right? " + 
                    str(self.leader == self) + "\n")
            self.turn_on()
            self.respond_to_ping()
        else:
            print "Hi, I'm a follower: " + str(self.id) + "\n"
            p = Process(target=self.check_turn_on, args=())
            p.start()
            self.election_q.put("first ping")
            self.ping_leader()

    def check_turn_on(self):
        while (self.state_q.empty()):
            time.sleep(1)
        self.state_q.get()
        self.turn_on()

    def turn_on(self):
        self.turned_on_list[self.id] = 1

        """my_ssh_connection = BulbControl(my_id = self.id,
                    bpm = self.bpm, 
                    host = self.host,
                    leader_id = self.leader_id,
                    state_q = self.state_q,
                    bulb_objects_list = self.bulb_objects_list, 
                    turned_on_list = self.turned_on_list)
        my_ssh_connection.start()"""
        neighbor_above_id = (self.id + 1) % 13
        neighbor_below_id = (self.id - 1) % 13 

        neighbors_to_signal_to = []
        if self.turned_on_list[neighbor_above_id] != 1: 
            neighbor_above_addr = self.bulb_objects_list[neighbor_above_id]
            neighbors_to_signal_to.append(neighbor_above_addr)
        if self.turned_on_list[neighbor_below_id] != 1: 
            neighbor_below_addr = self.bulb_objects_list[neighbor_below_id]
            neighbors_to_signal_to.append(neighbor_below_addr)
        if len(neighbors_to_signal_to) > 0: 
            self.signal_to_neighbors(neighbors_to_signal_to)

    def ping_leader(self):
        time.sleep(self.ping_time)
        if not self.election_q.empty():
            msg = self.election_q.get()
            if "New election" in str(msg) or "New leader" in str(msg):
                initiator_uuid = long(msg.split(": ")[1])
                #print "I'm bulb " + str(self.id) + " and bulb " + 
                    #str(self.uuid_dict[initiator_uuid].id) + 
                    #" told me there was a new election \n"
                self.set_bulbs_in_new_election(initiator_uuid)
                return
            #print ("I'm bulb " + str(self.id) + " and the leader responded: " + 
                #str(msg) + "\n Also my timeout is " + str(self.ping_time) + "\n")
            self.leader.election_q.put(self.uuid)
        else:
            time.sleep(self.max_timeout - self.ping_time)
            if self.election_q.empty():
                print ("I'm bulb " + str(self.id) + 
                    " and Oh no the leader didn't respond \n")
                self.send_new_election_msg()
                return
        self.ping_leader()

    def signal_to_neighbors(self, list_of_neighbors):
        """ 
        Wait for some amount of time and then 
        tell neighbors to turn on
        """
        time.sleep(self.ping_time)
        for neighbor in list_of_neighbors: 
            neighbor.state_q.put(1)

    def respond_to_ping(self):
        while not self.election_q.empty():
            pinger_uuid = self.election_q.get()
            if "New election" in str(pinger_uuid) or "New leader" in str(pinger_uuid):
                initiator_uuid = long(pinger_uuid.split(": ")[1])
                #print ("I'm bulb " + str(self.id) + " and bulb " + 
                    #str(self.uuid_dict[initiator_uuid].id) + 
                    #" told me there was a new election \n")
                self.set_bulbs_in_new_election(initiator_uuid)
                return           
            #print "I responded to bulb " + str(self.uuid_dict[pinger_uuid].id) + "\n")
            self.uuid_dict[pinger_uuid].election_q.put(self.uuid)
        time.sleep(self.ping_time)
        higher_uuid_bulbs = [bulb for bulb in self.bulb_objects_list 
                                if bulb.uuid > self.uuid]
        for bulb in higher_uuid_bulbs:
            bulb.election_q.put("New leader: " + str(self.uuid))
        self.respond_to_ping()

    def new_leader_election(self):
        timeout = time.time() + self.max_timeout
        responses = []
        while time.time() < timeout:
            if not self.election_q.empty(): 
                msg = self.election_q.get()
                if "New election" in str(msg):
                    initiator_uuid = long(msg.split(": ")[1])
                    bulbs_in_election = [bulb for bulb in self.bulb_objects_list 
                                            if bulb.uuid >= initiator_uuid and 
                                            bulb.uuid != self.uuid]
                    self.send_uuid(bulbs_in_election)
                else:
                    if msg not in responses:
                        responses.append(msg)
        responses.sort()
        if not responses or self.uuid > responses[len(responses) - 1]:
            print ("Responses: " + str(responses) + " I'm the LEADER and I'm bulb " 
                + str(self.id) + "\n")
            print datetime.datetime.now()
            self.leader = self
            for bulb in [bulb for bulb in self.bulb_objects_list if bulb is not self]:
                bulb.election_q.put("New leader: " + str(self.uuid))
            self.empty_q(self.election_q)
            self.respond_to_ping()
        else:
            print "I'm not the leader and I'm bulb " + str(self.id) + "\n"
            new_leader = False
            timeout = time.time() + 2 * self.max_timeout
            while time.time < timeout:
                if not self.election_q.empty():
                    msg = self.election_q.get()
                    if "New leader" in str(msg):
                        leader_uuid = long(msg.split(": ")[1])
                        if self.uuid < leader_uuid:
                            self.leader = self.uuid_dict[leader_uuid]
                            new_leader = True
                            break
            self.empty_q(self.election_q)
            if new_leader:
                time.sleep(self.max_timeout)
                print ("I'm bulb " + str(self.id) + " and I think the leader is " 
                    + str(self.leader.id) + "\n")
                self.election_q.put("first ping")
                self.ping_leader()
            else:
                self.send_new_election_msg()
                return



    def run(self):
        self.first_leader_election()
        #print ("I'm bulb " + str(self.id) + " and here are the bulbs in my new election " 
        # + str([bulb.id for bulb in self.bulbs_in_election]) + "\n")
        while True:
            self.send_uuid(self.bulbs_in_election)
            self.new_leader_election()







