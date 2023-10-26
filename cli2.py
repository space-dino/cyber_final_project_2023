import socket
import threading

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'  # Replace with the server's IP
port = 9999
client_socket.connect((host, port))


def send():
    while True:
        client_socket.send(str(8).encode())


def receive():
    while True:
        m = client_socket.recv(32)
        print(m.decode())


threading.Thread(target=send).start()
threading.Thread(target=receive).start()
