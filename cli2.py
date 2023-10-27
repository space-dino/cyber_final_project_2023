import socket
import threading
from tkinter import *
from PIL import Image, ImageTk

# socket creation
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
port = 9999
client_socket.connect((host, port))

# GUI initiation
root = Tk()
root.title("Video Stream")

labels = []


def send():
    while True:
        for i in range(0, 1023):
            client_socket.send(str(66666666).encode())
        for i in range(0, 1023):
            client_socket.send(str(77777777).encode())


def receive():
    while True:
        index = client_socket.recv(4).decode()
        frame_length = int(client_socket.recv(8).decode())
        frame = client_socket.recv(frame_length).decode()

        # print(str(index) + " " + str(frame_length) + " " + str(frame))

        GUI_frame(frame, int(index))


def GUI_frame(frame, index):
    if index >= len(labels):
        label = Label(root)
        labels.append(label)
    labels[index]['text'] = str(frame)
    labels[index].grid(column=index, row=0, sticky='new', pady=20, padx=20)


threading.Thread(target=send).start()
threading.Thread(target=receive).start()

root.mainloop()
