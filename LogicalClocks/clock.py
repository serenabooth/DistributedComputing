from datetime import datetime
import time 
import socket
import sys
from threading import *
import Queue
import random

class Clock(Thread):
    # shared between all processes / logical clocks
    global socket_connections
    socket_connections = {}

    def __init__(self, id, ticks_per_min, logbook, port):
        Thread.__init__(self)
        print "Clock " + str(id) + " started"

        self.id = id
        self.ticks_per_min = ticks_per_min
        self.logbook = logbook
        self.clock_time = 0

        self.msg_queue = Queue.Queue()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(self.ticks_per_min)
        try:
            self.s.bind(('', port))
        except socket.error as msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message : ' + str(msg[1])
            sys.exit()
        self.s.listen(10)

        global socket_connections
        socket_connections[str(self.id)] = self.s 

    def run(self):
        global socket_connections
        while True: 
            print str(datetime.now()) + str(self.id) + " says hello"

            #time.sleep(5)
            try: 
                # If the socket hasn't timed out, receive incoming messages.
                c, addr = self.s.accept()
                data = c.recv(1024)
                if data: self.msg_queue.append(data)
                c.close()
            except socket.timeout:
                # If the socket has timed out, restart the timeout, and perform an instruction.
                operation_instr = random.randint(1,3)
                if operation_instr == 1: 
                    self.send_event(socket_connections['1'])
                elif operation_instr == 2: 
                    self.receive_event()
                elif operation_instr == 3: 
                    self.internal_event()

                print "Exception! timed out!"

    def log(self, msg=None):
        f = open(self.logbook, 'a')
        f.write(" System time: " + str(datetime.now()) + 
                            " Logical clock time: " + self.clock_time)
        f.close()

    def receive_event(self):
        # update clocktime based on received, then add 1
        print "TO DO"

    def send_event(self, dst_socket):
        sent = dst_socket.send(b'Oi you sent something to me')
        if sent == 0:
            raise RuntimeError("socket connection broken")
        self.clock_time += 1
        print "TO DO"

    def internal_event (self):
        self.clock_time += 1
        print "TO DO"
