import socket
import tkinter as tk
from threading import Thread
import protocol4
import cv2
from PIL import Image, ImageTk


class client:
    def __init__(self):
        # <editor-fold desc="Socket Setup">
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.host = '127.0.0.1'
        self.port = 9999
        self.client_socket.connect((self.host, self.port))
        print("Connected to server")

        # </editor-fold>

        # <editor-fold desc="GUI">

        self.root = tk.Tk()

        self.close_button = tk.Button(self.root, text="Close", command=self.close_connection)
        self.close_button.grid(row=0, column=0)

        self.labels = []

        # </editor-fold>

        self.data = b''
        self.my_index = 6

        self.start()

    def close_connection(self):
        print("Closing Connection")
        self.client_socket.close()
        self.root.destroy()

    def send(self):
        vid = cv2.VideoCapture(0)  # 0 for the default camera

        vid.set(3, 100)
        vid.set(4, 75)

        while True:
            img, frame = vid.read()

            # indexes here dont matter becuase server isnt reading them
            protocol4.send_frame(self.client_socket, frame, 0, 0)
            self.draw_GUI_frame(frame, self.my_index)

    def receive(self):
        while True:
            frame, self.data, index, self.my_index = protocol4.receive_frame(self.client_socket, self.data)

            if bytes(frame) != b'' and index != self.my_index:
                self.draw_GUI_frame(frame, int(index))

    def draw_GUI_frame(self, frame, index):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)
        frame = ImageTk.PhotoImage(image=frame)

        while index >= len(self.labels):
            label = tk.Label(self.root)
            self.labels.append(label)

        self.labels[index].grid(row=index, column=0)

        self.labels[index].config(image=frame)
        self.labels[index].image = frame

        self.root.update()

    def start(self):
        Thread(target=self.receive).start()
        Thread(target=self.send).start()

        self.root.mainloop()


client()
