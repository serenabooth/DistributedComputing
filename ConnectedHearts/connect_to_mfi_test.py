import sys, os, string, threading
import paramiko

"""
    Code outline based on: StackOverflow Question 3485428
    "Creating multiple SSH connections at a time using Paramiko"
"""

outlock = threading.Lock() 

cmd = "echo 0 > /proc/power/relay1"

def workon(host):
    print "connected to " + host
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, username='ubnt', password='ubnt') 
    c.exec_command(cmd)

def main(): 
    hosts = ['192.168.1.20', '192.168.1.21']
    threads = []
    for h in hosts: 
        t = threading.Thread(target=workon, args=(h,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

main()


