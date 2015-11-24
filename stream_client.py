import socket, sys
import pyaudio

class StreamClient(object):
	def __init__(self, host, port):
		self.sock = socket.socket()         # Create a socket object
		self.host = host
		self.port = port
		self.sock.connect((host, port))
		self.width = 0
		self.f_rate = 0
		self.chunk_size = 0
		self.streaming = True

	def start(self):
		s_data_string, addr = self.sock.recvfrom(100)
		s_data = s_data_string.decode("utf-8").split("/")
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
		while self.streaming:
			header, addr = self.sock.recvfrom(2)
			header = header.decode("utf-8")
			chunk, addr = self.sock.recvfrom(self.chunk_size)
			# header = chunk.decode("utf-8").split("/////")
			if header == "NS":
				print("changing song")
				self.song_change(chunk)
			elif header == "SL":
				print("got songlist")
				print(str(chunk).split(",")[1])
			elif header == "SC":
				# stream.write(bytes(header[1], "UTF-8"))
				stream.write(chunk)

	def stop(self):
		self.streaming = False

	def song_change(self, s_data_string):
		s_data = s_data_string.decode("utf-8").split("/")
		self.width = int(s_data[1])
		self.f_rate = int(s_data[2])
		self.chunk_size = int(s_data[3])

	def request_songlist(self):
		self.sock.send(bytes("SONGLIST", "UTF-8"))
		# data = self.sock.recv(100)

	def request_songqueue(self):
		pass
	def request_song(self, songname):
		pass


