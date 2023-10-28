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


def send():
    vid = cv2.VideoCapture(0)  # 0 for the default camera

    vid.set(3, 400)
    vid.set(4, 300)

    while True:
        img, frame = vid.read()
        protocol.send_video_frame(client_socket, frame)


def receive():
    global data
    while True:
        frame, data = protocol.receive_video_frame(client_socket, data)

        if bytes(frame) != b'':
            draw_GUI_frame(frame, 0)


def draw_GUI_frame(frame, index):
    global labels
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)
    frame = ImageTk.PhotoImage(image=frame)

    if index >= len(labels):
        label = tk.Label(root)
        labels.append(label)

    labels[index].grid(row=index, column=0)

    labels[index].config(image=frame)
    labels[index].image = frame

    root.update()


Thread(target=receive).start()
Thread(target=send).start()


root.mainloop()
