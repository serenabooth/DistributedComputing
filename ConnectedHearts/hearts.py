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
        self.lock = Lock()

    def empty(self):
        return super(BulbQueue, self).empty()

    def size(self):
        self.lock.acquire()
        queuesize = self.queuesize
        self.lock.release()
        return queuesize

    def get(self):
        if not self.empty():
            self.lock.acquire()
            self.queuesize -= 1
            self.lock.release()
            return super(BulbQueue, self).get() 
        else:
            return None

    def put(self, item):
        super(BulbQueue, self).put(item)
        self.lock.acquire()
        self.queuesize += 1
        self.lock.release()

class Bulb(Process):
    def __init__(self, id, turned_on_list, bpm, host):
        super(Bulb, self).__init__()
        self.id = id
        self.uuid = random.randint(1,2**64-1)
        self.uuid_dict = {}
        self.bulb_objects_list = None
        self.bulbs_to_send_uuid = None
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

    def send_uuid(self, bulb_list):
        for bulb in bulb_list:
            bulb.election_q.put(self.uuid)

    def create_uuid_dict(self):
        for bulb in self.bulb_objects_list:
            self.uuid_dict[bulb.uuid] = bulb

    def check_new_leader_and_get_max_uuid(self):
        possible_leaders = []
        curr_max = 0
        while not self.election_q.empty():
            curr_item = self.election_q.get()
            if (type(curr_item) == type(1) and curr_item > curr_max):
                curr_max = curr_item
            if "New leader" in str(curr_item):
                possible_leaders.append(int(curr_item.split(": ")[1]))
        if possible_leaders:
            curr_max = max(possible_leaders)
        if curr_max == 0:
            curr_max = self.uuid
        return curr_max

    def print_q(self, q):
        q_contents = []
        #print "Am I getting here? Queue size: " + str(q.size()) + "\n"
        while not q.empty():
            #print "What about here? \n"
            q_contents.append(str(q.get()))
        return q_contents

    def first_leader_election(self):
        #print "is this working? \n"
        timeout = time.time() + 1
        while True:
            if time.time() > timeout:
                break
            if self.election_q.size() == 13:
                #print "Do I ever get here? \n"
                break
        self.leader = self.uuid_dict[self.check_new_leader_and_get_max_uuid()]
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

    def leader_election(self):
        #print "is this working? \n"
        timeout = time.time() + 1
        while True:
            if time.time() > timeout:
                break
            if self.election_q.size() == 13:
                #print "Do I ever get here? \n"
                break
        self.leader = self.uuid_dict[self.check_new_leader_and_get_max_uuid()]
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
            """timeout = time.time() + 10
            while True:
                #print "Leader. Here's my queue size: " + str(self.election_q.size())
                if time.time() > timeout:
                    break
            print self.print_q(self.election_q)
            #self.set_up_leader_socket()"""
            for bulb in self.bulb_objects_list:
                bulb.election_q.put("New leader: " + str(self.uuid))
            self.respond_to_ping()
        else:
            print "Hi, I'm a follower: " + str(self.id) + "\n"
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

        """my_ssh_connection = BulbControl(my_id = self.id,
                    bpm = self.bpm, 
                    host = self.host,
                    leader_id = self.leader_id,
                    state_q = self.state_q,
                    bulb_objects_list = self.bulb_objects_list)
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
        #print "I'm bulb " + str(self.id) + " and I'm pinging the leader"
        start_time = time.time()
        timeout = start_time + self.ping_time
        while True:
            if time.time() > timeout:
                break
        if not self.election_q.empty():
            msg = self.election_q.get()
            if "New election" in str(msg):
                initiator_uuid = int(msg.split(": ")[1])
                print "Is this right? " + str(initiator_uuid)
                self.bulbs_to_send_uuid = [bulb for bulb in self.bulb_objects_list if bulb.uuid >= initiator_uuid]
                return
            if "New leader" in str(msg):
                new_leader_uuid = int(msg.split(": ")[1])
                if new_leader_uuid > self.leader.uuid:
                    self.leader = self.uuid_dict[new_leader_uuid]
                    sys.stderr.write("I'm bulb " + str(self.id) + " and I've decided that the leader is " + str(self.leader.id) + "\n")
                else:
                    self.bulbs_to_send_uuid = [bulb for bulb in self.bulb_objects_list if bulb.uuid >= self.uuid]
                    for bulb in self.bulbs_to_send_uuid:
                        bulb.election_q.put("New election from bulb: " + str(self.uuid))
                    return
            #sys.stderr.write("I'm bulb " + str(self.id) + " and the leader responded: " + str(self.election_q.get()) + "\n Also my timeout is " + str(self.ping_time) + "\n")
            self.leader.election_q.put(self.uuid)
        else:
            print "My queue is empty"
            while True:
                if time.time() > start_time + self.max_timeout:
                    break
            if self.election_q.empty():
                print "I'm bulb " + str(self.id) + " and I'm starting a new election \n"
                #print "My uuid: " + str(self.uuid) + "\n"
                print "Oh no the leader didn't respond \n"
                """sorted_uuids = sorted([(bulb.id, bulb.uuid) for bulb in self.bulb_objects_list], key=lambda x: x[1])
                print "Sorted uuids, yes: " + str(sorted_uuids)
                higher_uuid = []
                for bulb in self.bulb_objects_list:
                    if bulb.uuid >= self.uuid:
                        higher_uuid.append(bulb)
                print "Actual higher uuid?: " + str(higher_uuid)"""
                self.bulbs_to_send_uuid = [bulb for bulb in self.bulb_objects_list if bulb.uuid >= self.uuid]
                #print [bulb.id for bulb in bulbs_to_send_uuid]
                #print "Higher uuids?: " + str(bulbs_to_send_uuid)
                #print "Does it work here? " + str(self.bulbs_to_send_uuid)
                for bulb in self.bulbs_to_send_uuid:
                    #print "The higher uuid: " + str(bulb.uuid) + "\n"
                    print "Bulb " + str(self.uuid) + " starting new election"
                    bulb.election_q.put("New election from bulb: " + str(self.uuid))
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
            if "New election" in str(pinger_uuid):
                initiator_uuid = int(pinger_uuid.split(": ")[1])
                self.bulbs_to_send_uuid = [bulb for bulb in self.bulb_objects_list if bulb.uuid >= initiator_uuid]
                return
            if "New leader" in str(pinger_uuid):
                new_leader_uuid = int(pinger_uuid.split(": ")[1])
                if new_leader_uuid > self.leader.uuid:
                    self.leader = self.uuid_dict[new_leader_uuid]
                    sys.stderr.write("I'm bulb " + str(self.id) + " and I've decided that the leader is " + str(self.leader.id) + "\n")
                else:
                    self.bulbs_to_send_uuid = [bulb for bulb in self.bulb_objects_list if bulb.uuid >= self.uuid]
                    for bulb in self.bulbs_to_send_uuid:
                        bulb.election_q.put("New election from bulb: " + str(self.uuid))
                    return
            #sys.stderr.write("I responded to bulb " + str(self.uuid_dict[pinger_uuid].id) + "\n")
            self.uuid_dict[pinger_uuid].election_q.put(self.uuid)
            if self.uuid == 2**64-1:
                print "Sleeping now \n" 
                time.sleep(30000)
                print "Done sleeping \n"
        timeout = time.time() + self.ping_time
        while True:
            if time.time() > timeout:
                break
        self.respond_to_ping()

    def run(self):
        self.first_leader_election()
        while True:
            self.send_uuid(self.bulbs_to_send_uuid)
            print "I'm bulb " + str(self.id) + " and I got to the while true again"
            self.leader_election()
            print "I'm bulb " + str(self.id) + " and there's a new election. Woo hoo! \n"
            #print "bulbs to send " + str(self.bulbs_to_send_uuid)







