import socket
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
        print("GOT CONNECTION FROM: " + str(addr[0]) + ":" + str(addr[1]) + "\nindex = " + str(len(clients) - 1) + "\n")

        frames.append(b'')
        data.append(b'')

        Thread(target=send_to_client, args=(client_socket, len(clients) - 1)).start()
        Thread(target=receive_from_client, args=(client_socket,)).start()


def send_to_client(connection, index):
    global frames
    while True:
        protocol.send_frame(connection, frames[0], index)


def receive_from_client(connection):
    global frames, data
    while True:
        frames[0], data[0], index = protocol.receive_frame(connection, data[0])


accept_connections()
