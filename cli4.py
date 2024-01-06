import socket
import tkinter as tk
from threading import Thread
import protocol4
import cv2
from PIL import Image, ImageTk
import pyshine as ps # pip install https://storage.googleapis.com/tensorflow/mac/cpu/tensorflow-1.8.0-py3-none-any.whl


class client:
    def __init__(self):
        # <editor-fold desc="Socket Setup">
        self.vid = None
        print("Client up")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.host = '127.0.0.1'
        self.port = 9999
        self.client_socket.connect((self.host, self.port))
        print("Connected to server")

        # </editor-fold>

        # <editor-fold desc="GUI">

        self.root = tk.Tk()

        self.close_button = tk.Button(self.root, text="Close", command=self.close_connection)
        self.close_button.grid(row=0, column=1)

        self.index_label = tk.Label(self.root, text="index")
        self.index_label.grid(row=1, column=1)
        self.fps_label = tk.Label(self.root, text="fps")
        self.fps_label.grid(row=2, column=1)

        self.labels = []

        # </editor-fold>

        self.data = b''
        self.my_index = 6

        self.up = True

        self.start()

    def close_connection(self):
        self.up = False
        print("Closing Connection")
        self.vid.release()
        self.client_socket.close()
        self.root.destroy()

    def send(self):
        # Video
        self.vid = cv2.VideoCapture(0)  # 0 for the default camera
        fps = self.vid.get(cv2.CAP_PROP_FPS)

        self.vid.set(3, 400)
        self.vid.set(4, 300)

        # Audio
        audio_get, context = ps.audioCapture(mode='send')

        while self.up:
            img, unflipped = self.vid.read()
            vid_frame = cv2.flip(unflipped, 1)

            aud_frame = audio_get.get()

            # indexes here dont matter becuase server isnt reading them. flag does matter!
            protocol4.send_frame(self.client_socket, vid_frame, 0, 0, 0)  # video
            self.draw_GUI_frame(vid_frame, self.my_index, fps)

            protocol4.send_frame(self.client_socket, aud_frame, 1, 0, 0)  # audio

    def receive(self):
        audio_put, context = ps.audioCapture(mode='get')

        while self.up:
            frame, self.data, flag, index, self.my_index = protocol4.receive_frame(self.client_socket, self.data)

            if bytes(frame) != b'' and index != self.my_index:
                if flag == 0:  # video
                    self.draw_GUI_frame(frame, int(index))
                if flag == 1:  # audio
                    audio_put.put(frame)

    def draw_GUI_frame(self, frame, index, fps):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)
        frame = ImageTk.PhotoImage(image=frame)

        while index >= len(self.labels):
            label = tk.Label(self.root)
            self.labels.append(label)

        self.labels[index].grid(row=index, column=0)

        self.labels[index].config(image=frame)
        self.labels[index].image = frame

        self.index_label.config(text="client " + str(index))
        self.fps_label.config(text=str(fps) + "fps")

        self.root.update()

    def start(self):
        Thread(target=self.receive).start()
        Thread(target=self.send).start()

        self.root.mainloop()


client()
