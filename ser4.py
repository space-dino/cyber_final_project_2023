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

        print_clients()

        Thread(target=send_to_client, args=(con,)).start()
        Thread(target=receive_from_client, args=(con,)).start()


def send_to_client(con: connection):
    b = True

    while b:
        for i in range(len(clients)):
            try:
                protocol4.send_frame(con.soc, con.frame, 0, i, con.index)
            except ConnectionResetError:
                b = False


def receive_from_client(con: connection):
    while True:
        try:
            # indexes here are obsolete and passed as a null value
            a, con.data, flag, *_ = protocol4.receive_frame(con.soc, con.data)

            if flag == 0:
                con.frame = a

        except ConnectionResetError:
            remove_client(con)


def remove_client(con: connection):
    for i in clients:
        if i.index == con.index:
            print("removing " + str(i))
            clients.remove(i)

            for o in range(0, len(clients)):
                if clients[o] is None:
                    if o < len(clients) - 1:
                        clients[o].index = clients[o].index - 1
    print_clients()


def print_clients():
    for i in clients:
        print(i.index)


accept_connections()
