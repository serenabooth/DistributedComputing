from datetime import datetime
import threading
import sys, time, socket, random
import uuid
from multiprocessing import Array, Process, Value
from multiprocessing.queues import Queue
import ctypes 
from control_bulb import *


# cite: http://stackoverflow.com/questions/19846332/python-threading-inside-a-class
# yay decorators
def threaded(fn):
    """ 
    Creates a new thread to run the function fn. Use by writing "@threaded" above function to thread.

    fn: function 
    returns: None 
    """
    def wrapper(*args, **kwargs):
       threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class BulbQueue(Queue):
    def __init__(self):
        #print "Here's the queue type: " + str(type(Queue()))
        super(BulbQueue, self).__init__()
        self.queuesize = 0

    def empty(self):
        return super(BulbQueue, self).empty()

    def size(self):
        return self.queuesize

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
    def __init__(self, id, turned_on_list, bpm, host):
        super(Bulb, self).__init__()
        self.id = id
        self.uuid = random.randint(1,2**64-1)
        self.uuid_dict = {}
        self.bulb_objects_list = None
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

    def send_uuid(self):
        for bulb in self.bulb_objects_list:
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
        #print "Am I getting here? Queue size: " + str(q.size()) + "\n"
        while not q.empty():
            #print "What about here? \n"
            q_contents.append(str(q.get()))
        return q_contents

    #def empty_election_q_and_check_for_leader(self):


    def leader_election(self):
        #print "is this working? \n"
        self.leader = None
        timeout = time.time() + 1
        while True:
            if time.time() > timeout:
                break
            if self.election_q.size() == 13:
                #print "Do I ever get here? \n"
                break
        self.leader = self.uuid_dict[self.get_max_uuid()]
        self.leader_id.value = self.leader.id
        print "Leader id: " + str(self.leader_id.value) + "\n"
        #print "Or here? " + str(self.leader.id) + "\n" 
        """if (self == self.leader):
            sys.stderr.write("I actually exited. I'm the leader. " + "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n")
            return"""
        #print "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n"
        sys.stderr.write("id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n")
        if self.leader.id == self.id:
            print "Hi, I'm the leader: " + str(self.id) + " Right? " + str(self.leader == self) + "\n"
            self.turn_on()
            """timeout = time.time() + 10
            while True:
                #print "Leader. Here's my queue size: " + str(self.election_q.size())
                if time.time() > timeout:
                    break
            print self.print_q(self.election_q)
            #self.set_up_leader_socket()"""
            self.respond_to_ping()
        else:
            print "Hi, I'm a follower: " + str(self.id) + "\n"
            p = Process(target=self.check_turn_on, args=())
            p.start()
            self.election_q.put("first ping")
            self.ping_leader()

            #self.connect_to_leader_socket(connection_timeout, time.time())
        #sys.stderr.write("Number of bulbs in dict: " + str(len(self.uuid_dict)) + " I'm thread " + str(self.id) + "\n")
        #self.ping_leader_socket()
        #print "I got here and I'm bulb " + str(self.id) + "\n"

    def check_turn_on(self):
        while (self.state_q.empty()):
            #print "I'm bulb " + str(self.id) + " and I'm checking if turned on"
            time.sleep(1)
        self.state_q.get()
        self.turn_on()

    def turn_on(self):
        self.turned_on_list[self.id] = 1
        #print "Yay, I'm bulb " + str(self.id) + " and I turned on"

        my_ssh_connection = BulbControl(my_id = self.id,
                    bpm = self.bpm, 
                    host = self.host,
                    leader_id = self.leader_id,
                    state_q = self.state_q,
                    bulb_objects_list = self.bulb_objects_list)
        my_ssh_connection.start()
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
        #print "I'm bulb " + str(self.id) + " and I'm pinging the leader"
        start_time = time.time()
        timeout = start_time + self.ping_time
        while True:
            if time.time() > timeout:
                break
        if not self.election_q.empty():
            msg = self.election_q.get()
            #sys.stderr.write("I'm bulb " + str(self.id) + " and the leader responded: " + str(self.election_q.get()) + "\n Also my timeout is " + str(self.ping_time) + "\n")
            self.leader.election_q.put(self.uuid)
            self.ping_leader()
        else:
            while True:
                if time.time() > start_time + self.max_timeout:
                    break
            if self.election_q.empty():
                sys.stderr.write("Oh no the leader didn't respond \n")
                #for bulb in bulb_objects_list:
                #    bulb.election_q.put("New election")
                #    self.leader_election()
            else:
                self.ping_leader()

    def signal_to_neighbors(self, list_of_neighbors):
        """ 
        Wait for some amount of time and then 
        tell neighbors to turn on
        """
        # TODO: not sure how long we want this delay to be
        timeout = time.time() + self.ping_time
        while True:
            if time.time() > timeout:
                break
        for neighbor in list_of_neighbors: 
            #print "Bulb " + str(neighbor.id) + " size before: " + str(neighbor.state_q.size()) + "\n"
            #print "Bulb " + str(self.id) + " signaled to bulb " + str(neighbor.id) + "\n"
            neighbor.state_q.put(1)
            #print "Bulb " + str(neighbor.id) + " size after: " + str(neighbor.state_q.size()) + "\n"

    def respond_to_ping(self):
        while not self.election_q.empty():
            #print "There's something on my queue"
            pinger_uuid = self.election_q.get()
            #sys.stderr.write("I responded to bulb " + str(self.uuid_dict[pinger_uuid].id) + "\n")
            self.uuid_dict[pinger_uuid].election_q.put(self.uuid)
        timeout = time.time() + self.ping_time
        while True:
            if time.time() > timeout:
                break
        self.respond_to_ping()

    def run(self):
        self.leader_election()






