import socket, sys
import pyaudio

class StreamClient(object):
	def __init__(self, host, port):
		self.sock = socket.socket()         # Create a socket object
		self.host = host
		self.port = port
		self.sock.connect((host, port))
		self.request_sock = socket.socket()
		self.request_sock.connect((host, port + 1))
		self.width = 0
		self.f_rate = 0
		self.chunk_size = 0
		self.streaming = True
		self.stream = None

	def start(self):
		# First receive
		s_data_string, addr = self.sock.recvfrom(100)
		s_data = s_data_string.decode("utf-8").split("/")
		print(s_data)
		self.width = int(s_data[1])
		self.f_rate = int(s_data[2])
		self.chunk_size = int(s_data[3])
		# Get hostname that we should receive from
		hostname, addr = self.sock.recvfrom(100)
		print(hostname)
		hostname = hostname.decode("utf-8").split("/")
		print(hostname)
		print("Closing " + self.host + ", opening " + hostname[1])
		self.host = hostname[1].rstrip()
		self.sock.close()
		self.sock = socket.socket()
		self.sock.connect((self.host, self.port))

		# instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		# open stream (2)
		self.stream = p.open(format=p.get_format_from_width(self.width),
						channels=1,
		                rate=self.f_rate,
		                output=True)
		while self.streaming:
			header, addr = self.sock.recvfrom(2)
			# print(header)
			header = header.decode("utf-8")
			chunk, addr = self.sock.recvfrom(self.chunk_size)
			# print(chunk)
			# header = chunk.decode("utf-8").split("/////")
			if header == "NS":
				print("changing song")
				self.song_change(chunk, p)
			# elif header == "SL":
			# 	print("got songlist")
			# 	print(str(chunk).split(",")[1])
			elif header == "SC":
				# stream.write(bytes(header[1], "UTF-8"))
				self.stream.write(chunk)

	def stop(self):
		self.streaming = False

	def song_change(self, s_data, p):
		s_data = s_data.decode("utf-8").split("/")
		print(s_data)
		self.width = int(s_data[0])
		self.f_rate = int(s_data[1])
		self.chunk_size = int(s_data[2])
		self.stream = p.open(format=p.get_format_from_width(self.width),
						channels=1,
		                rate=self.f_rate,
		                output=True)


	def request_songlist(self):
		self.request_sock.send(bytes("SONGLIST", "UTF-8"))
		data = self.request_sock.recv(10).decode("utf-8").split("##")
		length = data[0]
		if int(length) > len(data):
			more_data = self.request_sock.recv(int(length) - len(data)).decode("utf-8")
			songs = data[1] + more_data
		else:
			songs = data[1]
		songs = songs.replace("[", " ")
		songs = songs.replace("]", "")
		songs = songs.replace('\'', "")
		song_list = songs.split(",")
		i = 1
		for song in song_list:
			print(str(i) + "." + song)
			i = i+1

	def request_songqueue(self):
		self.request_sock.send(bytes("REQUESTLIST", "UTF-8"))
		data = self.request_sock.recv(10).decode("utf-8").split("##")
		length = data[0]
		if int(length) > len(data):
			more_data = self.request_sock.recv(int(length) - len(data)).decode("utf-8")
			songs = data[1] + more_data
		else:
			songs = data[1]
		songs = songs.replace("[", " ")
		songs = songs.replace("]", "")
		songs = songs.replace('\'', "")
		request_list = songs.split(",")
		i = 1
		if request_list[0] != "":
			for song in request_list:
				print(str(i) + ". " + song)
				i = i+1
		else:
			print("No requests at this time")

	def request_song(self, songname):
		self.request_sock.send(bytes("PLAY," + songname, "UTF-8"))
		data = self.request_sock.recv(100).decode("utf-8")
		print(data)

