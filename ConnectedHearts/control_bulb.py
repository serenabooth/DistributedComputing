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
        self.adjustment = Value('f', 0.0)
        self.time_of_last_blink = -1
        self.time_of_neighbor_below = -1
        self.time_of_neighbor_above = -1
        self.above_bulb_id = (self.id + 1) % 13
        self.below_bulb_id = (self.id - 1) % 13

        self.comp_time = datetime.datetime.now()
        self.comp_above_time = datetime.datetime.now()
        self.comp_below_time = datetime.datetime.now()

    def check_ordering(self):
        while True: 
            print "Here, " + str(self.id) + " and the leader is " + str(self.leader_id.value)
            if self.id != self.leader_id.value: 
                #print "I'm " + str(self.id) + " and my queue size is: " + str(self.state_q.size())
  
                print "I'm " + str(self.id) + " and my queue size is: " + str(self.bulb_objects_list[self.id].state_q.size())

                while not self.state_q.empty():
                    print "Something on my queue!"
                    message = self.state_q.get()
                    print "Message " + str(message)
                    time_received_message = datetime.datetime.now()

                    if message == self.above_bulb_id: 
                        self.time_of_neighbor_above = time_received_message
                    elif message == self.below_bulb_id: 
                        self.time_of_neighbor_below = time_received_message
                    else: 
                        self.time_of_last_blink = time_received_message

                if self.time_of_last_blink == self.comp_time:
                    #print self.time_of_last_blink.value
                    #self.adjustment.value = 0
                    time.sleep(0.5)
                    print "I am continuing"
                    continue

                # TODO: Fix this bad logic
                steps_to_above = 13
                steps_to_below = 13
                for i in range(1,12):
                    if (self.above_bulb_id + i) % 12 == leader_id:
                        steps_to_above = min(steps_to_above, i)
                    if (self.above_bulb_id - i) % 12 == leader_id:
                        steps_to_above = min(steps_to_above, i)

                    if (self.below_bulb_id + i) % 12 == leader_id:
                        steps_to_below = min(steps_to_below, i)
                    if (self.below_bulb_id - i) % 12 == leader_id:
                        steps_to_below = min(steps_to_below, i)

                if (steps_to_above < steps_to_below): 
                    closer_time = self.time_of_neighbor_above
                else:
                    closer_time = self.time_of_neighbor_below

                if (closer_time == self.comp_above_time or 
                        closer_time == self.comp_below_time):
                    time.sleep(0.5)
                    print "I am continuing"
                    continue
                # timedelta
                time_diff = self.time_of_last_blink - closer_time
                # convert timedelta to seconds
                microseconds = time_diff.microseconds

                if microseconds < 0:
                    self.adjustment.value = -0.05
                else:
                    self.adjustment.value = 0.05
                print "I, " + str(self.id) + " am making an adjustment of " + str(self.adjustment.value)
                
                self.comp_time = self.time_of_last_blink
                # self.comp_above_time = self.time_of_neighbor_above
                # self.comp_below_time = self.time_of_neighbor_below

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

    def __init__(self, my_id, bpm, host, adjustment, bulb_objects_list, above_neighbor, below_neighbor):
        super(BulbBlinker, self).__init__()
        self.bpm = bpm
        self.id = my_id
        self.host = host
        self.adjustment = adjustment
        self.bulb_objects_list = bulb_objects_list
        self.above_neighbor = above_neighbor
        self.below_neighbor = below_neighbor

    def send_message_to_neighbors(self):
        #print str(self.id) + ", Above length: " + str(self.bulb_objects_list[self.above_neighbor].state_q.size())
        #print str(self.id) + ", Below length: " + str(self.bulb_objects_list[self.below_neighbor].state_q.size())
        self.bulb_objects_list[self.above_neighbor].state_q.put("" + str(self.id))
        self.bulb_objects_list[self.below_neighbor].state_q.put("" + str(self.id))
        #print str(self.id) + ", Above length: " + str(self.bulb_objects_list[self.above_neighbor].state_q.size())
        #print str(self.id) + ", Below length: " + str(self.bulb_objects_list[self.below_neighbor].state_q.size())

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

        while True: 
            on_cmd_builder = "echo 1 > /proc/power/relay" + str(my_relay_id) + " "
            off_cmd_builder = "echo 0 > /proc/power/relay" + str(my_relay_id) + " "
            #print str(datetime.datetime.now()) + str(self.host) + " id: " + str(my_relay_id) + " on"
            (stdin, stdout, stderr) = c.exec_command(on_cmd_builder)
            # put my message on my own queue
            self.bulb_objects_list[self.id].state_q.put("" + str(self.id))
            # put my message on my neighbors queues
            self.send_message_to_neighbors()

            time.sleep(60.0 * 2/self.bpm) 

            #print str(datetime.datetime.now()) + str(self.host) + " id: " + str(my_relay_id) + " off"
            (stdin, stdout, stderr)  = c.exec_command(off_cmd_builder) 

            time.sleep(60.0 * 2/self.bpm + self.adjustment.value) 
            self.adjustment.value = 0

    def run(self):
        self.ssh_connection()
