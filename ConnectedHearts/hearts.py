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
        self.new_election = False

        self.leader_socket = None
        self.leader_socket_port = 8000
        self.follower_socket = None
        #self.follower_socket_port = follower_socket_port
        #print self.follower_socket_port

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
        timeout = time.time() + 1
        while True:
            if time.time() > timeout:
                break
            if len(self.uuid_dict) == 12:
                self.leader = self.uuid_dict[max(self.uuid_dict.keys())]
        self.leader = self.uuid_dict[max(self.uuid_dict.keys())]
        print "id: " + str(self.id) + ", leader: " + str(self.leader.id) + "\n"
        if self.leader.id == self.id:
            print "Hi, I'm the leader: " + str(self.id) + "\n"
            self.set_up_leader_socket()
        else:
            print "Hi, I'm a follower: " + str(self.id) + "\n"
            connection_timeout = random.random()
            self.connect_to_leader_socket(connection_timeout, time.time())

    def set_up_leader_socket(self):
        try: 
            self.leader_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.leader_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.leader_socket.bind(('', self.leader_socket_port))
            except socket.error as msg:
                print "Bind failed. Error Code : " \
                        + str(msg[0]) + " Message : " + str(msg[1]) + "\n"
                sys.exit()
            self.leader_socket.listen(12)
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            print "Successfully started socket at port " + str(self.leader_socket_port) + "\n"
        except Exception, e: 
            print "Exception: " + str(e)
            self.set_up_leader_socket() 

    @threaded
    def connect_to_leader_socket(self, connection_timeout, start_time):
        if self.new_election: 
            print "New election started by someone else \n"
            return
        elif time.time() < start_time + connection_timeout:
            try:
                self.follower_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #print self.follower_socket_port
                #print type(self.follower_socket_port)
                self.follower_socket.connect(('', self.leader_socket_port))
                print "\n" + str(self.id) + str(self.id) + str(self.id) + " Sucessfully started follower socket for " + str(self.id) + "\n"
            except Exception, e:
                print "Connecting follower socket exception " + str(e) + "\n"
                self.connect_to_leader_socket(connection_timeout, start_time)
        else:
            self.new_election = True
            for bulb in self.bulb_list:
                bulb.new_election = True  
            print "Let's start a new leader election after timeout: " + str(connection_timeout) + "\n"
            return

    def run(self):
        print "Hi I'm bulb_" + str(self.id) + "\n"
        self.send_uuid()
        






