# our libraries
from BulbBlinker import * 

# external libraries
from datetime import datetime
import sys, os
import string, time, random
from multiprocessing import Array, Process, Value
from multiprocessing.queues import Queue
from ctypes import c_char_p

"""
    Code outline based on: StackOverflow Question 3485428
    "Creating multiple SSH connections at a time using Paramiko"
"""

def bulb_id_distance( bulb1, bulb2 ):
    bulbDiff = abs( int(bulb1) - int(bulb2) ) % 13
    return ((13 - bulbDiff) if (bulbDiff > 6) else bulbDiff)

class BulbControl(Process):
    def __init__(self, my_id, bpm, host, adjustment, leader_id, state_q, bulb_objects_list, turned_on_list):
        """
        Initialize BulbControl process, set environment variables.
        
        :param my_id: id ranging from 0-12, specifying bulb position
        :type my_id: int 
        :param bpm: pulse rate in beats per minute
        :type bpm: int
        :param host: ip address of Ubiquiti strip with relevant relay
        :type host: string (e.x. "192.168.1.20")
        :param leader_id: id of leader bulb, ranging from 0-12
        :type leader_id: int
        :param state_q: Queue of bulb states corresponding to on/off messages
        :type state_q: BulbQueue (see BulbQueue.py)
        :param turned_on_list: List of bulbs turned on (process-safe) 
        :type turned_on_list: Process safe list of c_type ints 
        """
        super(BulbControl, self).__init__()
        self.id = my_id
        self.bpm = bpm
        self.host = host
        self.leader_id = leader_id
        self.state_q = state_q
        self.bulb_objects_list = bulb_objects_list
        self.turned_on_list = turned_on_list

        self.adjustment = adjustment

        self.time_of_last_blink = None
        self.time_of_neighbor_below = None
        self.time_of_neighbor_above = None

        self.above_bulb_id = (self.id + 1) % 13
        self.below_bulb_id = (self.id - 1) % 13

    def check_ordering(self):
        """
        Receive messages from self and neighbors. Decide which neighbor to trust. 
        Calculate necessary adjustment to time of bulb blinking. 
        Send adjustment message to child process, BulbBlinker
        
        :return: None
        """
        while True:
            if self.id == 1:
                print self.id
            
            if self.id == self.leader_id.value:
                # I am the leader.
                # Go to sleep for a bit; don't adjust synchronization.
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
                tPrev = datetime.now()
                relevant_neighbor_time = tPrev
                
                while True:
                    
                    # This is the point at which this process first pauses
                    # It waits for all bulbs to have started blinking at least once
                    # Then, self.state_q begins to be filled...
                    
                    if not self.state_q.empty():
                        # Get bulb uuid of either my self or my neighbors
                        message = self.state_q.get()
                        time_received_message = datetime.now()

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
                            
                tBreak = datetime.now()

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
                    waitTime = 0.25 # 2*halfTimePhase - diff.total_seconds() # 0.25
                elif diff.total_seconds() > 0.125 and diff.total_seconds() < halfTimePhase:
                    waitTime = -0.25 # -diff.total_seconds # -0.25
                else:
                    waitTime = 0
                
                # Slow down the adjustment to 'ease' the system into a stable state.
                adjustmentFactor = 1.0
                self.adjustment.put( waitTime * adjustmentFactor )
                
                if self.id == 1:
                    print ("I, " + str(self.id) + " had times: self: " + 
                           str(self.time_of_last_blink) + " / " + str(relevant_neighbor_time) + 
                           "  Adjustment: " + str(waitTime * adjustmentFactor) + 
                           " at " + str(datetime.now()))
                
                time.sleep(0.00001)
                
                sys.stdout.flush();
      

    def run(self):  
        """
        Create a child process to turn bulb on and off
        Start self continually checking ordering of bulbs 
        """
        self.check_ordering()
