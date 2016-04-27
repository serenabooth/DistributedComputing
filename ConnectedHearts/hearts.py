from datetime import datetime
import multiprocessing
import threading
import sys, time, socket, random, Queue
import uuid

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

class BulbQueue(Queue.Queue, object):
    def __init__(self):
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

class Bulb(multiprocessing.Process):
    def __init__(self, id):
        super(Bulb, self).__init__()
        self.id = id
        self.uuid = uuid.uuid4()
        self.uuid_dict = {}
        self.bulb_list = None
        self.leader = None
        self.new_election = False
        self.uuid_q = BulbQueue()
        self.task_q = BulbQueue()

        self.uuid_dict[self.uuid] = self

    def register_bulbs(self, all_bulb_objects):
        self.bulb_list = all_bulb_objects

    def send_uuid(self):
        #print "Is the thread getting here? \n"
        for bulb in self.bulb_list:
            #print "Here's my id: " + str(bulb.id) + "\n"
            bulb.uuid_q.put(self.uuid)
            bulb.uuid_dict[self.uuid] = self
            #print "I'm bulb " + str(bulb.id) +  " What about here? The dict: " + str(bulb.uuid_dict) + "\n"

    def create_queue_copy(self, q):
        q_copy = BulbQueue()
        for i in q.queue:
            q_copy.put(i)
        return q_copy

    def get_max_uuid(self):
        q = self.create_queue_copy(self.uuid_q)
        curr_uuid = q.get()
        curr_max = curr_uuid
        while not q.empty():
            curr_uuid = q.get()
            if curr_uuid > curr_max:
                curr_max = curr_uuid
        return curr_max

    def add_to_task_q(self, item):
        self.task_q.put(item)

    """def print_leader_q(self):
        print "Am I getting here? \n"
        while not self.task_q.empty():
            print "What about here? \n"
            sys.stderr.write(self.task_q.get())"""

    #@threaded
    def leader_election(self):
        #print "is this working? \n"
        self.leader = None
        timeout = time.time() + 1
        while True:
            if time.time() > timeout:
                break
            if self.uuid_q.size() == 12:
                #print "Before timeout. My uuid queue: " + str(self.uuid_q.size()) + "\n"
                #print "Do I ever get here? \n"
                break
        self.leader = self.uuid_dict[self.get_max_uuid()]
        #print "After timeout. My uuid queue: " + str(self.uuid_q.size()) + "\n"
        #print "Or here? " + str(self.leader.id) + "\n" 
        """if (self == self.leader):
            sys.stderr.write("I actually exited. I'm the leader. " + "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n")
            return"""
        #print "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n"
        #sys.stderr.write("id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n")
        self.new_election = False
        if self.leader.id == self.id:
            print "Hi, I'm the leader: " + str(self.id) + " Right? " + str(self.leader == self) + "\n"
            timeout = time.time() + 5
            while True:
                #print "Leader. Here's my queue size: " + str(self.task_q.size())
                if time.time() > timeout:
                    break
            #self.print_leader_q()
            #self.set_up_leader_socket()
        else:
            print "Hi, I'm a follower: " + str(self.id) + "\n"
            self.send_msg_to_leader(str(self.id))
            #self.connect_to_leader_socket(connection_timeout, time.time())
        #sys.stderr.write("Number of bulbs in dict: " + str(len(self.uuid_dict)) + " I'm thread " + str(self.id) + "\n")
        #self.ping_leader_socket()
        #print "I got here and I'm bulb " + str(self.id) + "\n"

    def send_msg_to_leader(self, msg):
        print "Send leader msg to " + str(self.leader.id) + "\n"
        for bulb in self.bulb_list:
            if bulb.id == self.leader.id:
                bulb.add_to_task_q(msg)
                print "My queue size: " + str(bulb.task_q.size()) + "\n"
        #print "Leader task queue: " + str(self.leader.task_q.size()) + " My task queue: " + str(self.task_q.size()) + " My uuid queue: " + str(self.uuid_q.size()) + "\n"

    def run(self):
        print "Hi I'm bulb_" + str(self.id) + " And my queue size is: " + str(self.uuid_q.size()) + "\n"
        self.leader_election()






