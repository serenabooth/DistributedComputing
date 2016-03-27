This application uses Python 2.7 and JavaScript. To run this code, you will need a MySQL database set up; details below. You may also need to install MySQLdb. The two other Python modules we use, BaseHTTPServer and CGI, should be installed with any standard distribution.

~~~~~~~ DEPENDENCIES ~~~~~~~ 

MySQLdb:
	used for CRUD of user data

BaseHTTPServer: 
	extends SocketServer. Used as server for HTTP/RESTful communication.

CGI:
	used to process input via forms submitted by users from HTML pages

The client’s environment must have access to HTTP passed over port 8080 and must be able to run JavaScript. The server must likewise be able to access HTTP passed over port 8080, via an HTTPServer library. The server must also run Python.

~~~~~~~ INSTALLATION ~~~~~~~

MySQLdb: 
	pip install MySQL-python

~~ Running the application: ~~ 

python webchat.py
navigate to: 0.0.0.0:8080

~~~~~~~ Code layout ~~~~~~~~

The majority of the code is located in webchat.py. 
Webchat.py launches a BaseHTTPServer, and extends BaseHTTPRequestHandler 
to handle POST (using method do_POST) and GET (using method do_GET) requests.

Data is stored in a MySQL database. The details of this database are outlined below.  

On launching the server, a client/user is directed to home.html. From here, users can 
navigate between different HTML pages with the following functionalities: 
	
	- home.html: sign up for or log in to service
	- log_in.html: log in to service
	- create_acct.html: sign up for service
	- home_page.html: main page for service. Functionalities: 
			- see messages sent to you
			- create a group
			- join a group
			- see groups
			- see users
			- delete account
	- create_group.html: create a group
	- join_group.html: join a group
	- see_groups.html: see all or a subset of groups
	- see_users.html: see all or a subset of all users
	- delete_useraccount.html: delete your account


~~~~~~~~~~ MySQL: ~~~~~~~~~~ 

We provide an example SQL database in /SQL_dump/cs262.sql. Please import this database, and set your credentials in following line in webchat.py: db = MySQLdb.connect(...). 

----------------------------

table name: messages
table columns: 
          id (bigint, primary key, unique) 
		  sender (varchar, 80char max length) 
		  recipient (varchar, 80char max length)
		  content (varchar, 160char max length) 
		  status (smallint) 
		  time_last_sent (datetime) 

-----------------------------

table name: groups
table columns: 
		  group_id (bigint, primary key, unique) 
		  group_name (varchar, 80char max length) 
		  user_name (varchar, 80char max length) 

-----------------------------

table name: users 
table columns: 
          user_id (bigint, primary key, unique) 
		  user_name (varchar, 80char max length, unique) 
		  user_password (varchar, 80char max length) 

-----------------------------


