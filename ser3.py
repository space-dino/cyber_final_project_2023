import socket
import struct
from threading import Thread
import  protocol

# <editor-fold desc="Socket Setup">

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '0.0.0.0'
port = 9999
socket_address = (host, port)
server_socket.bind(socket_address)

server_socket.listen()
print(socket.gethostname())
print("Listening at", socket_address)

# </editor-fold>

clients = []
frames = []
data = []


def accept_connections():
    while True:
        client_socket, addr = server_socket.accept()
        clients.append(client_socket)
        cli_index = len(clients) - 1
        print("GOT CONNECTION FROM: " + str(addr[0]) + ":" + str(addr[1]) + "\nindex = " + str(cli_index) + "\n")

        frames.append(b'')
        data.append(b'')

        Thread(target=send_to_client, args=(client_socket, cli_index)).start()
        Thread(target=receive_from_client, args=(client_socket, cli_index)).start()


def send_to_client(connection, index):
    global frames
    while True:
        for i in range(0, len(clients)):
            protocol.send_frame(connection, frames[i], i, index)


def receive_from_client(connection, index):
    global frames, data
    while True:
        # indexes here are obsolete and passed as a null value
        frames[index], data[index], ind, ind2 = protocol.receive_frame(connection, data[index])


accept_connections()
