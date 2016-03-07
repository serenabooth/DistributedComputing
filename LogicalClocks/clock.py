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

        # set up client (receiving) socket
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(None)


        global socket_connections
        socket_connections[str(self.id)] = self.client

    # @threaded 
    # def server_receive(self):
    #     print "TO DO"


    @threaded 
    def client_do_stuff(self):
        operation_instr = 1 #random.randint(1,3)
        if operation_instr == 1: 
            self.send_event(socket_connections['1'])
        elif operation_instr == 2: 
            self.receive_event()
        elif operation_instr == 3: 
            self.internal_event()

    def run(self):
        global socket_connections

        while True: 
            print str(datetime.now()) + ": Clock " + str(self.id) + " says hello"

            print "connecting to server"

            # set up server (listening) socket
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(self.ticks_per_min)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.server.bind(('', self.port_server))
            except socket.error as msg:
                print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message : ' + str(msg[1])
                sys.exit()
            self.server.listen(10)

            try: 
                print "accepting messages on server"
                c, addr = self.server.accept()
                data, addr_2 = c.recvfrom(1024)
                print "trying to get data "
                #data = self.server.recvfrom(1024)
                if data: 
                    self.msg_queue.append(data)
                    print "got some! " + data
                    # does this work? 
                c.close()

            except Exception, e: 
                self.server.close()
                print "exception" + str(e)
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
        #self.s.settimeout(10)
        print "trying to send"
        # try: 
        #     c, addr = dst.accept()
        #     print "c " + c
        #     print "addr " + addr
        #     msg = 'Hello other logical clock'
        #     sent = c.send(msg)
        #     if sent == 0:
        #         raise RuntimeError("socket connection broken")
        #     c.close()
        # except socket.timeout: 
        #     print "During send, socket timeout"
        # self.clock_time += 1
        # print "SEND - TO DO"

    def internal_event (self):
        self.clock_time += 1
        print "INTERNAL - TO DO"
