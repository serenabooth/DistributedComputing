from datetime import datetime
import threading
import sys, os
import string, time, datetime, random
import uuid
from multiprocessing import Array, Process
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
        self.time_of_last_blink = datetime.datetime.now()

    def checkOrdering(self, bulbBlinkerObj):
        print "TO DO"

    def run(self):

        my_bulb = BulbBlinker(my_id = self.id,
                    bpm = self.bpm, 
                    host = self.host,
                    adjustment = self.adjustment)
        self.checkOrdering(my_bulb)




class BulbBlinker(Process):
    def __init__(self, my_id, bpm, host, adjustment):
        super(BulbBlinker, self).__init__()
        self.bpm = bpm
        self.id = my_id
        self.host = host
        self.adjustment = adjustment
        self.time_of_last_blink = time_of_last_blink

    def sshConnection(self):
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
            self.sendSignalToNeighbors()
            (stdin, stdout, stderr) = c.exec_command(on_cmd_builder)
            #for i in range(0,10):
            time.sleep(60.0/self.bpm) #TO DO: set me to be the pulse
            #time.sleep(5)
            print str(datetime.datetime.now()) + str(self.host) + " id: " + str(my_relay_id) + " off"
            (stdin, stdout, stderr)  = c.exec_command(off_cmd_builder) 
            #for i in range(0,10):
            time.sleep(60.0/self.bpm) #TO DO: set me to be the pulse


    def run(self):
        print "hai"