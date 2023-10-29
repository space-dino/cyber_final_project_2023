import pickle
import struct

payload_size = struct.calcsize("Q")  # unsigned Long Long = 8 bytes
index_size = struct.calcsize("I")  # unsigned Int = 4 bytes


def send_frame(connection, frame, index, my_index):
    data = pickle.dumps(frame)
    message = struct.pack("I", index) + struct.pack("I", my_index) + struct.pack("Q", len(data)) + data
    connection.sendall(message)

    # Packet Structure:
    """ 
    
    index - 4 bytes unsigned int
    my_index - 4 bytes unsigned int
    data_length - 8 bytes unsigned long long
    data - data_length bytes data
    
    """


def receive_frame(connection, data):
    packed_index, data = receive_parameter(connection, data, index_size)  # index
    index = struct.unpack("I", packed_index)[0]

    packed_my_index, data = receive_parameter(connection, data, index_size)  # my_index
    my_index = struct.unpack("I", packed_my_index)[0]

    packed_msg_size, data = receive_parameter(connection, data, payload_size)  # data_length
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    frame_data, data = receive_parameter(connection, data, msg_size)  # data
    frame = pickle.loads(frame_data)

    return frame, data, index, my_index


def receive_parameter(connection, data, size):
    while len(data) < size:
        data += connection.recv(4096)

    parameter = data[:size]
    data = data[size:]

    return parameter, data
