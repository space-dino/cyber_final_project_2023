import socket
from threading import Thread
import protocol4
import pyaudio
import sqlite3
from datetime import datetime

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

        if lis == vid_clients:
            print("GOT VIDEO CONNECTION FROM:\n(" + str(addr[0]) + ":" + str(addr[1]) + ") " + str(cli_index) + "\n")
            update_database(cli_index, addr[0]) # Update db

        if lis == aud_clients:
            print("GOT AUDIO CONNECTION FROM:\n(" + str(addr[0]) + ":" + str(addr[1]) + ") " + str(cli_index) + "\n")

        # print_clients()


        Thread(target=send_to_client, args=(con, lis,)).start()
        Thread(target=receive_from_client, args=(con,)).start()


def send_to_client(con: connection, lis):
    b = True

    while b:
        for i in range(len(lis)):
            try:
                protocol4.send_frame(con.soc, lis[i].frame, 0, i, con.index)
            except ConnectionResetError:
                b = False


def receive_from_client(con: connection):
    while True:
        try:
            # indexes here are obsolete and passed as a null value
            con.frame, con.data, *_ = protocol4.receive_frame(con.soc, con.data)

            # audio test!!!
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            A_CHUNK = 1024
            audio = pyaudio.PyAudio()

            out_stream = audio.open(format=FORMAT, channels=CHANNELS,
                                    rate=RATE, output=True,
                                    frames_per_buffer=A_CHUNK)

            if con in aud_clients:
                out_stream.write(con.frame)

        except ConnectionResetError:
            remove_client(con, vid_clients)
            remove_client(con, aud_clients)


def remove_client(con: connection, lis):
    for i in lis:
        if i.index == con.index:
            print("Removing Connection" + str(i.index))
            lis.remove(i)

            # <editor-fold desc="SQL Update">

            sq = sqlite3.connect("video_chat.db")
            cur = sq.cursor()

            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")

            sql = 'UPDATE participant SET logout_time = "{}" WHERE name = {}'.format(str(current_time), i.index)
            print (sql)
            cur.execute(sql)
            sq.commit()
            res = cur.execute("SELECT * FROM participant")
            print("*****SQL******\n", res.fetchall())

            # </editor-fold>

            for o in range(0, len(lis)):
                if lis[o] is None:
                    if o < len(lis) - 1:
                        lis[o].index = lis[o].index - 1
    # print_clients()


def update_database(name, ip):
    sq = sqlite3.connect("video_chat.db")
    cur = sq.cursor()

    res = cur.execute("SELECT name FROM sqlite_master WHERE name='participant'")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE participant(name, ip, login_time, logout_time)")

    res = cur.execute("SELECT name FROM participant")

    if name not in res.fetchall():
        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")

        insert = """INSERT INTO participant(name, ip, login_time, logout_time) VALUES (?, ?, ?, ?);"""
        data_tuple = (name, ip, current_time, "")
        cur.execute(insert, data_tuple)
        sq.commit()
        res = cur.execute("SELECT * FROM participant")
        print("*****SQL******\n", res.fetchall())


def print_clients():
    for i in vid_clients:
        print(i.index)


Thread(target=accept_connections, args=(vid_server_socket, vid_clients,)).start()
Thread(target=accept_connections, args=(aud_server_socket, aud_clients,)).start()
