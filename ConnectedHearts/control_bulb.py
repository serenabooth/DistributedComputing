from datetime import datetime
import threading
import sys, os
import string, time, datetime, random, Queue
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
    def __init__(self, bpm, my_id, host):
        super(BulbControl, self).__init__()
        self.id = my_id
        self.bpm = bpm
        self.host = host

    def connect(self):
        print "connecting to " + self.host
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(self.host, username='ubnt', password='ubnt') 

        my_relay_id = int(self.id * 1.0 / 2)

        turn_myself_off = "echo 0 > /proc/relay" + str(my_relay_id)
        c.exec_command(turn_myself_off)

        while True: 
            #print on_cmd_builder
            #print off_cmd_builder
            print str(datetime.datetime.now()) + str(self.host) + " id: " + str(self.id) + " on"
            c.exec_command("echo 1 > /proc/relay" + str(my_relay_id))
            #for i in range(0,10):
            time.sleep(max(60 * 2 / self.bpm, 0.5)) #TO DO: set me to be the pulse
            #time.sleep(5)
            print str(datetime.datetime.now()) + str(self.host) + " id: " + str(self.id) + " off"
            c.exec_command("echo 0 > /proc/relay" + str(my_relay_id)) 
            #for i in range(0,10):
            time.sleep(max(60 * 2 / self.bpm, 0.5)) #TO DO: set me to be the pulse


    def run(self):
        self.connect()

