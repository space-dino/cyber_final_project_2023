import socket
import struct
from threading import Thread
import protocol4

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


class connection:
    def __init__(self, soc: socket, index: int):
        self.soc = soc
        self.frame = b''
        self.data = b''
        self.index = index


def accept_connections():
    while True:
        client_socket, addr = server_socket.accept()
        cli_index = len(clients)
        con = connection(client_socket, cli_index)
        clients.append(con)
        print("GOT CONNECTION FROM: " + str(addr[0]) + ":" + str(addr[1]) + "\nindex = " + str(cli_index) + "\n")

        Thread(target=send_to_client, args=(con,)).start()
        Thread(target=receive_from_client, args=(con,)).start()


def send_to_client(con: connection):
    while True:
        for i in range(len(clients)):
            protocol4.send_frame(con.soc, con.frame, i, con.index)


def receive_from_client(con: connection):
    while True:
        # indexes here are obsolete and passed as a null value
        con.frame, con.data, *_ = protocol4.receive_frame(con.soc, con.data)


accept_connections()
