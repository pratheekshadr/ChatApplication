import socket
import threading
import os
import sys, time
import logging

msg_count = 0

def create_socket():
    try:
        s = socket.socket()
    except socket.error, e:
        logging.error("Error creating socket %s", e)
        os._exit(0)
    return s

def connect_to_server(s, host, port):
    try:
        s.connect((host, port))
    except socket.gaierror, e:
        logging.error("Error connecting to server %s", e)
        os._exit(0)
    except socket.error, e:
        logging.error("Connection error %s", e)
        os._exit(0)


#send data from client who has socket_obj value connection
def send_data(num_retries, data, connection):
    for i in range(num_retries + 1):
        try:
            connection.send(data)
            return True
        except socket.error, e:
            print("Retrying to send the msg!")
            logging.error("Error sending data %s", e)
    return False

#to send group chat messages to server
def send_message(s):
    while True:
        msg = raw_input()
        sys.stdout.write("\033[F")

        status = send_data(3, msg, s) 
        #send_data failed    
        if not(status):
            print("resending failed...Try sending the msg again!")
            continue

        #to leave room
        if msg == 'lr':
            break


#retrun the data received from client who has socket_obj equal to connection
def receive_data(connection):
    try:
        data = connection.recv(1024)
    except socket.error, e:
        logging.error("Error receiving data %s", e)
        os._exit(0)
    return data


#to receive group chat messages
def receive_message(s):
    while True:
        data = receive_data(s)

        #when leave room is pressed
        if len(data)>2 and data[0] == 'l' and data[1]=='r':
            print("You left")
            rooms_available = data.split("room", 1)[1]
            if len(rooms_available) < 1:
                rooms_available = receive_data(s)
            print(rooms_available)     
            break
        #when other msgs are sent
        elif data:
            print(data)
    
def join_room(s):
    available_rooms = receive_data(s)
    print(available_rooms)

    while True:
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
        selected_room_no = raw_input("Enter valid room no(q to exit):")

        #to exit group chat
        if selected_room_no == 'q':
            status = send_data(3, 'Exit', s)
            if not(status):
                print("resending failed...Try sending the msg again!")
                continue

            data = receive_data(s)
            print(data)
            s.close()
            os._exit(0)
        #to join a new room
        else:
            status = send_data(3, selected_room_no, s)
            if not(status):
                print("resending failed...Try sending the msg again!")
                continue

            joined_users_info = receive_data(s)

            #if selected room isn't valid
            if joined_users_info.split(':')[0] == 'Error':
                sys.stdout.write("\033[F")
                print(joined_users_info.split(':')[1])
            else:       
                print(joined_users_info)
                try:
                    thread1 = threading.Thread(target = send_message, args=([s]))                          
                    thread2 = threading.Thread(target = receive_message, args=([s]))                   
                
                    thread1.start()
                    thread2.start()
                except:
                    logging.error("Error starting threads")
                    os._exit(0)

                while thread1.isAlive() or thread2.isAlive():
                    continue

def get_user_name(s):
    #Del:receives "Enter valid username"
    data = receive_data(s)
    print(data)

    while True:
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
        user_name = raw_input()

        if len(user_name)!=0:
            status = send_data(3, user_name, s)            
            if not(status):
                print("resending failed...Try sending the msg again!")
            else:
                server_data = receive_data(s)

                if server_data.split(':')[0] == 'Error':
                    sys.stdout.write("\033[F")
                    print(server_data.split(':')[1])
                else:     
                    logging.info("Username " + user_name + " assigned in the server")  
                    #Del: gets "enter lr to leave q to exit"
                    data = receive_data(s)
                    print(data)
                    return

def main():
    logging.basicConfig(level=logging.DEBUG, filename="clientlog", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    
    s = create_socket()
    port = 8080
    host = '192.168.100.4'
    connect_to_server(s, host, port)
    #asks user to give valid user name
    get_user_name(s)
   
    try:
        thread = threading.Thread(target = join_room, args=([s]))               
        thread.start()
    except:
        logging.error("Error starting thread")
        os._exit(0)

main()