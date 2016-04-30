from datetime import datetime
import threading
import sys, time, socket, random, Queue
import uuid
from multiprocessing import Array, Process
from multiprocessing.queues import Queue
import ctypes 
# cite: http://stackoverflow.com/questions/19846332/python-threading-inside-a-class
# yay decorators
#def threaded(fn):
    #""" 
    #Creates a new thread to run the function fn. Use by writing "@threaded" above function to thread.

    #fn: function 
    #returns: None 
    #"""
    #def wrapper(*args, **kwargs):
    #    Thread(target=fn, args=args, kwargs=kwargs).start()
    #return wrapper

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
    def __init__(self, id, uuid_list, turned_on_list):
        super(Bulb, self).__init__()
        self.id = id
        self.uuid = random.randint(1,2**64-1)
        self.uuid_dict = None
        self.leader = None
        self.new_election = False
        self.uuid_list = uuid_list
        self.election_q = BulbQueue()
        self.state_q = BulbQueue()
        self.ping_time = random.randint(1,12)
        self.turned_on_list = turned_on_list

    def register_bulbs(self, bulb_objects_dict):
        self.uuid_dict = bulb_objects_dict

    def send_uuid(self):
        #print self.uuid
        self.uuid_list[self.id] = self.uuid
        #print self.uuid_list[0]
        self.uuid_dict[self.uuid] = self
        """#print "Is the thread getting here? \n"
        for bulb in self.bulb_list:
            #print "Here's my id: " + str(bulb.id) + "\n"
            bulb.uuid_list.put(self.uuid)
            bulb.uuid_dict[self.uuid] = self
            #print "I'm bulb " + str(bulb.id) +  " What about here? The dict: " + str(bulb.uuid_dict) + "\n"""""

    def get_max_uuid(self):
        return max(self.uuid_list)

    def print_q(self, q):
        q_contents = []
        #print "Am I getting here? Queue size: " + str(q.size()) + "\n"
        while not q.empty():
            #print "What about here? \n"
            q_contents.append(str(q.get()))
        return q_contents

    #@threaded
    def leader_election(self):
        #print "is this working? \n"
        self.leader = None
        timeout = time.time() + 1
        while True:
            if time.time() > timeout:
                break
            if len(self.uuid_list) == 12:
                #print "Before timeout. My uuid queue: " + str(self.uuid_list.size()) + "\n"
                #print "Do I ever get here? \n"
                break
        self.leader = self.uuid_dict[self.get_max_uuid()]
        #print "After timeout. My uuid queue: " + str(self.uuid_list.size()) + "\n"
        #print "Or here? " + str(self.leader.id) + "\n" 
        """if (self == self.leader):
            sys.stderr.write("I actually exited. I'm the leader. " + "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n")
            return"""
        #print "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n"
        sys.stderr.write("id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n")
        self.new_election = False

        if self.leader.id == self.id:
            print "Hi, I'm the leader: " + str(self.id) + " Right? " + str(self.leader == self) + "\n"
            self.turned_on_list[self.id] = 1
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
            self.ping_leader()

            #self.connect_to_leader_socket(connection_timeout, time.time())
        #sys.stderr.write("Number of bulbs in dict: " + str(len(self.uuid_dict)) + " I'm thread " + str(self.id) + "\n")
        #self.ping_leader_socket()
        #print "I got here and I'm bulb " + str(self.id) + "\n"

    def send_msg_to_leader(self, msg):
        #bulb_objects_list = self.uuid_dict.values()
        """for i in range(0, len(bulb_objects_list) - 1):
            print bulb_objects_list[i].election_q == bulb_objects_list[i + 1].election_q
        #print "Send leader msg to " + str(self.leader.id) + "\n"""
        self.leader.election_q.put(msg)
        #print "Leader queue: " + str(self.election_q.size()) + " Uuid queue: " + str(len(self.uuid_list)) + "\n"

    def ping_leader(self):
        timeout = time.time() + self.ping_time
        while True:
            if time.time() > timeout:
                break
        self.leader.election_q.put(self.uuid)
        # wait for response from leader here before pinging
        # again, by checking if queue has an element in it
        # if no response, can assume that it's died 
        # and start leader election
        # also check for a leader election initiation here
        self.ping_leader()

    def respond_to_ping(self):
        while not self.election_q.empty():
            pinger_uuid = self.election_q.get()
            self.state_q.put(pinger_uuid)
            self.uuid_dict[pinger_uuid].election_q.put("I'm the leader")
        timeout = time.time() + self.ping_time
        while True:
            if time.time() > timeout:
                break
        self.respond_to_ping()

    def run(self):
        #print "Hi I'm bulb_" + str(self.id) + " And my queue size is: " + str(self.uuid_list.size()) + "\n"
        self.leader_election()






