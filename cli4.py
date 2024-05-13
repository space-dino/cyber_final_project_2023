import socket
import tkinter as tk
from threading import Thread
import protocol4
import cv2
from PIL import Image, ImageTk
import pyaudio


class client:
    def __init__(self):

        self.in_stream = None
        self.out_stream = None
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.A_CHUNK = 1024
        self.audio = pyaudio.PyAudio()

        self.vid = None

        # <editor-fold desc="Socket Setup">

        print("Client up")
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.host = '127.0.0.1'
        self.port = 9997

        # </editor-fold>

        # <editor-fold desc="GUI">

        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window initially

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
        # Label to display username
        self.username_label = tk.Label(self.root, text="username")
        self.username_label.grid(row=3, column=1)

        self.labels = []

        # </editor-fold>

        self.vid_data = b''
        self.aud_data = b''

        self.my_index = 6

        self.up = True

        self.mainloop()

    def submit(self):
        self.username = self.entry.get()
        self.window.destroy()
        self.root.deiconify()  # Show the main window
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
        self.vid = cv2.VideoCapture(0)  # 0 for the default camera
        fps = self.vid.get(cv2.CAP_PROP_FPS)

        self.vid.set(3, 400)
        self.vid.set(4, 300)

        while self.up:
            img, unflipped = self.vid.read()
            vid_frame = cv2.flip(unflipped, 1)

            # indexes here dont matter becuase server isnt reading them. flag does matter! ********* flags obsolete
            protocol4.send_frame(self.video_socket, vid_frame, 0, 0, self.username)  # video
            self.draw_GUI_frame(vid_frame, self.my_index, fps)

    def receive_vid(self):
        while self.up:
            vid_frame, self.vid_data, index, self.my_index = protocol4.receive_frame(self.video_socket, self.vid_data)

            if bytes(vid_frame) != b'' and index != self.my_index:
                self.draw_GUI_frame(vid_frame, int(index))

    def send_aud(self):
        # <editor-fold desc="Audio Settings">

        # Open a stream to capture audio

        self.in_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                         rate=self.RATE, input=True,
                                         frames_per_buffer=self.A_CHUNK)

        # </editor-fold>

        while self.up:
            aud_frame = self.in_stream.read(self.A_CHUNK)

            protocol4.send_frame(self.audio_socket, aud_frame, 1, 0, 0)  # audio
            # self.out_stream.write(aud_frame)

    def receive_aud(self):
        self.out_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                          rate=self.RATE, output=True,
                                          frames_per_buffer=self.A_CHUNK)

        while self.up:
            aud_frame, self.aud_data, index, self.my_index = protocol4.receive_frame(self.audio_socket, self.aud_data)
            # if bytes(aud_frame) != b'' and index != self.my_index:
            if bytes(aud_frame) != b'':
                self.out_stream.write(aud_frame)

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
        Thread(target=self.send_vid).start()
        Thread(target=self.send_aud).start()
        Thread(target=self.receive_vid).start()
        Thread(target=self.receive_aud).start()

    def mainloop(self):
        self.root.mainloop()


client()
