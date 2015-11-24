import socket, sys, os, threading, random
from time import sleep
from pydub import AudioSegment
import pyaudio

class Stream(object):
	def __init__(self, port):
		self.sock = socket.socket()         # Create a socket object
		self.host = socket.gethostname() # Get local machine name
		self.port = port
		self.sock.bind((self.host, port))        # Bind to the port
		self.sock.listen(5)                 # Now wait for client connection.
		print("server running on " + self.host + ":" + str(port))
		self.songlist = os.listdir("../songs")
		self.current_song = AudioSegment.from_mp3("../songs/" + random.choice(self.songlist))
		self.clients = []

	def start(self):
		for chunk in self.current_song:
			# Simply skip the time for the client
			if len(self.clients) == 0:
				sleep(0.001)
			for client, address in self.clients:
				try:
					client.sendto(chunk.raw_data, address)
				except BrokenPipeError:
					self.clients.remove((client, address))

	def accept_incoming_connections(self):
		self.connect_thread = threading.Thread(target=self.accept_connection, 
								args=[])
		self.connect_thread.daemon = True
		self.connect_thread.start()

	def accept_connection(self):
		while True:
			c, addr = self.sock.accept()
			print("found a client!")
			width = self.current_song.sample_width
			f_rate = self.current_song.frame_rate * 2
			chunk_size = len(self.current_song[0].raw_data)
			data = "NS," + str(width) + "," + str(f_rate) + "," + str(chunk_size)
			c.sendto(bytes(data, "UTF-8"), addr)

			self.clients.append((c, addr))