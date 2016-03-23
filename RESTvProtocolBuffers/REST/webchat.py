#!/usr/bin/python

"""
http://www.acmesystems.it/python_httpd

Modified by: cs262, team 2 
"""

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import curdir, sep
import cgi
import MySQLdb
import time

global db

PORT_NUMBER = 8080

def query_result_to_list(results):
    """ Converts a MySQL query result to a list """
    return [result[0] for result in results]

def dictionary_from_messages_query(result):
    """
    Converts a row from the messages table, returned by a MySQL query,
    to a dictionary. The keys are the column names for the messages table.
    """
    if result:
        return {"id": result[0], "sender": result[1], "recipient": result[2],
                "content": result[3], "status": result[4], 
                "time_last_sent": result[5]}
    else:
        return None

def get_all_from_table(table_name, table_col_name): 
    """
    A MySQL query that looks up the value of table_col_name for each row in 
    table_name and returns a list containing the result.
    """
    with db: 
        cur = db.cursor() 
        cur.execute("SELECT " + table_col_name + " FROM " + table_name + 
                    " ORDER BY " + table_col_name)
        all_from_db = cur.fetchall()
        return query_result_to_list(all_from_db)

def check_if_exists(tbl_name, col_name, col_value):
    """
    A MySQL query that returns True if there exists an entry in tbl_name where 
    the value of the column col_name is col_value. Returns False otherwise.
    """
    with db: 
        cur = db.cursor()
        cur.execute("SELECT EXISTS( SELECT 1 FROM " + tbl_name + 
                     " WHERE " + col_name + " = '" + str(col_value) + "' )")
        answer = cur.fetchone()
        if (answer[0] == 1):
            return True 
        else:
            return False

def post_create_helper(table_name, table_values_dict):
    """
    Inserts a row into table_name using the keys and values in the dictionary
    table_values_dict. table_values_dict contains the values submitted by a 
    client POST request. The keys are the names of the columns in table_name and 
    values are the desired values. 
    """
    with db: 
        cur = db.cursor()
        cur.execute("INSERT INTO " + str(table_name) +  
                    " ("+ ", ".join(table_values_dict.keys()) + 
                    ") VALUES (" + ", ".join(table_values_dict.values()) + ")")

def password_correct(table_values_dict):
    """
    Returns True if the client entered the correct password when logging in and
    False otherwise. This is done with a MySQL query that looks up the password 
    in the db for the username entered by the client and compares it to the 
    password the user entered. table_values_dict contains the information 
    submitted by the client.
    """

    # Password is incorrect if password field was left blank
    if ("user_password" not in table_values_dict.keys()):
        print "Password field empty"
        return False

    with db: 
        cur = db.cursor()
        cur.execute("SELECT user_password "+ "FROM users " + 
                    "WHERE user_name = " + table_values_dict["user_name"])
        password = cur.fetchone()
        if str(password[0]) == table_values_dict["user_password"][1:-1]:
            print "User Authenticated!"
            return True
        else: 
            print "Nope"
            return False

def lookup_message_for_user(username): 
    """
    A MySQL query that looks up the oldest unsent message for the recipient 
    username and returns a dictionary with all the information
    for the corresponding row.
    The status of the message is updated to 1 to indicate that the server intends
    to send it to the client, but has not yet done so. The time_last_sent is also
    set to the current time stamp. 
    """
    with db: 
        cur = db.cursor()
        cur.execute("SELECT * FROM messages WHERE recipient = '" + 
                    str(username) + "' AND status = 0")
        message = dictionary_from_messages_query(cur.fetchone())
        if message: 
            cur.execute("UPDATE messages SET status = 1, time_last_sent = " + 
                        "CURRENT_TIMESTAMP WHERE id = " + str(message["id"]))
    return message

def evaluate_message_receipt(username):
    """
    Looks up any messages with a status of 1, which means they were marked by the
    server to be sent, but have not yet been received by the client. If any of 
    of these messages 
    """
    with db: 
        cur = db.cursor()
        cur.execute("SELECT * FROM messages " + "WHERE recipient = '" + 
                    str(username) + "' AND " + "status = 1")
        messages = cur.fetchall()
        messages = [dictionary_from_messages_query(message) for message in messages] 
        if messages: 
            for message in messages: 
                cur.execute("UPDATE messages SET status = 0 WHERE (id = " + 
                            str(message["id"]) + ") AND (TIMESTAMPDIFF(MINUTE, '" + 
                            str(message["time_last_sent"]) + 
                            "', CURRENT_TIMESTAMP) > 0)")


