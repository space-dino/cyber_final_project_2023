import socket
import tkinter as tk
from threading import Thread
import protocol4
import cv2
from PIL import Image, ImageTk
import pyaudio


class client:
    def __init__(self):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.A_CHUNK = 1024
        self.audio = pyaudio.PyAudio()
        self.in_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                         rate=self.RATE, input=True, frames_per_buffer=self.A_CHUNK)
        self.out_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                          rate=self.RATE, output=True, frames_per_buffer=self.A_CHUNK)

        self.vid = None

        print("Client up")
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.host = '127.0.0.1'
        self.port = 9997

        self.root = tk.Tk()
        self.root.withdraw()

        self.username = ""
        self.window = tk.Toplevel(self.root)
        self.window.title("Enter Your Name")

        self.label = tk.Label(self.window, text="Enter your name:")
        self.label.pack()

        self.entry = tk.Entry(self.window)
        self.entry.pack()

        self.submit_button = tk.Button(self.window, text="Join Meeting", command=self.submit)
        self.submit_button.pack()

        self.close_button = tk.Button(self.root, text="Close", command=self.close_connection)
        self.close_button.grid(row=0, column=1)

        self.index_label = tk.Label(self.root, text="index")
        self.index_label.grid(row=1, column=1)
        self.fps_label = tk.Label(self.root, text="fps")
        self.fps_label.grid(row=2, column=1)
        self.username_label = tk.Label(self.root, text="username")
        self.username_label.grid(row=3, column=1)

        self.labels = []

        self.vid_data = b''
        self.aud_data = b''

        self.my_index = 6

        self.up = True

        self.mainloop()

    def submit(self):
        self.username = self.entry.get()
        self.window.destroy()
        self.root.deiconify()
        self.username_label.config(text=self.username)

        self.video_socket.connect((self.host, self.port))
        self.audio_socket.connect((self.host, self.port + 1))
        print("Connected to server")

        self.start()

    def close_connection(self):
        self.in_stream.stop_stream()
        self.in_stream.close()
        self.out_stream.stop_stream()
        self.out_stream.close()

        self.audio.terminate()

        self.up = False
        print("Closing Connection")
        self.vid.release()
        self.video_socket.close()
        self.audio_socket.close()
        self.root.destroy()

    def send_vid(self):
        self.vid = cv2.VideoCapture(0)
        fps = self.vid.get(cv2.CAP_PROP_FPS)

        self.vid.set(3, 400)
        self.vid.set(4, 300)

        while self.up:
            img, unflipped = self.vid.read()
            vid_frame = cv2.flip(unflipped, 1)
            protocol4.send_frame(self.video_socket, vid_frame, 0, 0, self.my_index)
            self.draw_GUI_frame(vid_frame, self.my_index, fps)

    def receive_vid(self):
        while self.up:
            vid_frame, self.vid_data, index, self.my_index = protocol4.receive_frame(self.video_socket, self.vid_data)
            if bytes(vid_frame) != b'' and index != self.my_index:
                self.draw_GUI_frame(vid_frame, int(index))

    def send_aud(self):
        while self.up:
            aud_frame = self.in_stream.read(self.A_CHUNK)

            self.audio_socket.sendall(aud_frame)

    def receive_aud(self):
        while self.up:
            aud_frame = self.audio_socket.recv(self.A_CHUNK * 2)
            if not aud_frame:
                break
            self.out_stream.write(aud_frame)

    def draw_GUI_frame(self, frame, index, fps=None):
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
        if fps:
            self.fps_label.config(text=str(fps) + "fps")

        self.root.update()

    def start(self):
        Thread(target=self.send_vid).start()
        Thread(target=self.send_aud).start()
        Thread(target=self.receive_vid).start()
        Thread(target=self.receive_aud).start()

    def mainloop(self):
        self.root.mainloop()


client()
