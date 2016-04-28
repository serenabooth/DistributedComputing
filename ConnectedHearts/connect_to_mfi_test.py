import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.20', username='ubnt', password='ubnt') 
c.exec_command("echo 1 > /proc/power/relay1")
print "connected?"