def mark_message_as_seen(msg_val):
    """
    Sets the status of the message with id msg_val to 2. This indicates that the
    message has been received by the client and does not need to be sent again.
    The time_last_sent is also updated to the current time stamp.
    """
    with db: 
        cur = db.cursor()
        cur.execute("UPDATE messages SET status = 2, " + 
                    "time_last_sent = CURRENT_TIMESTAMP WHERE id = " + msg_val)

def delete_acct(username):
    """ Delete the account username. """
    with db:
        cur = db.cursor()
        cur.execute("DELETE FROM users WHERE user_name = '" + str(username) + "'")

def lookup_group_users(group):
    """ Returns a list of all the users in group """
    with db: 
        cur = db.cursor() 
        cur.execute("SELECT user_name FROM groups WHERE group_name = '" + 
                    str(group) + "'")
        all_from_db = cur.fetchall()
        return query_result_to_list(all_from_db)

def lookup_by_regex(name, tbl_name, col_name):
    """
    Subset users or groups. 
    If user doesn't include the * operator, look up the exact input. 
    If user uses * operator, convert * to %, for SQL syntax. 
    Then query using the LIKE keyword. 
    Further details: http://dev.mysql.com/doc/refman/5.7/en/pattern-matching.html
    """
    with db: 
        all_from_db = None
        cur = db.cursor()
        if not "*" in name: 
            cur.execute("SELECT " + col_name + " FROM " + tbl_name + 
                        " WHERE " + col_name + " = '" + str(name) + "'")
            all_from_db = cur.fetchall()
        else: 
            name = name.replace("*", "%")
            cur.execute("SELECT DISTINCT " + col_name + " FROM " + tbl_name + 
                        " WHERE " + col_name + " LIKE '" + str(name) + "'")
            all_from_db = cur.fetchall()
    if (all_from_db):
        return query_result_to_list(all_from_db)
    else:
        return all_from_db

def lookup_last_ten_messages_for_user(username):
    """
    Looks up the ten messages most recently sent to username and returns a list
    of dictionaries (dictionary explained in dictionary_from_messages_query).
    """
    with db: 
        cur = db.cursor()
        cur.execute("SELECT * FROM messages WHERE recipient = '" + str(username) + 
                    "' AND status = 2 ORDER BY time_last_sent DESC limit 10")
        messages = cur.fetchall()
    if (messages):
        return [dictionary_from_messages_query(message) for message in messages] 
    else:
        return None

