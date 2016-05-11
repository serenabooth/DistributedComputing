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

        :param my_id: id ranging from 0-12, specifying bulb position
        :type my_id: int 
        :param bpm: pulse rate in beats per minute
        :type bpm: int
        :param host: ip address of Ubiquiti strip with relevant relay
        :type host: string (e.x. "192.168.1.20")
        :param adjustment: queue to receive adjustment instructions
        :type adjustment: multiprocessing Queue
        :param above_neighbor: id of above neighbor
        :type above_neighbor: int
        :param below_neighbor: id of below neighbor
        :type below_neighbor: int
        :param turned_on_list: List of bulbs turned on (process-safe) 
        :type turned_on_list: Process safe list of c_type ints  
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
                
        self.my_relay_id = int(self.id * 1.0 / 2) + 1
        
    def send_message_to_neighbors(self):
        """
        Check all bulbs are on (using turned_on_list) 
        Put self.id on state_q's of self as well as of neighboring bulbs 

        :return: None
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

        :return: None
        """
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(self.host, username='ubnt', password='ubnt') 
        
        while True:
            if os.getppid() == 1: 
                os.kill(os.getpid(), 9)
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
