import threading
import socket
import pickle
import struct

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '0.0.0.0'  # Use 0.0.0.0 to accept connections from any IP
port = 9999
socket_address = (host, port)

server_socket.bind(socket_address)

server_socket.listen(5)
print("Listening at", socket_address)

clients = []
data = [b""]

payload_size = struct.calcsize("Q")


def update_frame(client_socket, index):
    global data
    while len(data[index]) < payload_size:
        packet = client_socket.recv(16 * 1024)  # Adjust the buffer size as needed
        if not packet:
            break
        data[index] += packet
    packed_msg_size = data[index][:payload_size]
    data[index] = data[index][payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data[index]) < msg_size:
        data[index] += client_socket.recv(16 * 1024)  # Adjust the buffer size as needed

    frame_data = data[index][:msg_size]
    data[index] = data[index][msg_size:]
    frm = pickle.loads(frame_data)
    return frm


def accept_connections():
    while True:
        client_socket, addr = server_socket.accept()

        # if client_socket:
        print("GOT CONNECTION FROM: " + str(addr[0]) + ":" + str(addr[1]) + "\nindex = " + str(len(clients)) + "\n")
        threading.Thread(target=client_handler, args=(client_socket, 0, len(clients))).start()
        clients.append(addr)
        data.append(b"")


def client_handler(connection, type, index):
    while True:
        for i in range(0, len(clients)):
            frame = update_frame(connection, i)

            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            connection.send(i)
            connection.sendall(message)


accept_connections()
