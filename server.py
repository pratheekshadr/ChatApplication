from socket import * 
import socket
import threading	
import time
import logging 
import sys
import os

class Client:
    def __init__(self, user_name, connection, room_no):
        self.user_name = user_name
        self.connection = connection
        self.room_no = room_no

def create_socket():
    try:
        s = socket.socket()
    except socket.error, e:
        logging.error("Error creating socket %s", e)
        sys.exit(1)
    return s

def bind_socket_port(s, port):
    try:
        s.bind(('', port))
    except socket.error, e:
        logging.error("Error binding socket to the port %s", e)
        sys.exit(1)

#send data from client who has socket_obj value connection
def send_data(data, connection):
    try:
        connection.send(data)
    except socket.error, e:
        logging.error("Error sending data %s", e)
        sys.exit(1)

#retrun the data received from client who has socket_obj equal to connection
def receive_data(connection):
    try:
        data = connection.recv(1024)
        return data
    except socket.error, e:
        logging.error("Error receiving data %s", e)
        sys.exit(1)

#creates client object with given parameters
def create_client(new_user_name, new_user_conn, new_user_room_no):
    logging.info("Client object created")
    new_client = Client(new_user_name, new_user_conn, new_user_room_no)
    logging.info(new_user_name + " joined")
    return new_client

#broadcast data2 to all the users except sender and send data1 to sender
def broadcast_data(data1, data2, sender, clients):
    for client in clients:
        if client.connection == sender.connection:
            if data1 != None:
                send_data(data1, sender.connection)
        elif client.room_no == sender.room_no and client.room_no != 0:
            if data2 != None:
                send_data(data2, client.connection)

#to broadcast group chat messages    
def new_message_notification(data, sender, clients):
    #when leave room(lr) is pressed
    if data == 'lr':
        leave_msg = sender.user_name + " left"
        broadcast_data(None, leave_msg, sender, clients)

        logging.info(sender.user_name + " left room : " + sender.room_no)
        sender.room_no = 0
        send_data("lr:leave room", sender.connection)
        room_no = select_room(sender, clients)
        join_new_room(room_no, sender, clients)  
        return 
    #to broadcast normal msg
    else:
        msg1 = "Me[" + sender.room_no + "]:" + data + "\n"
        msg2 = sender.user_name+ "[" + sender.room_no + "]: " + data + "\n"
        broadcast_data(msg1, msg2, sender, clients)                

#thread to receive group chat messages from every user
def get_client_msg(new_client, clients):
    try:
        while True:
            data = receive_data(new_client.connection)
            new_message_notification(data, new_client, clients)
    except:
        logging.info(new_client.user_name + " exited ")

#sending room info to the user who has joined room_no
def join_new_room(room_no, new_client, clients):
    new_client.room_no = room_no
    try:
        joined_users = ' '.join([str(client.user_name) for client in clients if client.room_no == room_no and client.connection != new_client.connection and client.room_no != 0 ])
    except:
        logging.error("Error in collecting room info")
    
    room_info_msg = "Users already in room: " + joined_users + "\n"
    send_data(room_info_msg, new_client.connection)

    logging.info(new_client.user_name + " joined room : " + new_client.room_no)
    
    join_msg1 = "Welcome to " + new_client.room_no + "\n"
    join_msg2 = new_client.user_name + " has joined\n"
    broadcast_data(join_msg1, join_msg2, new_client, clients)

#displays and gets valid room_no from the user
def select_room(new_client, clients):
    send_data("Select roomNo:\n 101\n 102\n 103\n", new_client.connection)
    while True:
        room_no = receive_data(new_client.connection)
        #when q is pressed
        if room_no == 'Exit':
            exit_msg1 = "You exited\n"
            exit_msg2 = new_client.user_name + " exited\n"
            broadcast_data(exit_msg1, exit_msg2, new_client, clients)
        
            index = clients.index(new_client)
            clients.remove(clients[index])

        #to check if selected room is valid or not
        elif room_no not in ['101', '102', '103']:
            send_data('Error:Invalid room number', new_client.connection)

        #to send room info after joining
        else:
            return room_no

#accepts connection from client and returns client obj with valid username and default room number i.e, 0
def accept_new_connection(s, clients):
    new_user_conn, addr = s.accept()

    send_data("Enter valid username\n", new_user_conn)
    while True:
        new_user_name = receive_data(new_user_conn)

        #check if user name is empty or newline
        if len(new_user_name) == 0 or new_user_name == '\n':
            new_user_conn.send('Error:Invalid username')
        #check if username is already taken
        elif len([client.user_name for client in clients if client.user_name == new_user_name]):
            new_user_conn.send('Error:Username already present')
        else:
            new_user_conn.send('Success:Username assigned')
            break
    
    new_client = create_client(new_user_name, new_user_conn, 0)
    send_data("\nEnter lr to leave room\nEnter q to exit\n", new_client.connection)

    try:
        #add new user to exisitng users list
        clients.append(new_client)
    except:
        logging.error("Error adding new client to the list")
        sys.exit(1)
    logging.info("added new client")

    return new_client

def main():
    logging.basicConfig(level=logging.DEBUG, filename="serverlog", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
   
    clients = []
    s = create_socket()
    port = 8080
    bind_socket_port(s, port)
    s.listen(5)	

    while True:
        new_client = accept_new_connection(s, clients)
        new_user_room_no = select_room(new_client, clients)
        join_new_room(new_user_room_no, new_client, clients)

        try:
            #background thread to receive data from new user and broadcast it
            thread = threading.Thread(target = get_client_msg, args=([new_client, clients]))                  
            thread.start()  
        except:
            logging.error("Error starting the thread")
            sys.exit(1)
        logging.info("New thread started for user : "+ new_client.user_name)

    s.close()
    logging.info("Socket connection closed")

main()                