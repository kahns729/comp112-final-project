import socket, sys
import pyaudio
import threading
from collections import deque
from time import sleep

class StreamClient(object):
	def __init__(self, host, port):
		self.sock = socket.socket()         # Create a socket object
		self.host = host
		self.port = port
		self.sock.connect((host, port + 1))
		self.request_sock = socket.socket()
		self.request_sock.connect((host, port))
		self.width = 0
		self.f_rate = 0
		self.chunk_size = 0
		self.streaming = True
		self.stream = None
		self.chunk_buffer = deque([])
		self.client_sock = socket.socket()
		self.has_client = False
		self.client = None

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

		port, addr = self.sock.recvfrom(100)
		before = self.port + 1
		self.port = int(port.decode("utf-8").split("/")[1].rstrip())
		print("Closing " + self.host + ":" + str(before) + ", opening " 
			+ hostname[1] + ":" + str(self.port - 1))

		self.client_sock.bind((socket.gethostname(), self.port))
		self.client_sock.listen(5) 
		
		self.stream_thread = threading.Thread(target=self.accept_and_stream, 
								args=[])
		self.stream_thread.daemon = True
		self.stream_thread.start()

		print("bound on " + str(self.port))
		self.host = hostname[1].rstrip()
		self.sock.close()
		self.sock = socket.socket()
		self.sock.connect((self.host, self.port - 1))

		# instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		# open stream (2)
		self.stream = p.open(format=p.get_format_from_width(self.width),
						channels=1,
		                rate=self.f_rate,
		                output=True)
		while self.streaming:
			header, addr = self.sock.recvfrom(6)
			# print(header)
			header = header.decode("utf-8")
			# chunk, addr = self.sock.recvfrom(self.chunk_size)
			chunk_size = int(header[2:])
			chunk, addr = self.sock.recvfrom(chunk_size)
			if len(chunk) < chunk_size:
				print(len(chunk))
				# chunk = chunk.ljust(self.chunk_size)
				print("less than")
				while len(chunk) != chunk_size:
					more_data, addr = self.sock.recvfrom(chunk_size - len(chunk))
					chunk = chunk + more_data
			# print(chunk)
			# header = chunk.decode("utf-8").split("/////")
			if header[:2] == "NS":
				print("changing song")
				self.song_change(chunk, p)
				if self.has_client:
					try:
						self.client.sendto(bytes("NS100 ", "UTF-8"), self.client_address)
						self.client.sendto(chunk, self.client_address)
					except BrokenPipeError:
						self.has_client = False
						self.accept_and_stream()
						self.stream_thread.join()
						self.stream_thread.start()
			# elif header == "SL":
			# 	print("got songlist")
			# 	print(str(chunk).split(",")[1])
			elif header[:2] == "SC":
				# print("received a chunk")
				# stream.write(bytes(header[1], "UTF-8"))
				# print("chunk chunk chunk")
				self.stream.write(chunk)
				if self.has_client:
					# print("POOP")
					chunk_length = str(len(chunk))
					try:
						self.client.sendto(bytes("SC" + chunk_length + (4 - len(chunk_length)) * " ", "UTF-8"), self.client_address)
						self.client.sendto(chunk, self.client_address)
					except BrokenPipeError:
						self.has_client = False
						self.stream_thread.join()
						self.stream_thread = threading.Thread(target=self.accept_and_stream, 
								args=[])
						self.stream_thread.daemon = True
						self.stream_thread.start()
			elif header[:2] == "DC":
				data = chunk.decode("utf-8").split("#")
				self.host = data[1]
				self.port = data[3]
				print("host: " + self.host + ", port: " + self.port)
				self.sock.close()
				self.sock = socket.socket()
				self.sock.connect((self.host, int(self.port) - 1))


		


	def accept_and_stream(self):
		self.client, self.client_address = self.client_sock.accept()

		print("found a client!")
		self.has_client = True
		


	def stop(self):
		self.streaming = False
		print("sending host and port")
		sleep(1)
		# No longer streaming, due to disconnect
		if self.has_client:
			data = "HOST#" + str(self.host) + "#PORT#" + str(self.port)
			data_length = str(len(data))
			self.client.sendto(bytes("DC" + data_length + (4 - len(data_length)) * " ", "UTF-8"), self.client_address)
			self.client.sendto(bytes(data, "UTF-8"), self.client_address)
		data = "HOST," + str(self.host) + ",PORT," + str(self.port)
		data_length = str(len(data))
		self.request_sock.send(bytes("DC," + data, "UTF-8"))


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

