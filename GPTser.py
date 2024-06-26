import socket
from threading import Thread
import protocol4
import sqlite3
from datetime import datetime

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

vid_clients = []
aud_clients = []


class connection:
    def __init__(self, soc: socket.socket, index: int):
        self.soc = soc
        self.frame = b''
        self.data = b''
        self.index = index


def accept_connections(soc: socket.socket, lis):
    while True:
        client_socket, addr = soc.accept()
        cli_index = int(str(addr[0]).replace(".", ""))
        con = connection(client_socket, cli_index)
        lis.append(con)

        if lis == vid_clients:
            print(f"GOT VIDEO CONNECTION FROM: ({addr[0]}:{addr[1]}) {cli_index}\n")
            update_database(cli_index, addr[0])

        if lis == aud_clients:
            print(f"GOT AUDIO CONNECTION FROM: ({addr[0]}:{addr[1]}) {cli_index}\n")

        Thread(target=handle_client, args=(con,)).start()


def handle_client(con: connection):
    if con in aud_clients:
        while True:
            try:
                data = con.soc.recv(1024 * 2)
                if not data:
                    break

                for i in aud_clients:
                    i.soc.sendall(data)
            except ConnectionResetError:
                remove_client(con, vid_clients)
                remove_client(con, aud_clients)
    else:
        while True:
            try:
                con.frame, con.data, *_ = protocol4.receive_frame(con.soc, con.data)
                for i in vid_clients:
                    ipos = get_index_pos(i)
                    cpos = get_index_pos(con)
                    protocol4.send_frame(i.soc, con.frame, 0, cpos, ipos)
            except ConnectionResetError:
                remove_client(con, vid_clients)
                remove_client(con, aud_clients)


def get_index_pos(i):
    sorted_numbers = sorted([conn.index for conn in vid_clients])
    pos = sorted_numbers.index(i.index)
    return pos


def remove_client(con: connection, lis):
    for i in lis:
        if i.index == con.index:
            print(f"Removing Connection {i.index}")
            lis.remove(i)
            sq = sqlite3.connect("video_chat.db")
            cur = sq.cursor()
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            sql = f'UPDATE participant SET logout_time = "{current_time}" WHERE name = {i.index}'
            cur.execute(sql)
            sq.commit()
            res = cur.execute("SELECT * FROM participant")
            print("*****SQL******\n", res.fetchall())

            for o in range(0, len(lis)):
                if lis[o] is None:
                    if o < len(lis) - 1:
                        lis[o].index -= 1


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


Thread(target=accept_connections, args=(vid_server_socket, vid_clients,)).start()
Thread(target=accept_connections, args=(aud_server_socket, aud_clients,)).start()
