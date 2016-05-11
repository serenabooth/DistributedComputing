from datetime import datetime
import threading
import sys, os
import string, time, datetime, random
import uuid
from multiprocessing import Array, Process
from multiprocessing.queues import Queue
import ctypes 
import paramiko
import signal

class BulbBlinker(Process):
    
    def __init__(self, 
                    my_id, 
                    bpm, 
                    host, 
                    adjustment, 
                    bulb_objects_list, 
                    above_neighbor, 
                    below_neighbor, 
                    turned_on_list):
        """ 
        Initialize BulbBlinker
        """
        super(BulbBlinker, self).__init__()
        self.id = my_id
        self.bpm = bpm
        self.host = host
        self.adjustment = adjustment
        self.bulb_objects_list = bulb_objects_list
        self.above_neighbor = above_neighbor
        self.below_neighbor = below_neighbor
        self.turned_on_list = turned_on_list
        
        self.on = 0
        self.ppid = os.getppid()
        
        self.my_relay_id = int(self.id * 1.0 / 2) + 1
        
    def send_message_to_neighbors(self):
        """
        Check all bulbs are on (using turned_on_list) 
        Put self.id on state_q's of self as well as of neighboring bulbs 
        """
        # Check that all bulbs are on (and pulsing)
        # If so, set self.on to true.
        if self.on == 0:
            tmp = 1
            for i in range(0,13):
                if self.turned_on_list[i] != 1:
                    tmp = 0
            
            if tmp == 1: 
                self.on = 1
                print "Everyone turned on!"

        # Send messages to neighbors
        if self.on == 1: 
            self.bulb_objects_list[self.id].state_q.put(str(self.id))
            self.bulb_objects_list[self.above_neighbor].state_q.put(str(self.id))
            self.bulb_objects_list[self.below_neighbor].state_q.put(str(self.id))
            
            if self.id == 1:
                print ("=========================================================" + 
                       "===================\nAdded messages to self and neighbor state_qs " +
                       str(datetime.datetime.now()))

    def back_and_forth_forever(self):
        """
        Continue blinking 
        - Connect to Ubiquiti box over ssh once
        - forever, blink. Adjust time based on messages sent by parent process
        - After blinking, send message to neighboring bulbs
        """
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(self.host, username='ubnt', password='ubnt') 
        
        while True:          
            if os.getppid() == 1: 
                print " I SHOULD BE TERMINATINGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
                sys.exit()
            adjustment_value = 0
            while not self.adjustment.empty():
                adjustment_value = self.adjustment.get()
        
            on_cmd_builder = "echo 1 > /proc/power/relay" + str(self.my_relay_id) + " "
            off_cmd_builder = "echo 0 > /proc/power/relay" + str(self.my_relay_id) + " "
            
            # Sleep for the adjustment time
            if self.id == 1:
                print "Adj value " + str(adjustment_value)

            # TURN ON
            (stdin, stdout, stderr) = c.exec_command(on_cmd_builder)
            
            # WAIT (fixed amount of time)
            timeWait = (60.0 / float(self.bpm)) * 2
            time.sleep( timeWait )

            # TURN OFF
            (stdin, stdout, stderr) = c.exec_command(off_cmd_builder) 
            time.sleep( timeWait + adjustment_value )
            
            # SIGNAL TO NEIGHBORS THAT I FINISHED MY CYCLE
            self.send_message_to_neighbors()
            

    def run(self):
        """
        Start blinking
        """
        self.back_and_forth_forever()
