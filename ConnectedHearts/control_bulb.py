from datetime import datetime
import threading
import sys, os
import string, time, datetime, random
import uuid
from multiprocessing import Array, Process, Value
from multiprocessing.queues import Queue
import ctypes 
import paramiko
from ctypes import c_char_p
from hearts import BulbQueue


"""
    Code outline based on: StackOverflow Question 3485428
    "Creating multiple SSH connections at a time using Paramiko"
"""

class BulbControl(Process):
    def __init__(self, my_id, bpm, host, leader_id, state_q, bulb_objects_list):
        super(BulbControl, self).__init__()
        self.id = my_id
        self.bpm = bpm
        self.host = host
        self.leader_id = leader_id
        self.state_q = state_q
        self.bulb_objects_list = bulb_objects_list
        self.adjustment = Queue()
        self.time_of_last_blink = datetime.datetime.now()
        self.time_of_neighbor_below = datetime.datetime.now()
        self.time_of_neighbor_above = datetime.datetime.now()
        self.above_bulb_id = (self.id + 1) % 13
        self.below_bulb_id = (self.id - 1) % 13

        self.comp_time = datetime.datetime.now()
        self.comp_above_time = datetime.datetime.now()
        self.comp_below_time = datetime.datetime.now()

    def check_ordering(self):

        array_of_queues = [BulbQueue(), BulbQueue(), BulbQueue()]

        while True: 
            #print "Here, " + str(self.id) + " and the leader is " + str(self.leader_id.value)
            if self.id != self.leader_id.value: 
                #print "I'm " + str(self.id) + " and my queue size is: " + str(self.state_q.size())
  
                #print "I'm " + str(self.id) + " and my queue size is: " + str(self.state_q.size())

                while not self.state_q.empty():
                    #print "Something on my queue!"
                    message = self.state_q.get()
                    time_received_message = datetime.datetime.now()

                    if message == str(self.above_bulb_id): 
                        array_of_queues[2].put(time_received_message)
                        #self.time_of_neighbor_above = time_received_message
                        #print "ABOVE NEIGHBOR"
                    elif message == str(self.below_bulb_id): 
                        array_of_queues[0].put(time_received_message)

                        #self.time_of_neighbor_below = time_received_message
                        #print "BELOW NEIGHBOR"
                    else: 
                        array_of_queues[1].put(time_received_message)

                        #self.time_of_last_blink = time_received_message
                        #print "MY OWN"

                    if (not array_of_queues[0].empty() and 
                            not array_of_queues[1].empty() and 
                            not array_of_queues[2].empty()):
                        break

                if (not array_of_queues[0].empty() and 
                            not array_of_queues[1].empty() and 
                            not array_of_queues[2].empty()):
                    self.time_of_neighbor_below = array_of_queues[0].get()
                    self.time_of_last_blink  = array_of_queues[1].get()
                    self.time_of_neighbor_above = array_of_queues[2].get()

                    # TODO: Fix this bad logic
                    steps_to_above = 13
                    steps_to_below = 13
                    for i in range(0,12):
                        if (self.above_bulb_id + i) % 12 == self.leader_id.value:
                            steps_to_above = min(steps_to_above, i)
                        elif (self.above_bulb_id - i) % 12 == self.leader_id.value:
                            steps_to_above = min(steps_to_above, i)

                        if (self.below_bulb_id + i) % 12 == self.leader_id.value:
                            steps_to_below = min(steps_to_below, i)
                        elif (self.below_bulb_id - i) % 12 == self.leader_id.value:
                            steps_to_below = min(steps_to_below, i)

                    #print "I am " + str(self.id) + " and my above is  " + str(steps_to_above) + " steps from the leader"

                    if (steps_to_above < steps_to_below): 
                        closer_time = self.time_of_neighbor_above
                    else:
                        closer_time = self.time_of_neighbor_below
                    
                    #print "My time: " + str(self.time_of_last_blink)
                    #print "My neighbors time: " + str(closer_time)
                    #print "Closer? " + str(closer_time)

                    # timedelta
                    # if time_of_last_blink comes after, this is >0
                    # otherwise < 0
                    time_diff = self.time_of_last_blink - closer_time
                    # convert timedelta to seconds
                    seconds = time_diff.total_seconds()

                    self.adjustment.put(seconds/2.0)
                    print "I, " + str(self.id) + " NEED an adjustment of " + str(self.adjustment.value)
                        
            else: 
                time.sleep(5)

    def run(self):
        my_bulb = BulbBlinker(my_id = self.id,
                    bpm = self.bpm, 
                    host = self.host,
                    adjustment = self.adjustment,
                    bulb_objects_list = self.bulb_objects_list, 
                    above_neighbor = self.above_bulb_id, 
                    below_neighbor = self.below_bulb_id)
        my_bulb.start()
        self.check_ordering()


