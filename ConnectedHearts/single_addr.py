from datetime import datetime
import threading
import sys, os
import string, time, datetime, random
import uuid
from multiprocessing import Array, Process
from multiprocessing.queues import Queue
import ctypes 
import paramiko

hosts = ["192.168.1.20", "192.168.1.21"]

c_20 = paramiko.SSHClient()
c_20.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c_20.connect(hosts[0], username='ubnt', password='ubnt') 

c_21 = paramiko.SSHClient()
c_21.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c_21.connect(hosts[1], username='ubnt', password='ubnt') 

turn_all_off = ""

for i in range(1,8):
        turn_all_off += "& echo 0 > /proc/power/relay" + str(i) + " "

turn_all_on = ""

for i in range(1,8):
        turn_all_on += "& echo 1 > /proc/power/relay" + str(i) + " "

while True: 
    c.exec_command(turn_all_off)
    time.sleep(1)
    c.exec_command(turn_all_on)
    time.sleep(1)