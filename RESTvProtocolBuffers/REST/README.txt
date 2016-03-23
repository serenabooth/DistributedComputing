This application uses Python 2.7 and JavaScript. To run this code, you will need a MySQL database set up; details below. You may also need to install BaseHTTPServer, MySQLdb, and CGI. 

~~ Running the application: ~~ 

python webchat.py

~~~~~~~ Code layout ~~~~~~~~

The majority of the code is located in webchat.py

~~~~~~~~~~ MySQL: ~~~~~~~~~~ 

database name: messages
database columns: 
          id (bigint, primary key, unique) 
		  sender (varchar, 80char max length) 
		  recipient (varchar, 80char max length)
		  content (varchar, 160char max length) 
		  status (smallint) 
		  time_last_sent (datetime) 

-----------------------------

database name: groups

database columns: 
		  group_id (bigint, primary key, unique) 
		  group_name (varchar, 80char max length) 
		  user_name (varchar, 80char max length) 

-----------------------------

database name: users 

database columns: 
          user_id (bigint, primary key, unique) 
		  user_name (varchar, 80char max length, unique) 
		  user_password (varchar, 80char max length) 

-----------------------------