class BulbBlinker(Process):

    def __init__(self, 
                        my_id, 
                        bpm, 
                        host, 
                        adjustment, 
                        bulb_objects_list, 
                        above_neighbor, 
                        below_neighbor):
        super(BulbBlinker, self).__init__()
        self.id = my_id
        self.bpm = bpm
        self.host = host
        self.adjustment = adjustment
        self.bulb_objects_list = bulb_objects_list
        self.above_neighbor = above_neighbor
        self.below_neighbor = below_neighbor

    def send_message_to_neighbors(self):
        self.bulb_objects_list[self.id].state_q.put("" + str(self.id))
        self.bulb_objects_list[self.above_neighbor].state_q.put("" + str(self.id))
        self.bulb_objects_list[self.below_neighbor].state_q.put("" + str(self.id))

    def ssh_connection(self):
        print "connecting to " + self.host
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(self.host, username='ubnt', password='ubnt') 
        print c

        my_relay_id = int(self.id * 1.0 / 2) + 1

        turn_myself_off = "echo 0 > /proc/power/relay" + str(my_relay_id) + " "
        (stdin, stdout, stderr) = c.exec_command(turn_myself_off)
        print "Stdout: " + str(stdout.readlines())
        #print turn_myself_off
        if 60 * 2/self.bpm - 1.2 > 0: 
            time.sleep(60 * 2/self.bpm - 1.2)        

        while True: 
            if not self.adjustment.empty():
                adjustment_value = self.adjustment.get()
            print "I, " + str(self.id) + " am making an adjustment of " + str(adjustment_value)
            # tmp = 0
            # if self.adjustment.value < 0: 
            #     time.sleep(abs(self.adjustment.value))
            # else: 
            #     tmp = self.adjustment.value
            #print str(self.host) + "Turning on/off " + str(my_relay_id)
            on_cmd_builder = "echo 1 > /proc/power/relay" + str(my_relay_id) + " "
            off_cmd_builder = "echo 0 > /proc/power/relay" + str(my_relay_id) + " "

            if adjustment_value < 0:
                time.sleep(abs(self.adjustment.value))
            #print str(datetime.datetime.now()) + str(self.host) + " id: " + str(my_relay_id) + " on"
            (stdin, stdout, stderr) = c.exec_command(on_cmd_builder)
            # put my message on my neighbors queues
            #if self.adjustment.value > 0: 
            #    time.sleep(abs(self.adjustment.value))
            #self.send_message_to_neighbors()

            time.sleep(60.0 * 2/self.bpm) 

            #print str(datetime.datetime.now()) + str(self.host) + " id: " + str(my_relay_id) + " off"
            (stdin, stdout, stderr)  = c.exec_command(off_cmd_builder) 

            if adjustment_value > 0: 
                tmp = 60.0 * 2/self.bpm - abs(adjustment_value)
                if tmp > 0:
                    time.sleep(tmp)

            self.send_message_to_neighbors() 

    def run(self):
        self.ssh_connection()
