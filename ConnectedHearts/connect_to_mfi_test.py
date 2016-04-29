import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.20', username='ubnt', password='ubnt') 
<<<<<<< HEAD
c.exec_command("echo 1 > /proc/power/relay1 && echo 1 > /proc/power/relay2")
=======
c.exec_command("echo 1 > /proc/power/relay1  && echo 1 > /proc/power/relay2")
>>>>>>> 6b78baa3256d57abf2265c7e09cbdfcd843f25cd
print "connected?"
