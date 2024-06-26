import socket
import tkinter as tk
from threading import Thread
import cv2
from PIL import Image, ImageTk
import pyaudio
import time
import pickle
import struct
import numpy as np
import lz4.frame
import protocol4

class Client:
    def __init__(self):
        self.FORMAT, self.CHANNELS, self.RATE, self.A_CHUNK, self.audio, self.in_stream, self.out_stream = self.setup_audio()
        self.root, self.username, self.window, self.entry, self.index_label, self.fps_label, self.username_label = self.setup_gui()
        self.video_socket, self.audio_socket, self.host, self.port = self.setup_network()
        self.labels, self.vid_data, self.aud_data, self.my_index, self.up = self.setup_data()
        self.vid = cv2.VideoCapture(0)
        self.vid.set(3, 320)  # Reduce frame width
        self.vid.set(4, 240)  # Reduce frame height
        self.mainloop()



    def setup_audio(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        A_CHUNK = 1024
        audio = pyaudio.PyAudio()
        in_stream = audio.open(format=FORMAT, channels=CHANNELS,
                               rate=RATE, input=True, frames_per_buffer=A_CHUNK)
        out_stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, output=True, frames_per_buffer=A_CHUNK)

        return FORMAT, CHANNELS, RATE, A_CHUNK, audio, in_stream, out_stream

    def setup_gui(self):
        root = tk.Tk()
        root.withdraw()
        username = ""
        window = tk.Toplevel(root)
        window.title("Enter Your Name")
        tk.Label(window, text="Enter your name:").pack()
        entry = tk.Entry(window)
        entry.pack()
        tk.Button(window, text="Join Meeting", command=self.submit).pack()
        tk.Button(root, text="Close", command=self.close_connection).grid(row=0, column=1)
        index_label = tk.Label(root, text="index")
        index_label.grid(row=1, column=1)
        fps_label = tk.Label(root, text="fps")
        fps_label.grid(row=2, column=1)
        username_label = tk.Label(root, text="username")
        username_label.grid(row=3, column=1)

        return root, username, window, entry, index_label, fps_label, username_label

    def setup_data(self):
        labels = []
        vid_data = b''
        aud_data = b''
        my_index = 0
        up = True

        return labels, vid_data, aud_data, my_index, up

    def setup_network(self):
        video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 9997

        return video_socket, audio_socket, host, port

    def submit(self):
        self.username = self.entry.get()

        self.window.destroy()
        self.root.deiconify()
        self.username_label.config(text=self.username)
        self.video_socket.connect((self.host, self.port))
        self.audio_socket.connect((self.host, self.port + 1))
        print("Connected to server")
        self.start_threads()

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
        counter = 0
        start_time = time.time()
        fps = 0
        while self.up:
            ret, frame = self.vid.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            _, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            compressed_frame = lz4.frame.compress(encoded_frame.tobytes())
            protocol4.send_frame(self.video_socket, compressed_frame, 0, 0, self.my_index)
            # self.send_data(self.video_socket, compressed_frame, self.my_index)

            counter += 1
            if (time.time() - start_time) >= 1:
                fps = counter
                counter = 0
                start_time = time.time()
            self.draw_GUI_frame(frame, self.my_index, f"{fps} fps")

    def receive_vid(self):
        while self.up:
            frame_data, vid_data, index, self.my_index = protocol4.receive_frame(self.video_socket, self.vid_data)

            if frame_data and index != self.my_index:
            # if frame_data:
                decompressed_frame = lz4.frame.decompress(frame_data)
                frame = np.frombuffer(decompressed_frame, dtype=np.uint8)
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                self.draw_GUI_frame(frame, index)

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
        if index != -1:
            self.index_label.config(text=f"client {index}")
        if fps:
            self.fps_label.config(text=fps)
        self.root.update()

    def start_threads(self):
        Thread(target=self.send_vid).start()
        Thread(target=self.send_aud).start()
        Thread(target=self.receive_vid).start()
        Thread(target=self.receive_aud).start()

    def mainloop(self):
        self.root.mainloop()


Client()
