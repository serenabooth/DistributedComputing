from datetime import datetime
import threading
import sys, time, socket, random, os
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
    BulbQueue inherits from multiprocessing.Queue, but has the added 
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
    """ Creates a Bulb process which runs leader election """

    def __init__(self, id, turned_on_list, bpm, host):
        """
        Initializes a Bulb process

        :param id: The unique id of the bulb which acts as its name, ranges from 
        0 to 12
        :type id: long
        :param turned_on_list: Used to keep track of which bulbs are currently 
        turned on. The list is of length 13 with information about the status of 
        a particular bulb located at the index equal to its id.
        :type turned_on_list: multiprocessing.Array
        :type bpm: The pulse that the bulb should use when determining when to turn
        on and off. This is calculated using the webcame_pulse library. 
        :type bpm: int
        :param host: The ip address of the power strip that the bulb is physically
        plugged into.
        :type host: string
        :return: A Bulb Process
        :type return: Bulb()
        """
        super(Bulb, self).__init__()
        self.id = id

        # A random int used to determine the leader in leader election. With a 
        # high probability, these will be unique.
        self.uuid = random.randint(1,2**64-1)

        # A dict where the keys are the uuid of a bulb process and the values
        # are the bulb process object.
        self.uuid_dict = {}

        # A list of all the bulb process objects.
        self.bulb_objects_list = None

        # A list of bulb process objects that are a part of the current election
        # this is used in new_leader_election but not first_election.
        self.bulbs_in_election = None

        # The bulb process object of the leader
        self.leader = None

        # A multiprocessing.Value containing the id of the leader.
        self.leader_id = Value('i', -1)

        # A BulbQueue() used to communicate information related to leader election.
        self.election_q = BulbQueue()

        # A BulbQueue() used to communicate between neighbor bulbs.
        self.state_q = BulbQueue()

        # A random time that a bulb process will sleep before pinging the leader
        # or responding to pings. This is used to prevent 13 simultaneous while
        # loops and to introduce interesting time differences between bulb flashes.
        self.ping_time = random.randint(1,12)

        # This is the a max time that a bulb will wait for another bulb to respond.
        self.max_timeout = 15

        self.turned_on_list = turned_on_list
        self.bpm = bpm
        self.host = host

        if self.id == 0:
            self.uuid = 2**64-2

    def register_bulbs(self, bulb_objects_list):
        """
        Sets self.bulb_object_list equal to a list of all the bulb process 
        objects in the system.

        :param bulb_objects_list: A list of all the bulb process objects in the 
        system, which is passed in by the main thread.
        :type bulb_objects_list: list of Bulb()s
        :return: None
        """
        self.bulb_objects_list = bulb_objects_list
        self.create_uuid_dict()

    def send_uuid(self, bulbs):
        """
        The process self puts its uuid on the election_q of every bulb in bulbs.

        :param bulbs: The bulbs that self will send its uuid to.
        :type bulbs: list of Bulb()s
        :return: None
        """
        for bulb in bulbs:
            bulb.election_q.put(self.uuid)

    def create_uuid_dict(self):
        """
        Creates a dictionary of bulb uuid keys to the corresponding Bulb() object

        :return: None
        """
        for bulb in self.bulb_objects_list:
            self.uuid_dict[bulb.uuid] = bulb

    def get_max_uuid(self):
        """
        Finds the max uuid in the election_q

        :returns: The max uuid
        :type return: long
        """
        curr_max = self.election_q.get()
        while (self.election_q.size() > 0):
            curr_item = self.election_q.get()
            if (curr_item > curr_max):
                curr_max = curr_item
        return curr_max

    def print_q(self, q):
        """
        Gets all of the items in q and returns them as a list

        :param q: Any BulbQueue()
        :type q: BulbQueue()
        :return: A list of the contents of q
        :type return: list
        """
        q_contents = []
        while not q.empty():
            q_contents.append(q.get())
        return q_contents

    def empty_q(self, q):
        """
        Empties a BulbQueue()

        :param q: Any BulbQueue()
        :type q: BulbQueue()
        :return: None
        """
        while not q.empty():
            q.get()

    def send_new_election_msg(self):
        """
        Sets bulbs_in_election to a list of bulb objects with uuids higher than 
        self.uuid. Then self puts a new election message on the election_q of 
        all of these bulbs.

        :return: None
        """
        self.bulbs_in_election = [bulb for bulb in self.bulb_objects_list 
                                    if bulb.uuid > self.uuid 
                                    and bulb.uuid != self.uuid]
        for bulb in self.bulbs_in_election:
            bulb.election_q.put("New election from: " + str(self.uuid))

    def set_bulbs_in_new_election(self, uuid):
        """
        This sets bulbs_in_election to a list of all bulb objects with uuids greater
        or equal to uuid, excluding self. 

        :return: None
        """
        self.bulbs_in_election = [bulb for bulb in self.bulb_objects_list 
                                    if bulb.uuid >= uuid 
                                    and bulb.uuid != self.uuid]

    def first_leader_election(self):
        """
        A bulb process finds the max uuid in its election_q and then chooses
        the leader accordingly.

        Has the invariant that all bulbs know the uuid of all other bulbs that are
        running. 

        :return: None
        """
        self.leader = self.uuid_dict[self.get_max_uuid()]
        self.leader_id.value = self.leader.id
        print "Leader id: " + str(self.leader_id.value) + "\n"
        print "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n"
        if self.leader.id == self.id:
            print ("Hi, I'm the leader: " + str(self.id) + " Right? " + 
                    str(self.leader == self) + "\n")
            # turn myself on
            self.turn_on()
            # then respond to pings from followers
            self.respond_to_ping()
        else:
            print "Hi, I'm a follower: " + str(self.id) + "\n"
            # start a new process to check for when I should turn on
            p = Process(target=self.check_turn_on, args=())
            p.start()
            # start pinging the leader
            self.election_q.put("first ping")
            self.ping_leader()

    def check_turn_on(self):
        """
        Continuously checks to see if there is something on the state_q.
        If there is something on the state_q, that means that a neighbor has
        told it to turn on so it turns itself on.

        :return: None
        """
        while (self.state_q.empty()):
            time.sleep(1)
        self.state_q.get()
        self.turn_on()

    def turn_on(self):
        """
        Starts a new process called bulb_control and then signals to its neighbors
        that they should turn on.

        bulb_control handles anything related to physically turning the bulb on
        and off.

        :return: None
        """
        self.turned_on_list[self.id] = 1

        """bulb_control = BulbControl(  my_id = self.id,
                                    bpm = self.bpm, 
                                    host = self.host,
                                    leader_id = self.leader_id,
                                    state_q = self.state_q,
                                    bulb_objects_list = self.bulb_objects_list, 
                                    turned_on_list = self.turned_on_list)
        bulb_control.start()"""
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

    def signal_to_neighbors(self, list_of_neighbors):
        """ 
        Wait for ping_time and then tell neighbors to turn on

        :param list_of_neighbors: The bulb neighbors of self
        :type param: list of Bulb()s
        :return None:
        """
        time.sleep(self.ping_time)
        for neighbor in list_of_neighbors: 
            neighbor.state_q.put(1)

    def ping_leader(self):
        """
        Repeatedly ping the leader after waiting ping_time, if you have received 
        a message from the leader.

        If you receive a new election or new leader message, prepare for a new 
        leader election and return.

        If the leader does not respond after max_timeout, start a new election and
        return.

        :return: None
        """
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
            print ("I'm bulb " + str(self.id) + " and the leader responded: " + 
                str(msg) + "\n Also my timeout is " + str(self.ping_time) + "\n")
            self.leader.election_q.put(self.uuid)
        else:
            time.sleep(self.max_timeout - self.ping_time)
            if self.election_q.empty():
                print ("I'm bulb " + str(self.id) + 
                    " and Oh no the leader didn't respond \n")
                self.send_new_election_msg()
                return
        self.ping_leader()

    def respond_to_ping(self):
        """
        Respond to the pings of all the followers. Continuously get messages from
        your election_q and respond to pinger_uuid if the queue isn't empty.

        If the queue is empty, sleep for ping_time. 

        Then send a new leader message to all bulbs with a higher uuid than yourself 
        (this can be an empty list and thus no messages will be sent). This allows 
        any bulbs who restart to recover their status as leader.

        Then continue responding to pings.

        If you receive a new election or new leader message, prepare for a new 
        leader election and return.

        :return: None
        """
        print "Responding to pings"
        while not self.election_q.empty():
            pinger_uuid = self.election_q.get()
            if "New election" in str(pinger_uuid) or "New leader" in str(pinger_uuid):
                initiator_uuid = long(pinger_uuid.split(": ")[1])
                #print ("I'm bulb " + str(self.id) + " and bulb " + 
                    #str(self.uuid_dict[initiator_uuid].id) + 
                    #" told me there was a new election \n")
                self.set_bulbs_in_new_election(initiator_uuid)
                return 
            if self.id == 0:
                time.sleep(30000)         
            #print "I responded to bulb " + str(self.uuid_dict[pinger_uuid].id) + "\n")
            self.uuid_dict[pinger_uuid].election_q.put(self.uuid)
        time.sleep(self.ping_time)
        higher_uuid_bulbs = [bulb for bulb in self.bulb_objects_list 
                                if bulb.uuid > self.uuid]
        for bulb in higher_uuid_bulbs:
            bulb.election_q.put("New leader: " + str(self.uuid))
        self.respond_to_ping()

    def new_leader_election(self):
        """
        A slight modification to the Bully algorithm.

        This is run if a leader ever becomes non-responsive and a process receives
        a "new election" message on its election_q

        :return: None
        """
        new_leader = False
        timeout = time.time() + self.max_timeout
        responses = []
        # wait for responses from higher uuids for max_timeout 
        while time.time() < timeout:
            # if the election_q isn't empty, decide what to do with the msg
            if not self.election_q.empty():  
                msg = self.election_q.get()

                # if the msg is a new election, send your uuid to the appropriate bulbs
                if "New election" in str(msg):
                    initiator_uuid = long(msg.split(": ")[1])
                    bulbs_in_election = [bulb for bulb in self.bulb_objects_list 
                                            if bulb.uuid >= initiator_uuid and 
                                            bulb.uuid != self.uuid]
                    self.send_uuid(bulbs_in_election)

                # if you receive a new leader message
                elif "New leader" in str(msg):
                    leader_uuid = long(msg.split(": ")[1])
                    if self.uuid < leader_uuid:
                        # and your uuid is lower than the new leaders uuid
                        # then set leader to the new leader
                        self.leader = self.uuid_dict[leader_uuid]
                        new_leader = True
                        break
                else:
                    # add msg to responses if it is not already in responses
                    if msg not in responses:
                        responses.append(msg)

        # sort responses from lowest to highest uuid
        responses.sort()

        # this means you are the leader
        if not responses or self.uuid > responses[len(responses) - 1]:
            print ("Responses: " + str(responses) + " I'm the LEADER and I'm bulb " 
                + str(self.id) + "\n")
            print datetime.datetime.now()
            self.leader = self
            # send a new leader message to all of the bulbs
            for bulb in [bulb for bulb in self.bulb_objects_list if bulb is not self]:
                print "Sending to bulb " + str(bulb.id) + "\n"
                bulb.election_q.put("New leader: " + str(self.uuid))

            # empty your election_q before responding to pings
            self.empty_q(self.election_q)
            self.respond_to_ping()

        # this means you are not the leader
        else:
            print "I'm not the leader and I'm bulb " + str(self.id) + "\n"
            timeout = time.time() + 2 * self.max_timeout
            while time.time() < timeout:
                if not self.election_q.empty():
                    # if you receive a new leader message
                    if "New leader" in str(msg):
                        leader_uuid = long(msg.split(": ")[1])
                        if self.uuid < leader_uuid:
                            # and your uuid is lower than the new leaders uuid
                            # then set leader to the new leader
                            self.leader = self.uuid_dict[leader_uuid]
                            new_leader = True
                            break

            # empty your election_q
            self.empty_q(self.election_q)

            if new_leader:
                # if there is a new leader, wait max_timeout for it to start
                # responding to pings
                time.sleep(self.max_timeout)
                print ("I'm bulb " + str(self.id) + " and I think the leader is " 
                    + str(self.leader.id) + "\n")
                # then start pinging the new leader
                self.election_q.put("first ping")
                self.ping_leader()
            else:
                # if you never received a new leader message, start another election
                self.send_new_election_msg()
                return



    def run(self):
        """
        Runs the first leader election.

        After that returns, which means the first leader has crashed, uuids are sent
        to all the bulbs in the new election and a new leader election is started.

        The while True ensures that anytime a leader crashes or there is disagreement
        over the leader, a new leader election is run (since new_leader_election 
        only returns when the leader has crashed)

        :return: None
        """
        self.first_leader_election()
        #print ("I'm bulb " + str(self.id) + " and here are the bulbs in my new election " 
        # + str([bulb.id for bulb in self.bulbs_in_election]) + "\n")
        while True:
            self.send_uuid(self.bulbs_in_election)
            self.new_leader_election()







