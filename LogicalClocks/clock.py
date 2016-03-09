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
        print "Clock " + str(id) + " started with clock time " + str(ticks_per_min)

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
        socket_connections[self.id] = self.port_server

        #time.sleep(ticks_per_min)

    @threaded 
    def client_do_stuff(self):
        #print "client time"
        #global socket_connections

        # if not self.msg_queue.empty(): 
        #     self.receive_event()
        # else: 
        op = 3 # random.randint(1,10)

        set_of_clocks_excluding_me = socket_connections.keys()
        set_of_clocks_excluding_me.remove(self.id)

        if op == 1: 
            self.send_event([socket_connections[set_of_clocks_excluding_me[0]]])
            self.clock_time += 1
            print "Sending from " + str(self.id) + " to " + str(set_of_clocks_excluding_me[0])
        elif op == 2: 
            self.send_event([socket_connections[set_of_clocks_excluding_me[1]]])
            self.clock_time += 1
            print "Sending from " + str(self.id) + " to " + str(set_of_clocks_excluding_me[1])
        elif op == 3: 
            dsts = [socket_connections[clock_id] for clock_id in set_of_clocks_excluding_me] 
            self.send_event(dsts)
            self.clock_time += 1
            print "Sending from " + str(self.id) + " to both" 
        else: 
            print "to do"

    def start_server_socket(self):
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(self.ticks_per_min)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.server.bind(('', self.port_server))
            except socket.error as msg:
                print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message : ' + str(msg[1])
                sys.exit()
            self.server.listen(10)
        except Exception, e: 
            print "Exception: " + str(e)
            self.start_server_socket() 

    def run(self):
        global socket_connections

        self.start_server_socket()

        while True: 
            #print str(datetime.now()) + ": Clock " + str(self.id) + " says hello"

            #print " connecting to server "
    
            # set up server (listening) socket

            try: 
                start_time = time.time() 

                c, addr = self.server.accept()
                data, addr_2 = c.recvfrom(1024)

                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()

                end_time = time.time() 


                self.start_server_socket()

                #print "Ticks: " + str(self.ticks_per_min) + " Time diff: " + str(end_time - start_time)
                #print self.server.gettimeout()
                data = data.decode()
                # print "trying to get data "
                #data = self.server.recvfrom(1024)
                if data: 
                    self.msg_queue.put(data)
                    print str(self.id) + " got some! " + data
                    # does this work? 

                # should we close the connection? 
                # c.close()

            except Exception, e: 
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                print "exception: " + str(e)
                print "complete an instruction"
                self.client_do_stuff()

                self.start_server_socket()

            # If the socket has timed out, restart the timeout, and perform an instruction.

    def log(self, msg=None):
        f = open(self.logbook, 'a')
        f.write(" System time: " + str(datetime.now()) + 
                            " Logical clock time: " + self.clock_time)
        f.close()

    def receive_event(self):
        # update clocktime based on received, then add 1
        print "RECEIVE - TO DO"

    def send_event(self, dsts):
        for dst in dsts: 
            try: 
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.settimeout(None)
                self.client.connect(('', dst))
                #print "(TRYING) My id is " + str(self.id) 
                msg="" + str(self.id) + ": " + str(self.clock_time)

                self.client.send(msg.encode())
                #print "trying to send"
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
            except Exception, e: 
                print "(EXCEPTING) My id is " + str(self.id) + str(e)
                self.send_event([dst])

    def internal_event (self):
        self.clock_time += 1
        print "INTERNAL - TO DO"
