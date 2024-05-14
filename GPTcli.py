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

class Client:
    def __init__(self):
        self.setup_audio()
        self.setup_gui()
        self.setup_network()
        self.vid = cv2.VideoCapture(0)
        self.vid.set(3, 320)  # Reduce frame width
        self.vid.set(4, 240)  # Reduce frame height
        self.mainloop()

    def setup_audio(self):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.A_CHUNK = 1024
        self.audio = pyaudio.PyAudio()
        self.in_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                         rate=self.RATE, input=True, frames_per_buffer=self.A_CHUNK)
        self.out_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                          rate=self.RATE, output=True, frames_per_buffer=self.A_CHUNK)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.username = ""
        self.window = tk.Toplevel(self.root)
        self.window.title("Enter Your Name")
        tk.Label(self.window, text="Enter your name:").pack()
        self.entry = tk.Entry(self.window)
        self.entry.pack()
        tk.Button(self.window, text="Join Meeting", command=self.submit).pack()
        tk.Button(self.root, text="Close", command=self.close_connection).grid(row=0, column=1)
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

    def setup_network(self):
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '127.0.0.1'
        self.port = 9997

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
            self.send_data(self.video_socket, compressed_frame, self.my_index)
            counter += 1
            if (time.time() - start_time) >= 1:
                fps = counter
                counter = 0
                start_time = time.time()
            self.draw_GUI_frame(frame, self.my_index, f"{fps} fps")

    def receive_vid(self):
        while self.up:
            frame_data, index = self.receive_data(self.video_socket)
            if frame_data and index != self.my_index:
                decompressed_frame = lz4.frame.decompress(frame_data)
                frame = np.frombuffer(decompressed_frame, dtype=np.uint8)
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                self.draw_GUI_frame(frame, int(index))

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
        self.index_label.config(text=f"client {index}")
        if fps:
            self.fps_label.config(text=fps)
        self.root.update()

    def send_data(self, socket, data, index):
        data = pickle.dumps((index, data))
        message = struct.pack("Q", len(data)) + data
        socket.sendall(message)

    def receive_data(self, socket):
        data_size = struct.calcsize("Q")
        while len(self.vid_data) < data_size:
            self.vid_data += socket.recv(4096)
        packed_size = self.vid_data[:data_size]
        self.vid_data = self.vid_data[data_size:]
        msg_size = struct.unpack("Q", packed_size)[0]
        while len(self.vid_data) < msg_size:
            self.vid_data += socket.recv(4096)
        data = self.vid_data[:msg_size]
        self.vid_data = self.vid_data[msg_size:]
        index, frame_data = pickle.loads(data)
        return frame_data, index

    def start_threads(self):
        Thread(target=self.send_vid).start()
        Thread(target=self.send_aud).start()
        Thread(target=self.receive_vid).start()
        Thread(target=self.receive_aud).start()

    def mainloop(self):
        self.root.mainloop()

Client()
