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

def bulb_id_distance( bulb1, bulb2 ):
    bulbDiff = abs( int(bulb1) - int(bulb2) ) % 13
    return ((13 - bulbDiff) if (bulbDiff > 6) else bulbDiff)

class BulbControl(Process):
    def __init__(self, my_id, bpm, host, leader_id, state_q, bulb_objects_list, turned_on_list):
        super(BulbControl, self).__init__()
        self.id = my_id
        self.bpm = bpm
        self.host = host
        self.leader_id = leader_id
        self.state_q = state_q
        self.bulb_objects_list = bulb_objects_list
        self.turned_on_list = turned_on_list

        self.adjustment = Queue()

        self.time_of_last_blink = None
        self.time_of_neighbor_below = None
        self.time_of_neighbor_above = None

        self.above_bulb_id = (self.id + 1) % 13
        self.below_bulb_id = (self.id - 1) % 13

    def check_ordering(self):

        while True:
            if self.id == 1:
                print self.id
            
            if self.id == self.leader_id.value:
                # I am the leader.
                # Go to sleep for a bit.
                time.sleep(5)
            else:
                # I am not the leader.
                # I want to find the time difference between myself 
                # and the leader, through my neighbors.
                #
                # Find which neighbor of mine is closer to the leader.
                steps_to_above = bulb_id_distance( self.leader_id.value, self.above_bulb_id )
                steps_to_below = bulb_id_distance( self.leader_id.value, self.below_bulb_id )

                # if my +1 neighbor is closer, set neighbor = 1; otherwise, -1
                neighbor = 1 if steps_to_above < steps_to_below else -1
                
                # Loop until I have a message from my leading neighbor and a message from myself
                tPrev = datetime.datetime.now()
                relevant_neighbor_time = tPrev
                
                while True:
                    
                    # This is the point at which this process first pauses
                    # It waits for all bulbs to have started blinking at least once
                    # Then, self.state_q begins to be filled...
                    
                    if not self.state_q.empty():
                        # Get bulb uuid of either my self or my neighbors
                        message = self.state_q.get()
                        time_received_message = datetime.datetime.now()

                        # If I 'sent' the message
                        if message == str(self.id):
                            self.time_of_last_blink = time_received_message
                            if self.id == 1:
                                print "Received self message " + str(time_received_message)
                            if relevant_neighbor_time != tPrev:
                                break
                                
                        # If my trusted neighbor sent the message
                        elif message == str((self.id + neighbor) % 13):
                            relevant_neighbor_time = time_received_message
                            if self.id == 1:
                                print "Received trusted neighbor message " + str(time_received_message)
                            
                tBreak = datetime.datetime.now()

                if self.id == 1:
                    print "I, " + str(self.id) + " broke out after " + str((tBreak-tPrev).total_seconds())
                
                # I now have:
                # - The last time that I received a message from my trusted neighbor that it pulsed.
                # - The last time that I pulsed
                

                # Compare last received message from neighbor to neighbor's expected future tick
                # Set my time difference based on which one I'm closer to
                halfTimePhase = (60.0 / float(self.bpm)) * 2
                diff = self.time_of_last_blink - relevant_neighbor_time
                
                if self.id == 1:
                    print "diff.total_seconds " + str( diff.total_seconds() )
                assert( diff.total_seconds() >= 0 )
                waitTime = 0;
                
                if diff.total_seconds() < halfTimePhase:
                    # Previous pulse start is closer
                    # Wait the extra part to bring me into phase
                    waitTime = (2 * halfTimePhase) - diff.total_seconds()
                    
                else:
                    # Future pulse start is closer
                    # Wait the difference to bring me into phase
                    waitTime = diff.total_seconds()
                
                if diff.total_seconds() > halfTimePhase and diff.total_seconds() < (2*halfTimePhase - 0.125):
                    waitTime = 0.25
                elif diff.total_seconds() > 0.125 and diff.total_seconds() < halfTimePhase:
                    waitTime = -0.25
                else:
                    waitTime = 0
                
                # Slow down the adjustment to 'ease' the system into a stable state.
                adjustmentFactor = 1.0
                self.adjustment.put( waitTime * adjustmentFactor )
                
                if self.id == 1:
                    print "I, " + str(self.id) + " had times: self: " + str(self.time_of_last_blink) + " / " + str(relevant_neighbor_time) + "  Adjustment: " + str(waitTime * adjustmentFactor) + " at " + str(datetime.datetime.now()) 
                
                time.sleep(0.00001)
                
                sys.stdout.flush();
      

    def run(self):
        #sys.stdout = open(str(os.getpid()) + ".out", "w")
        
        my_bulb = BulbBlinker(  my_id = self.id,
                                bpm = self.bpm, 
                                host = self.host,
                                adjustment = self.adjustment,
                                bulb_objects_list = self.bulb_objects_list, 
                                above_neighbor = self.above_bulb_id, 
                                below_neighbor = self.below_bulb_id, 
                                turned_on_list = self.turned_on_list)
        
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
                    below_neighbor, 
                    turned_on_list):
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

        #
        if self.on == 1: 
            self.bulb_objects_list[self.id].state_q.put(str(self.id))
            self.bulb_objects_list[self.above_neighbor].state_q.put(str(self.id))
            self.bulb_objects_list[self.below_neighbor].state_q.put(str(self.id))
            
            if self.id == 1:
                print "============================================================================\nAdded messages to self and neighbor state_qs " + str(datetime.datetime.now())

    def back_and_forth_forever(self):
        
        #print "connecting to " + self.host
        #paramiko.util.log_to_file( "bulb" + str(self.id) + ".log" )
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(self.host, username='ubnt', password='ubnt') 
        #print c
        
        while True: 
            
            #tStart = datetime.datetime.now()
            
            adjustment_value = 0
            while not self.adjustment.empty():
                adjustment_value = self.adjustment.get()
        
            on_cmd_builder = "echo 1 > /proc/power/relay" + str(self.my_relay_id) + " "
            off_cmd_builder = "echo 0 > /proc/power/relay" + str(self.my_relay_id) + " "
            
            # Sleep for the adjustment time
            if self.id == 1:
                print "Adj value " + str(adjustment_value)
            #time.sleep( adjustment_value )

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
            
            #tEnd = datetime.datetime.now()
            #print "Time between messages: " + str((tEnd-tStart).total_seconds())
            
            #sys.stdout.flush();

    def run(self):
        #sys.stdout = open(str(os.getpid()) + ".out", "w")
        self.back_and_forth_forever()
