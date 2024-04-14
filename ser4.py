import socket
import struct
from threading import Thread
import protocol4

# <editor-fold desc="Socket Setup">

vid_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
aud_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '0.0.0.0'
port = 9997
vid_socket_address = (host, port)
aud_socket_address = (host, port + 1)

vid_server_socket.bind(vid_socket_address)
aud_server_socket.bind(aud_socket_address)

vid_server_socket.listen()
aud_server_socket.listen()

print(socket.gethostname())
print("Listening video at", vid_socket_address, "audio at", aud_socket_address)

# </editor-fold>

vid_clients = []
aud_clients = []


class connection:
    def __init__(self, soc: socket, index: int):
        self.soc = soc
        self.frame = b''
        self.data = b''
        self.index = index


def accept_connections(soc: socket, lis):
    while True:
        client_socket, addr = soc.accept()
        cli_index = len(lis)
        con = connection(client_socket, cli_index)
        lis.append(con)
        print("GOT CONNECTION FROM: " + str(addr[0]) + ":" + str(addr[1]) + "\nindex = " + str(cli_index) + "\n")

        print_clients()

        Thread(target=send_to_client, args=(con,)).start()
        Thread(target=receive_from_client, args=(con,)).start()


def send_to_client(con: connection):
    b = True

    while b:
        for i in range(len(vid_clients)):
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
            remove_client(con, vid_clients)
            remove_client(con, aud_clients)


def remove_client(con: connection, lis):
    for i in lis:
        if i.index == con.index:
            print("removing " + str(i))
            lis.remove(i)

            for o in range(0, len(lis)):
                if lis[o] is None:
                    if o < len(lis) - 1:
                        lis[o].index = lis[o].index - 1
    print_clients()


def print_clients():
    for i in vid_clients:
        print(i.index)


Thread(target=accept_connections, args=(vid_server_socket, vid_clients,)).start()
Thread(target=accept_connections, args=(aud_server_socket, aud_clients,)).start()
