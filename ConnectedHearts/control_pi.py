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

class Pi(Process):
    def __init__(self, hosts):
        """
        Initialize process, set environment variables

        :param hosts: a list of ssh connections
        :type hosts: list of strings
        """ 
        super(Pi, self).__init__()
        self.hosts = hosts

    def connect(self, host):
        """
        Set up a Paramiko SSH connection with the specified host; 
        Turn off all lightbulbs

        :param host: an ssh connections
        :type hosts: string (e.g. "192.168.1.20")
        """ 
        print "connecting to " + str(host)
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(host, username='ubnt', password='ubnt') 

        turn_all_off = "echo turning_all_off "
        for i in range(1,8):
            turn_all_off += "& echo 0 > /proc/power/relay" + str(i) + " "
        c.exec_command(turn_all_off)

    def run(self):
        """ 
        Process run function; start two SSH connections 
        """
        for host in self.hosts: 
            self.connect(host)
