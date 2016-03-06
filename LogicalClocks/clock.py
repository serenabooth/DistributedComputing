import time
import socket
import sys
from threading import *

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

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.bind(('', port))
        except socket.error as msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message : ' + str(msg[1])
            sys.exit()
        self.s.listen(10)

        global socket_connections
        socket_connections[str(self.id)] = self.s 

    def run(self):
        while True: 
            print str(time.time()) + str(self.id) + " says hello"
            time.sleep(5)
            # c, addr = self.s.accept()
            # data = c.recv(1024)
            # if data: print data
            # c.close()

    def log(self):
        print "TO DO"

    def receive_event(self, msg):
        # update clocktime based on received, then add 1
        print "TO DO"

    def send_event(self, dst):
        #dst.s.send("Hello!")
        print dst.s
        sent = dst.s.send(b'Oi you sent something to me')
        if sent == 0:
            raise RuntimeError("socket connection broken")
        self.clock_time += 1
        print "TO DO"

    def internal_event (self):
        self.clock_time += 1
        print "TO DO"
