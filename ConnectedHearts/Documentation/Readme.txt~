This application uses Python 2.7, OpenCV 3.0, Paramiko, and PiCamera. 

~~~~~~~~~~~~ HARDWARE DEPENDENCIES ~~~~~~~~~~~~ 

- Raspberry Pi
- Raspberry PiCamera
- 2x Ubiquiti 8-outlet mPower powerstrips, one of which with static IP address 192.168.1.20, another with 192.168.1.21. 

~~~~~~~~~~~~ SOFTWARE DEPENDENCIES ~~~~~~~~~~~~ 

Python 2.7 
----------
    - All code written in python
    - Installation instructions: https://wiki.python.org/moin/

OpenCV 3.0
----------
    - Used for image analysis, to detect faces in the camera view and to measure the 
    - On a Linux distro, OpenCV (for Python) can be installed by running: 
          sudo pip install python-opencv
    
Paramiko
--------
    - Used for in-code SSH connections
    - On a UNIX distro: 
          sudo pip install paramiko

PiCamera (software)
--------
    - NOTE: MUST BE USED WITH A PHYSICAL PiCamera, A RASPBERRY PI CAMERA MODULE
    - Used as a webcam to view frames of the world
    - Install on a Linux Distro: sudo apt-get install python-picamera


~~~~~~~~~~~~ CODE LAYOUT ~~~~~~~~~~~~ 

To run our program, run: python main.py. This code will only run successfully on a Raspberry Pi, with the above dependencies installed. 

Main.py creates an object, App, found in /webcam_pulse/get_pulse.py. This object is used to detect a pulse of a face in the scene. 
Main.py also creates a CheckFace object, found in /webcam_pulse/lib/check_face_visible.py. 

Main.py first launches two "Pi" processes, from control_pi.py. These processes establish SSH connections and shut off relays 1-7 on both Ubiquiti powerstrips. 

Main.py then creates 13 "Bulb" processes, from hearts.py. These processes run leader election. Once a leader is selected, the leader spawns a child process, "BulbControl" from control_bulb.py, which further spawns a process "BulbBlinker" in control_bulb.py. The leader then communicates with its neighboring (in the physical world) Bulb processes, and these bulbs follow this same process of spawning child processes. 

BulbControl is used to determine how much the bulb should adjust its pulsating; BulbBlinker keeps the bulb pulsating continually. These two processes communicate via two queues. 






