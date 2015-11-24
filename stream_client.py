import socket, sys
import pyaudio

class StreamClient(object):
	def __init__(self, host, port):
		self.sock = socket.socket()         # Create a socket object
		self.host = host # Get local machine name
		self.port = port
		self.sock.connect((host, port))
		self.width = 0
		self.f_rate = 0
		self.chunk_size = 0

	def start(self):
		s_data_string, addr = self.sock.recvfrom(100)
		s_data = s_data_string.decode("utf-8").split(",")
		self.width = int(s_data[1])
		self.f_rate = int(s_data[2])
		self.chunk_size = int(s_data[3])

		# instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		# open stream (2)
		stream = p.open(format=p.get_format_from_width(self.width),
						channels=1,
		                rate=self.f_rate,
		                output=True)
		while True:
			chunk, addr = self.sock.recvfrom(self.chunk_size)
			if str(chunk).split(",")[0] == "NS":
				song_change(chunk)
			stream.write(chunk)

	def song_change(self, s_data_string):
		s_data = s_data_string.decode("utf-8").split(",")
		self.width = int(s_data[1])
		self.f_rate = int(s_data[2])
		self.chunk_size = int(s_data[3])