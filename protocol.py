import pickle
import struct

payload_size = struct.calcsize("Q") # unsigned Long Long = 8 bytes
index_size = struct.calcsize("I") # unsigned Int = 4 bytes


def send_frame(connection, frame, index):
    data = pickle.dumps(frame)
    message = struct.pack("I", index) + struct.pack("Q", len(data)) + data
    connection.sendall(message)


def receive_frame(connection, data):
    packed_index, data = receive_parameter(connection, data, index_size)
    index = struct.unpack("I", packed_index)[0]

    packed_msg_size, data = receive_parameter(connection, data, payload_size)
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    frame_data, data = receive_parameter(connection, data, msg_size)
    frame = pickle.loads(frame_data)

    return frame, data, index


def receive_parameter(connection, data, size):
    while len(data) < size:
        data += connection.recv(4096)

    parameter = data[:size]
    data = data[size:]

    return parameter, data
