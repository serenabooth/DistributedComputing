import socket
import os
import random
from clock import *

clock_1 = Clock(1, 3, "logbook_clock_1.txt", 8000, 5000)
clock_2 = Clock(2, 3, "logbook_clock_2.txt", 8080, 5080)
clock_3 = Clock(3, 3, "logbook_clock_3.txt", 8888, 5888)

clock_1.start()
clock_2.start()
clock_3.start() 

