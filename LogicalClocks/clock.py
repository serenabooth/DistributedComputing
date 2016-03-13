from datetime import datetime
from threading import *
import sys, time, socket, random, Queue


# cite: http://stackoverflow.com/questions/19846332/python-threading-inside-a-class
def threaded(fn):
    """ Creates a new thread to run the function fn """
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class Clock(Thread):
    """ Sets up a machine """
    # shared between all processes / logical clocks
    # keeps track of server connections that can be binded to
    global socket_connections
    socket_connections = {}

    def __init__(self, id, ticks_per_min, logbook, port_client, port_server):
        """ 
        Initialize a clock that runs at the speed of ticks_per_min (a random
        number between 1 and 6 determined in main.py).
        Set the log file to logbook, the client socket port to port_client,
        and the server socket port to port_sever.
        The client socket will be used to connect to other servers and the 
        server socket will be listening for connections.
        """
        print "Clock " + str(id) + " started with clock time " + str(ticks_per_min)

        self.id = id
        self.ticks_per_min = ticks_per_min
        self.logbook = logbook

        f = open(self.logbook, 'a')
        f.write("\n\n\n\n\n\n\n\n STARTUP " + str(datetime.now()) + 
                " with clock time " + str(ticks_per_min) + "\n")
        f.close()

        # the current logical clock time for this particular clock
        self.clock_time = 0
        # a queue of all the messages received by this clock that have not
        # yet been processed
        self.msg_queue = Queue.Queue()

        # keep track of the ports
        self.port_client = port_client
        self.port_server = port_server

        global socket_connections
        socket_connections[self.id] = self.port_server

        Thread.__init__(self)

    @threaded 
    def perform_random_action(self):
        """
        Perform a random action unless there is a message in msg_queue. 
        The probability of each action is defined by the assignment specification.
        """
        if not self.msg_queue.empty(): 
            self.receive_event()
        else: 
            op = random.randint(1,10)

            # create a list that includes all the server ports except the
            # server port for this clock
            set_of_clocks_excluding_me = socket_connections.keys()
            set_of_clocks_excluding_me.remove(self.id)

            # send a message to clock A
            if op == 1: 
                self.send_event([set_of_clocks_excluding_me[0]])
            # send a message to clock B
            elif op == 2: 
                self.send_event([set_of_clocks_excluding_me[1]])
            # send a message to clocks A and B
            elif op == 3: 
                self.send_event(set_of_clocks_excluding_me)
            # internal event
            else: 
                self.internal_event()


    def start_server_socket(self, time):
        """ 
        Start up the server socket with a timeout of time, binding it to 
        self.port_server. 
        """
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(time)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.server.bind(('', self.port_server))
            except socket.error as msg:
                print "Bind failed. Error Code : " + str(msg[0]) + " Message : " 
                        + str(msg[1])
                sys.exit()
            self.server.listen(10)
        except Exception, e: 
            print "Exception: " + str(e)
            self.start_server_socket() 

    def run(self):
        """
        Start up the server socket and accept connections for self.ticks_per_min.
        When the socket times out, perform a random action in a new thread and 
        start up the server socket again.
        """
        global socket_connections

        self.start_server_socket(self.ticks_per_min)

        while True: 

            try: 
                # keep track of the time that the server started
                start_time = time.time() 
                c, addr = self.server.accept()
                data, addr_2 = c.recvfrom(1024)

                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()

                # keep track of the time that the server finishes receiving
                # a request
                end_time = time.time() 

                # set the timeout of the server to end_time - start_time to get
                # around the GIL
                self.start_server_socket(end_time - start_time)

                data = data.decode()

                # add the received message to the msg_queue
                if data: 
                    self.msg_queue.put(data)
                    print str(self.id) + " got some! " + data

            except Exception, e:
                # shutdown the server first 
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                print "exception: " + str(e)
                print "complete an instruction"
                self.perform_random_action()

                self.start_server_socket(self.ticks_per_min)

    def log(self, msg=None):
        """ Writes the appropriate information to the clock log """
        f = open(self.logbook, 'a')
        if msg: 
            f.write(" System time: " + str(datetime.now()) + 
                    " Logical clock time: " + str(self.clock_time) + 
                    " " + str(msg) + '\n')
        # if it is an internal event just write the system time and current
        # logical clock time
        else:
            f.write(" System time: " + str(datetime.now()) + 
                    " Logical clock time: " + str(self.clock_time) + '\n')
        f.close()

    def connect_client_socket(self, dst):
        """ Starts up the client socket with no timeout, binded to the port dst """
        try: 
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(None)
            self.client.connect(('', dst))
        except Exception, e:
            print "Connecting to client socket exception " + str(e) 
            self.connect_client_socket(dst)

    def send_event_helper(self, dsts):
        """ 
        Attempt to connect to each dst in dsts and send a message, one at a time. 
        Retry the connection if the server is not available.
        """
        # for each server in dsts
        for dst in dsts: 
            # connect the client socket to the server
            self.connect_client_socket(dst)

            # attempt to send a message with the clock id and logical clock time
            # shutdown the server when finished
            try: 
                msg="" + str(self.id) + ": " + str(self.clock_time)
                self.client.send(msg.encode())
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
            # if message is not sent, recursively attempt to send it again
            except Exception, e: 
                print "(EXCEPTING) My id is " + str(self.id) + str(e)
                self.send_event_helper([dst])       

    def send_event(self, dsts):
        """ Sends a message to dsts, which can be one machine or multiple """
        # get a list of the port numbers to send a message to
        if dsts: 
            dsts = [socket_connections[clock_id] for clock_id in dsts] 

            self.send_event_helper(dsts)

            # keep track of the logical clock time when the message was sent
            # so that it can be put in the log
            cur_time = self.clock_time

            # update the logical clock time
            self.clock_time += 1

            # log sending the message
            self.log(" Sending to " + str(dsts) + " at LC time: " + str(cur_time))

    def receive_event(self):
        """ 
        Process a received message by putting it into msg_queue and updating the
        logical clock time appropriately.
        """
        msg = self.msg_queue.get()

        # get the logical clock time of the machine that sent the message
        other_system_clock = msg[msg.index(":") + 1:] 
        
        # set the clock time to the maximum of self's clock time and other 
        # system's clock time
        self.clock_time = max(self.clock_time, int(other_system_clock))

        # increment the logical clock time and log that a message was received
        self.clock_time += 1
        self.log(" Received message from " + str(msg[:msg.index(":")]) + 
                    " with LC time " + str(msg[msg.index(":") + 2:]) + 
                    "; messages left to process: " + str(self.msg_queue.qsize()))

    def internal_event (self):
        """ 
        Perform an internal event, which just increases the logical clock time
        and logs the the current system time and logical clock time.
        """
        self.clock_time += 1
        self.log()
