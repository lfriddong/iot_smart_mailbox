#!/usr/bin/env python3
import socket
import threading
from typing import Tuple

# Global variables
app_address: Tuple[str, int] = ('192.168.1.1', 8080)  # app address, NEED TO BE MODIFIED!
huzzah_address: Tuple[str, int] = ('192.168.1.2', 8080)  # app address, NEED TO BE MODIFIED!


# methods definition
def handle_client(client_socket, client_address):
    print("Connection from", client_address)

    # The server will keep the connection until client closes it
    while True:
        data = client_socket.recv(1024)
        if not data:
            break  # when client close connection, break the loop,and close connection
        received_message = data.decode('utf-8')
        print(f"Received message from {client_address}: {received_message}")

        # analyze msg and handle it
        # msg from huzzah's connection requesting door open
        if received_message == "REQUEST_DOOROPEN_HUZZAH":

            # send request to app via a new socket 'app_socket'
            request_usr_message = "REQUEST_DOOROPEN_SERVER"
            app_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_socket.connect(app_address)
            app_socket.send(request_usr_message.encode('utf-8'))
            app_socket.close()

            # send ack to huzzah
            client_socket.send("request_sent_to_app".encode('utf-8'))

        # msg from app's connection permitting door open
        elif received_message == "USR_PERMIT_DOOROPEN":

            # send permit to huzzah
            dooropen_permit_message = "PERMIT_DOOROPEN"
            huzzah_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            huzzah_socket.connect(huzzah_address)
            huzzah_socket.send(dooropen_permit_message.encode('utf-8'))
            huzzah_socket.close()

            # send ack to app
            client_socket.send("permit_sent_to_huzzah".encode('utf-8'))

        elif received_message == "USR_TURN_ON_PROTECT":

            message_to_huzzah = "TURN_ON_PROTECT"
            huzzah_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            huzzah_socket.connect(huzzah_address)
            huzzah_socket.send(message_to_huzzah.encode('utf-8'))
            huzzah_socket.close()

            # send ack to app
            client_socket.send("protect_on_sent_to_huzzah".encode('utf-8'))

        elif received_message == "USR_TURN_OFF_PROTECT":

            message_to_huzzah = "TURN_OFF_PROTECT"
            huzzah_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            huzzah_socket.connect(huzzah_address)
            huzzah_socket.send(message_to_huzzah.encode('utf-8'))
            huzzah_socket.close()

            # send ack to app
            client_socket.send("protect_off_sent_to_huzzah".encode('utf-8'))

    # close tcp connection
    client_socket.close()
    print(f"Connection with {client_address} closed.")


# initialize Socket connection
server_address = ('0.0.0.0', 8080)  # 0.0.0.0 allow from any ip connection
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)
server_socket.listen(5)  # 5 connections max

print("Waiting for a connection...")

# multi-threading handles different connections at the same time
while True:
    client_socket, client_address = server_socket.accept()
    client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_handler.start()

