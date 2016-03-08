from datetime import datetime
import time 
import socket
import sys
from threading import *
import Queue
import random

# cite: http://stackoverflow.com/questions/19846332/python-threading-inside-a-class
def threaded(fn):
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class Clock(Thread):
    # shared between all processes / logical clocks
    global socket_connections
    socket_connections = {}

    def __init__(self, id, ticks_per_min, logbook, port_client, port_server):
        Thread.__init__(self)
        print "Clock " + str(id) + " started"

        self.id = id
        self.ticks_per_min = ticks_per_min
        self.logbook = logbook

        self.clock_time = 0
        self.msg_queue = Queue.Queue()

        # keep track of the ports
        self.port_client = port_client
        self.port_server = port_server

        # # set up client (receiving) socket
        # self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.client.settimeout(None)

        global socket_connections
        socket_connections[str(self.id)] = self.port_server

    # @threaded 
    # def server_receive(self):
    #     print "TO DO"

    # @threaded
    # def listen_up(self, c, addr):
    #     print "accepting messages on server"
    #     data, addr_2 = c.recvfrom(1024)
    #     data = data.decode()
    #     print "trying to get data "
    #     #data = self.server.recvfrom(1024)
    #     if data: 
    #         self.msg_queue.put(data)
    #         print str(self.id) + " got some! " + data
    #         # does this work? 
    #     c.close()

    @threaded 
    def client_do_stuff(self):
        print "client time"
        #global socket_connections

        if not self.msg_queue.empty(): 
            self.receive_event()
        else: 
            if (not self.id == 1): 
                self.send_event(socket_connections['1'])
            else: 
                print "maybe that was the problem"
            # op = random.randint(1,10)
            # if op == 1: 
            #     print "to do"
            # elif op == 2: 
            #     print "to do"
            # elif op == 3: 
            #     print "to do"
            # else: 
            #     print "to do"
        # if queue has message, 
            # receive_event 
        # otherwise: 
            # generate value 1-10
            # if 1, 
                #   send to machine (a) 
                # + other stuff 
            # if 2
                # send to machine (b) 
                # + other stuff 
            # if 3 
                # send to both
                # + other stuff
            # if other, 
                # internal event.   


    def run(self):
        global socket_connections


        while True: 
            print str(datetime.now()) + ": Clock " + str(self.id) + " says hello"

            #print " connecting to server "
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(self.ticks_per_min)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.server.bind(('', self.port_server))
            except socket.error as msg:
                print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message : ' + str(msg[1])
                sys.exit()
            self.server.listen(10)
            # set up server (listening) socket

            try: 
                c, addr = self.server.accept()
                data, addr_2 = c.recvfrom(1024)
                data = data.decode()
                print "trying to get data "
                #data = self.server.recvfrom(1024)
                if data: 
                    self.msg_queue.put(data)
                    print str(self.id) + "got some! " + data
                    # does this work? 

                # should we close the connection? 
                # c.close()

            except Exception, e: 
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                print "exception: " + str(e)
                print "complete an instruction"
                self.client_do_stuff()


            # If the socket has timed out, restart the timeout, and perform an instruction.

    def log(self, msg=None):
        f = open(self.logbook, 'a')
        f.write(" System time: " + str(datetime.now()) + 
                            " Logical clock time: " + self.clock_time)
        f.close()

    def receive_event(self):
        # update clocktime based on received, then add 1
        print "RECEIVE - TO DO"

    def send_event(self, dst):

        try: 

            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(None)

            print "(TRYING) My id is " + str(self.id) 

            self.client.connect(('', dst))
            msg='HI OTHER SOCKET from ' + str(self.id)

            self.client.send(msg.encode())
            print "trying to send"
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
        except Exception, e: 
            print "try again"
            print "(EXCEPTING) My id is " + str(self.id) + str(e)
            #sys.exit()
            self.send_event(dst)

    def internal_event (self):
        self.clock_time += 1
        print "INTERNAL - TO DO"
