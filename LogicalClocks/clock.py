import time

class Clock():
    def __init__(self, id, ticks_per_min, logbook):
        self.id = id
        self.ticks_per_min = ticks_per_min
        self.logbook = logbook

        self.clock_time = 0
        self.socket_connections = []
        print "TO DO"

    def init_socket_connections(self):
        print "TO DO"

    def log(self):
        print "TO DO"

    def receive_event(self, msg):
        # update clocktime based on received, then add 1
        print "TO DO"

    def send_event(self, msg):
        self.clock_time += 1
        print "TO DO"

    def internal_event (self):
        self.clock_time += 1
        print "TO DO"
