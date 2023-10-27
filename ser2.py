import socket
import threading

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '0.0.0.0'
port = 9999
socket_address = (host, port)

server_socket.bind(socket_address)

server_socket.listen(5)
print("Listening at", socket_address)

clients = []
data = []

print("Host name is", socket.gethostname())


def accept_connections():
    while True:
        client_socket, addr = server_socket.accept()

        # if client_socket:
        print("GOT CONNECTION FROM: " + str(addr[0]) + ":" + str(addr[1]) + "\nindex = " + str(len(clients)) + "\n")
        threading.Thread(target=receive_from_client, args=(client_socket, 0, len(clients))).start()
        threading.Thread(target=send_to_client, args=(client_socket, 0)).start()

        clients.append(client_socket)
        data.append(b'')


def receive_from_client(connection, type, index):
    while True:
        data[index] = connection.recv(8)  # bytes obj?


def send_to_client(connection, type):
    while True:
        for i in range(0, len(clients)):
            message = str(i).zfill(4) + str(len(data[i])).zfill(8) + str(data[i].decode())
            connection.send(message.encode())


accept_connections()
