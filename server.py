import threading

import cv2
import socket
import pickle
import struct

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '0.0.0.0'  # Use 0.0.0.0 to accept connections from any IP
port = 9999
socket_address = (host, port)

# Bind the socket to the address
server_socket.bind(socket_address)

# Listen for incoming connections
server_socket.listen(5)
print("Listening at", socket_address)

data = b""
payload_size = struct.calcsize("Q")


def update_frame(client_socket):
    global data
    while len(data) < payload_size:
        packet = client_socket.recv(4 * 1024)  # Adjust the buffer size as needed
        if not packet:
            break
        data += packet
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4 * 1024)  # Adjust the buffer size as needed

    frame_data = data[:msg_size]
    data = data[msg_size:]
    frm = pickle.loads(frame_data)
    return frm


def accept_connections():
    while True:
        client_socket, addr = server_socket.accept()

        #if client_socket:
        print('GOT CONNECTION FROM:', addr)
        threading.Thread(target=client_handler, args=(client_socket,)).start()


def client_handler(connection):
    while True:
        frame = update_frame(connection)

        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        connection.sendall(message)


accept_connections()
