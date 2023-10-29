import socket
import tkinter as tk
from threading import Thread
import protocol
import cv2
from PIL import Image, ImageTk

# <editor-fold desc="Socket Setup">

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
port = 9999
client_socket.connect((host, port))
print("Connected to server")


# </editor-fold>


def close_connection():
    print("Closing Connection")
    client_socket.close()
    root.destroy()


# <editor-fold desc="GUI">

root = tk.Tk()

close_button = tk.Button(root, text="Close", command=close_connection)
close_button.grid(row=0, column=0)

labels = []

# </editor-fold>

data = b''
my_index = 6


def send():
    vid = cv2.VideoCapture(0)  # 0 for the default camera

    vid.set(3, 100)
    vid.set(4, 75)

    while True:
        img, frame = vid.read()

        # indexes here dont matter becuase server isnt reading them
        protocol.send_frame(client_socket, frame, 0, 0)
        draw_GUI_frame(frame, my_index)


def receive():
    global data, my_index
    while True:
        frame, data, index, my_index = protocol.receive_frame(client_socket, data)

        if bytes(frame) != b'' and index != my_index:
            draw_GUI_frame(frame, int(index))


def draw_GUI_frame(frame, index):
    global labels
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)
    frame = ImageTk.PhotoImage(image=frame)

    while index >= len(labels):
        label = tk.Label(root)
        labels.append(label)

    labels[index].grid(row=index, column=0)

    labels[index].config(image=frame)
    labels[index].image = frame

    root.update()


Thread(target=receive).start()
Thread(target=send).start()

root.mainloop()
