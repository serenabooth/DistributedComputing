import socket
import os
import random
from clock import *

clock_1 = Clock(1, random.randint(1, 6), "logbook_clock_1.txt", 8000)
clock_2 = Clock(2, random.randint(1, 6), "logbook_clock_2.txt", 8080)
clock_3 = Clock(3, random.randint(1, 6), "logbook_clock_3.txt", 8888)

clock_1.start()
clock_2.start()
clock_3.start() 

#clock_1.send_event(clock_2)


