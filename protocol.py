import pickle
import struct

payload_size = struct.calcsize("Q") # unsigned Long Long = 8 bytes


def send_video_frame(connection, frame):
    data = pickle.dumps(frame)
    message = struct.pack("Q", len(data)) + data
    connection.sendall(message)


def receive_video_frame(connection, data):
    packed_msg_size, data = receive_parameter(connection, data, payload_size)
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    frame_data, data = receive_parameter(connection, data, msg_size)
    frame = pickle.loads(frame_data)

    return frame, data


def receive_parameter(connection, data, size):
    while len(data) < size:
        data += connection.recv(4096)

    parameter = data[:size]
    data = data[size:]

    return parameter, data