def concat_messages(msgs):
    """ Takes a list of message dictionaries to create an HTML string """
    msg_ret = ""
    for i in reversed(range(0, len(msgs))):
        msg_ret += "<div> " + msgs[i]["sender"] + ": " + msgs[i]["content"] + " </div>"
    return msg_ret

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
    def display_error_message(self, url_direction, error_msg):
        """ Displays the text error_msg on the the page url_direction """
        f = open(curdir + sep + url_direction) 
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(f.read())
        self.wfile.write(error_msg)
        f.close()

    #Handler for the GET requests
    def do_GET(self):
        print self.path

        # When the home page is loaded, looks up the last 10 messages and adds
        # them to the page
        if self.path.startswith("/getLastMessages"):
            self.path="/home_page.html"
            msg = lookup_last_ten_messages_for_user(self.headers['Cookie'])
            if msg: 
                self.send_response(200)
                self.send_header("messages_found", "0")
                self.end_headers() 
                self.wfile.write(concat_messages(msg))
                return
            else: 
                self.send_response(200)
                self.send_header("messages_found", "1")
                self.end_headers() 
                return

        # When the client requests messages, the server sends back the message 
        # content along with the unique message id
        if self.path.startswith("/getmsg"):
            self.path="/home_page.html"
            # fetch user's messages from DB
            try: 
                msg = lookup_message_for_user(self.headers['Cookie'])
                evaluate_message_receipt(self.headers['Cookie'])
                if msg: 
                    print "YESSS" + self.headers['Cookie']
                    self.send_response(200)
                    self.send_header("message_id", str(msg["id"]))
                    self.end_headers() 
                    self.wfile.write(str(msg["sender"]) + ": " + str(msg["content"]))
                # if there are no new messages, the servers sends the message id -1 
                else: 
                    self.send_response(200)
                    self.send_header("message_id", str(-1))
                    self.end_headers() 
                return 
            except: 
                self.send_response(200)
                self.send_header("message_id", str(-1))
                self.end_headers() 

        # Once the server receives confirmation that the message was received by
        # the client, it marks the message as successfully sent using the unique
        # message id passed by the client in the url
        if self.path.startswith("/receivedmsg"):
            msg_val = self.path[len("/receivedmsg"):]
            mark_message_as_seen(msg_val)
            self.path="/home_page.html"
            # mark as seen in DB
            print "GOT IT!" + self.headers['Cookie']
            self.send_response(200)
            return 

        if self.path.endswith("?"):
            self.path=self.path[1:-1]

        if (self.path.startswith("/delete_acct")):
            print "TRYING TO DELETE ACCOUNT"
            delete_acct(self.path[len("/delete_acct"):])
            self.path="/delete_useraccount.html"

        if self.path.startswith("/group_lookup"):
            group_name_regex = self.path[len("/group_lookup?group_name="):]
            self.path = "/see_groups.html"
            groups = lookup_by_regex(group_name_regex, "groups", "group_name")
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            f = open(curdir + sep + self.path) 
            self.wfile.write(f.read())
            if (groups):
                self.wfile.write(groups)
            else: 
                self.wfile.write("couldn't find such a group")
            f.close()
            return

        if self.path.startswith("/user_lookup"):
            user_regex = self.path[len("/user_lookup?user_name="):]
            self.path = "/see_users.html"
            users = lookup_by_regex(user_regex, "users", "user_name")
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            f = open(curdir + sep + self.path) 
            self.wfile.write(f.read())
            if (users):
                self.wfile.write(users)
            else: 
                self.wfile.write("couldn't find such a user")
            f.close()
            return

        if self.path=="/":
            self.path="/home.html"

        try:
            #Check the file extension required and
            #set the right mime type
                #Open the static file requested and send it
            f = open(curdir + sep + self.path) 
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f.read())
            if self.path == "see_groups.html":
                groups_with_dups = get_all_from_table("groups", "group_name")
                self.wfile.write(sorted(list(set(groups_with_dups))))
            elif self.path == "see_users.html":
                self.wfile.write(get_all_from_table("users", "user_name"))
            f.close() 
            return

        except IOError:
            print "error"
            self.send_error(404,'File Not Found: %s' % self.path)

    #Handler for the POST requests
    def do_POST(self): 
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
        })

        print self.path[1:]

        # dictionary with keys that are the name elements in an html form 
        # submitted by the client and the values correspond to the correct name
        form_values_dict = {}
        for key in form.keys():
            # check for apostrophes in client input to prevent problems with 
            # SQL queries 
            if ("'" in str(form.getvalue(key))):
                # if the input is for a message escape every apostrophe with an 
                # apostrophe since apostrophes are allowed in message input
                if (self.path[1:] == "messages"):
                    sanitized_msg = str(form.getvalue(key)).replace("'", "''")
                    form_values_dict[key] = "'" + sanitized_msg + "'"
                # otherwise, keep track of the fact that there was an apostrophe
                # to print an error message to client later
                else:
                    form_values_dict[key] = None
            else:
                form_values_dict[key] = "'" + str(form.getvalue(key)) + "'"

        if (self.path[1:] == "login"):
            if ("user_name" not in form_values_dict.keys() or 
                "user_password" not in form_values_dict.keys()):
                self.display_error_message("log_in.html", 
                                            "You left a field blank.")
                return
            # no usernames or passwords include apostrophes
            if (None in form_values_dict.values()):
                self.display_error_message("log_in.html", 
                                            "Incorrect username and password")
                return
            if (check_if_exists("users", "user_name", form["user_name"].value)):
                if (not password_correct(form_values_dict)):
                    self.display_error_message("log_in.html", 
                                                "Incorrect password")
                    return
            else:
                self.display_error_message("log_in.html", 
                                            "Username does not exist")
                return

        elif (self.path[1:] == "users"):
            if (None in form_values_dict.values()):
                self.display_error_message("create_acct.html", 
                                            "Fields cannot contain apostrophe.")
                return
            if ("user_name" not in form_values_dict.keys()):
                self.display_error_message("create_acct.html", 
                                            "Username field was empty.")
                return
            if (len(form["user_name"].value) >= 80):
                self.display_error_message("create_acct.html", 
                                            "Username too long")
                return
            if ("user_password" not in form_values_dict.keys()):
                self.display_error_message("create_acct.html", 
                                            "Password field was empty.")
                return
            # enfornce unique group names and user names
            if (check_if_exists("users", "user_name", form["user_name"].value) or 
                check_if_exists("groups", "group_name", form["user_name"].value)):
                self.display_error_message("create_acct.html", 
                                            "Username already in use.")
                return
            post_create_helper(self.path[1:], form_values_dict)

        elif (self.path[1:] == "messages"):
            # content or recipient left blank, or content too long
            if ("content" not in form_values_dict.keys() or 
                "recipient" not in form_values_dict.keys() or 
                len(form_values_dict["content"]) >= 120):
                self.send_response(204)
                return  
            # add the sender to the dictionary
            form_values_dict["sender"] = "'" + self.headers['Cookie'] + "'"
            form_values_dict["content"] = ("'(to " + 
                                            form_values_dict["recipient"][1:-1] + 
                                            ") " + 
                                            form_values_dict["content"][1:-1] + "'")
            # if the recipient is a group, send to everyone in the group
            if (check_if_exists("groups", "group_name", form_values_dict["recipient"][1:-1])):
                group_users = lookup_group_users(form_values_dict["recipient"][1:-1])
                for user in group_users:
                    form_values_dict["recipient"] = "'" + str(user) + "'"
                    post_create_helper(self.path[1:], form_values_dict)
                # send message to self, too, if not in the group, for coherent chat log
                if (self.headers['Cookie'] not in group_users):
                    form_values_dict["recipient"] = "'" + self.headers['Cookie'] + "'"
                    post_create_helper(self.path[1:], form_values_dict)
            elif (check_if_exists("users", "user_name", form_values_dict["recipient"][1:-1])):
                post_create_helper(self.path[1:], form_values_dict)
                # send message to self, too, for coherent chat log
                form_values_dict["recipient"] = "'" + self.headers['Cookie'] + "'"
                post_create_helper(self.path[1:], form_values_dict)
            # send 204 response to prevent page reload    
            self.send_response(204)
            return

        elif (self.path[1:] == "groups"):
            if (None in form_values_dict.values()):
                self.display_error_message("create_group.html", 
                                            "Groupname cannot contain apostrophe.")
                return
            if ("group_name" not in form_values_dict.keys()):
                self.display_error_message("create_group.html", 
                                            "Groupname field blank")
                return
            if (len(form["group_name"].value) >= 80):
                self.display_error_message("create_group.html", 
                                            "Groupname too long")
                return
            if (not check_if_exists("groups", "group_name", form["group_name"].value) and 
                not check_if_exists("users", "user_name", form["group_name"].value)):
                form_values_dict["user_name"] = "'" + str(self.headers['Cookie']) + "'"
                post_create_helper(self.path[1:], form_values_dict)
            else:
                self.display_error_message("create_group.html", 
                                            "Group name already in use.")
                return

        elif (self.path[1:] == "join_group"):
            if (None in form_values_dict.values() or 
                "group_name" not in form_values_dict.keys() or 
                not check_if_exists("groups", "group_name", form["group_name"].value)):
                self.display_error_message("join_group.html", 
                                            "Group does not exist.")
                return
            else:
                form_values_dict["user_name"] = "'" + str(self.headers['Cookie']) + "'"
                post_create_helper("groups", form_values_dict)

        else:
            post_create_helper(self.path[1:], form_values_dict)

        self.send_response(301)
        self.send_header('Location',curdir + sep + "home_page.html")
        self.end_headers()

        return                  
            
try:
    db= MySQLdb.connect("mysql.slbooth.com", "262_team_2", "michelleserena", "cs262")

    #Create a web server and define the handler to manage the
    #incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print 'Started httpserver on port ' , PORT_NUMBER
    
    #Wait forever for incoming htto requests
    server.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()
    