import socket
import cv2
import pickle
import struct
from tkinter import *
from PIL import Image, ImageTk
import threading

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'  # Replace with the server's IP
port = 9999
client_socket.connect((host, port))

data = b""
payload_size = struct.calcsize("Q")


def close_connection():
    client_socket.close()


# GUI
root = Tk()
root.title("Video Stream")
# root.resizable(False, False)
label = Label(root)
label.grid(row=0, column=0, sticky=W, pady=2)

label2 = Label(root)
label2.grid(row=1, column=0, sticky=W, pady=2)

l1 = Button(root, text="Close", command=close_connection)
l2 = Label(root, text="Second:")

l1.grid(row=1, column=0, sticky=W, pady=2)
l2.grid(row=2, column=0, sticky=W, pady=2)


def send_video():
    vid = cv2.VideoCapture(0)  # 0 for the default camera

    vid.set(3, 400)
    vid.set(4, 300)

    while True:
        if vid.isOpened():
            img, frame = vid.read()
            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            client_socket.sendall(message)


def update_frame():
    while True:
        global data
        global label

        index = client_socket.recv(1)

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

        update_GUI_frame(frm, index)


def update_GUI_frame(frm, index):
    # GUI
    frm = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB)
    frm = Image.fromarray(frm)
    frm = ImageTk.PhotoImage(image=frm)

    if index == 0:
        label.config(image=frm)
        label.image = frm
    if index == 1:
        label2.config(image=frm)
        label2.image = frm

    root.update()


threading.Thread(target=send_video).start()
threading.Thread(target=update_frame).start()

root.mainloop()

close_connection()
