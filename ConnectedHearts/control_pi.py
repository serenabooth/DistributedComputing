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

class Pi(Process):
    def __init__(self, bpm, turned_on_list, hosts, face_visible):
        super(Pi, self).__init__()
        self.bpm = bpm
        self.sleep_time = max(60 * 2/bpm, 0.5) 
        self.turned_on_list = turned_on_list
        self.hosts = hosts
        self.face_visible = face_visible

    def connect(self, host):
        for i in range(0, 12):
            print str(i) + "is on? " + str(self.turned_on_list[i])
        print "connecting to " + host
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username='ubnt', password='ubnt') 

        turn_all_off = "echo turning_all_off "
        for i in range (1,7):
            turn_all_off += "&& echo 0 > /proc/power/relay" + str(i) + " "
        for i in range(7,9):
            turn_all_off += "&& echo 1 > /proc/power/relay" + str(i) + " "
        c.exec_command(turn_all_off)

        while self.face_visible: 
            on_cmd_builder = "echo turning_on "
            off_cmd_builder = "echo turning_off "
            for i in range(0,7):
                chk_on = i
                if (host == "192.168.1.21" and i == 6):
                    continue
                if (host == "192.168.1.21"):
                    chk_on = i * 2 + 1 
                if self.turned_on_list[chk_on] == 1:
                    on_cmd_builder += "&& echo 1 > /proc/power/relay" + str(i+1) + " "
                    off_cmd_builder += "&& echo 0 > /proc/power/relay" + str(i+1) + " "

            #print on_cmd_builder
            #print off_cmd_builder
            print str(datetime.datetime.now()) + str(host) + " on"
            c.exec_command(on_cmd_builder)
            #for i in range(0,10):
            time.sleep(self.sleep_time) #TO DO: set me to be the pulse
            #time.sleep(5)
            print str(datetime.datetime.now()) + str(host) + " off"
            c.exec_command(off_cmd_builder) 
            #for i in range(0,10):
            time.sleep(self.sleep_time) #TO DO: set me to be the pulse


    def run(self):
        outlock = threading.Lock() 
        # connect via ssh to both power strips
        threads = []
        for h in self.hosts:
            t = threading.Thread(target = self.connect, args=(h,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        while True: 

            print "I am running"
            time.sleep(5)

