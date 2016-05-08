from datetime import datetime
import threading
import sys, os
import string, time, datetime, random
import uuid
from multiprocessing import Array, Process, Value
from multiprocessing.queues import Queue
import ctypes 
import paramiko

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

    def check_ordering(self, bulbBlinkerObj):
        while True: 
            if self.id != self.leader_id.value: 
                while not self.state_q.empty():
                    message = self.election_q.get()
                    time_received_message = datetime.datetime.now()

                    if message == self.above_bulb_id: 
                        self.time_of_neighbor_above = time_received_message
                    else: 
                        self.time_of_neighbor_below = time_received_message

                if self.time_of_last_blink == bulbBlinkerObj.time_of_last_blink:
                    self.adjustment.value = 0
                    continue

                self.time_of_last_blink = bulbBlinkerObj.time_of_last_blink

                steps_to_above = 13
                steps_to_below = 13
                for i in range(0,12):
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

                # timedelta
                time_diff = self.time_of_last_blink - closer_time
                # convert timedelta to seconds
                seconds = time_diff.total_seconds()
                self.adjustment.value = seconds / 3
            else: 
                print "I am the leader, so I will not adjust my timing"

    def run(self):
        my_bulb = BulbBlinker(my_id = self.id,
                    bpm = self.bpm, 
                    host = self.host,
                    adjustment = self.adjustment,
                    bulb_objects_list = self.bulb_objects_list, 
                    above_neighbor = self.above_bulb_id, 
                    below_neighbor = self.below_bulb_id)
        my_bulb.start()
        self.check_ordering(my_bulb)



class BulbBlinker(Process):
    def __init__(self, my_id, bpm, host, adjustment, bulb_objects_list, above_neighbor, below_neighbor):
        super(BulbBlinker, self).__init__()
        self.bpm = bpm
        self.id = my_id
        self.host = host
        self.adjustment = adjustment
        self.time_of_last_blink = -1
        self.bulb_objects_list = bulb_objects_list
        self.above_neighbor = above_neighbor
        self.below_neighbor = below_neighbor

    def send_message_to_neighbors(self):
        self.bulb_objects_list[self.above_neighbor].state_q.put("" + str(self.id))
        self.bulb_objects_list[self.above_neighbor].state_q.put("" + str(self.id))

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
        print turn_myself_off

        while True: 
            on_cmd_builder = "echo 1 > /proc/power/relay" + str(my_relay_id) + " "
            off_cmd_builder = "echo 0 > /proc/power/relay" + str(my_relay_id) + " "
            print str(datetime.datetime.now()) + str(self.host) + " id: " + str(my_relay_id) + " on"
            (stdin, stdout, stderr) = c.exec_command(on_cmd_builder)
            self.send_message_to_neighbors()

            self.time_of_last_blink = datetime.datetime.now()

            time.sleep(60.0/self.bpm) 

            print str(datetime.datetime.now()) + str(self.host) + " id: " + str(my_relay_id) + " off"
            (stdin, stdout, stderr)  = c.exec_command(off_cmd_builder) 

            time.sleep(60.0/self.bpm + self.adjustment.value) 


    def run(self):
        self.ssh_connection()
