import socket, sys
import pyaudio
import threading
from collections import deque
from time import sleep

class StreamClient(object):
	def __init__(self, host, port):
		# Socket to receive data
		self.sock = socket.socket()         # Create a socket object
		self.host = host
		self.port = port
		# Connect to the server first
		self.sock.connect((host, port + 1))
		# Socket to send requests over
		self.request_sock = socket.socket()
		self.request_sock.connect((host, port))
		# Music information
		self.width = 0
		self.f_rate = 0
		self.chunk_size = 0
		# Are we receiving data?
		self.streaming = True
		# Our music stream, which plays the audio
		self.stream = None
		# Deprecated: Buffer to hold chunks
		self.chunk_buffer = deque([])
		# Socket connected to our peer whom we are serving
		self.client_sock = socket.socket()
		# Do we have such a peer?
		self.has_client = False
		# The peer
		self.client = None

	def start(self):
		# First receive, get song information so we can start playing
		s_data_string, addr = self.sock.recvfrom(100)
		s_data = s_data_string.decode("utf-8").split("/")
		self.width = int(s_data[1])
		self.f_rate = int(s_data[2])
		self.chunk_size = int(s_data[3])
		# Get hostname that we should receive from
		hostname, addr = self.sock.recvfrom(100)
		hostname = hostname.decode("utf-8").split("/")
		# Get port that we should receive from
		port, addr = self.sock.recvfrom(100)
		before = self.port + 1
		self.port = int(port.decode("utf-8").split("/")[1].rstrip())
		# Display connection information
		print("Closing " + self.host + ":" + str(before) + ", opening " 
			+ hostname[1].rstrip() + ":" + str(self.port - 1))
		# Start our socket to accept peers
		self.client_sock.bind((socket.gethostname(), self.port))
		self.client_sock.listen(5) 
		# Start streaming to peer (handles if we don't have one)
		self.stream_thread = threading.Thread(target=self.accept_and_stream, 
								args=[])
		self.stream_thread.daemon = True
		self.stream_thread.start()

		# Print this client's port
		print("Bound on " + str(self.port))
		# Connect to where we will receive our data
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
		# As long as we are streaming
		while self.streaming:
			# Receive and decode header packet
			header, addr = self.sock.recvfrom(6)
			header = header.decode("utf-8")
			# Receive data chunk
			chunk_size = int(header[2:])
			chunk, addr = self.sock.recvfrom(chunk_size)
			# If we didn't receive the whole chunk
			if len(chunk) < chunk_size:
				# Receive the rest of the chunk
				while len(chunk) != chunk_size:
					more_data, addr = self.sock.recvfrom(chunk_size - len(chunk))
					chunk = chunk + more_data
			# New Song header
			if header[:2] == "NS":
				print("Changing song")
				self.song_change(chunk, p)
				# If we have a client, forward the NS message
				if self.has_client:
					try:
						self.client.sendto(bytes("NS100 ", "UTF-8"), self.client_address)
						self.client.sendto(chunk, self.client_address)
					# Handle disconnect of the peer we are streaming to
					except BrokenPipeError:
						self.has_client = False
						# self.accept_and_stream()
						# Start a new stream, since this one has ended
						self.stream_thread.join()
						self.stream_thread.start()
			# Song chunk (most common)
			elif header[:2] == "SC":
				# Play the chunk in our music stream
				self.stream.write(chunk)
				# Stream only if we have a peer to stream to
				if self.has_client:
					chunk_length = str(len(chunk))
					# Ordinarily, send the song chunk
					try:
						self.client.sendto(bytes("SC" + chunk_length + (4 - len(chunk_length)) * " ", "UTF-8"), self.client_address)
						self.client.sendto(chunk, self.client_address)
					# If a client disconnects, receive a new client and wait
					#	until client is found until we start serving content
					except BrokenPipeError:
						self.has_client = False
						self.stream_thread.join()
						self.stream_thread = threading.Thread(target=self.accept_and_stream, 
								args=[])
						self.stream_thread.daemon = True
						self.stream_thread.start()
			# Disconnect notification
			elif header[:2] == "DC":
				data = chunk.decode("utf-8").split("#")
				# Connect to communicated host and port
				self.host = data[1]
				self.port = data[3]
				self.sock.close()
				self.sock = socket.socket()
				self.sock.connect((self.host, int(self.port) - 1))

	# Accept a client to stream to
	def accept_and_stream(self):
		self.client, self.client_address = self.client_sock.accept()

		print("found a client!")
		self.has_client = True
	
	# Call stop when client has requested to disconnect
	def stop(self):
		self.streaming = False
		# print("sending host and port")
		sleep(1)
		# No longer streaming, due to disconnect. If we have a client,
		if self.has_client:
			# send disconnect information to it
			data = "HOST#" + str(self.host) + "#PORT#" + str(self.port)
			data_length = str(len(data))
			self.client.sendto(bytes("DC" + data_length + (4 - len(data_length)) * " ", "UTF-8"), self.client_address)
			self.client.sendto(bytes(data, "UTF-8"), self.client_address)
		# Always tell server we have disconnected
		data = "HOST," + str(self.host) + ",PORT," + str(self.port)
		data_length = str(len(data))
		self.request_sock.send(bytes("DC," + data, "UTF-8"))

	# Change the song, based on received data
	def song_change(self, s_data, p):
		s_data = s_data.decode("utf-8").split("/")
		self.width = int(s_data[0])
		self.f_rate = int(s_data[1])
		self.chunk_size = int(s_data[2])
		self.stream = p.open(format=p.get_format_from_width(self.width),
						channels=1,
		                rate=self.f_rate,
		                output=True)

	# Request a list of songs the server has
	def request_songlist(self):
		# Send header
		self.request_sock.send(bytes("SONGLIST", "UTF-8"))
		# Receive information
		data = self.request_sock.recv(10).decode("utf-8").split("##")
		length = data[0]
		# If we have not received the full data, try to receive the rest
		if int(length) > len(data):
			more_data = self.request_sock.recv(int(length) - len(data)).decode("utf-8")
			songs = data[1] + more_data
		else:
			songs = data[1]
		# Clean the data
		songs = songs.replace("[", " ")
		songs = songs.replace("]", "")
		songs = songs.replace('\'', "")
		song_list = songs.split(",")
		i = 1
		# Display our song list
		for song in song_list:
			print(str(i) + "." + song)
			i = i+1

	# Request the list of requests that have been made
	def request_songqueue(self):
		# Send header
		self.request_sock.send(bytes("REQUESTLIST", "UTF-8"))
		# Try to receive data
		data = self.request_sock.recv(10).decode("utf-8").split("##")
		length = data[0]
		# If we have not received all data, try receiving the rest
		if int(length) > len(data):
			more_data = self.request_sock.recv(int(length) - len(data)).decode("utf-8")
			songs = data[1] + more_data
		else:
			songs = data[1]
		# Clean the data
		songs = songs.replace("[", " ")
		songs = songs.replace("]", "")
		songs = songs.replace('\'', "")
		request_list = songs.split(",")
		i = 1
		# Display the requests list, or inform that no requests exist
		if request_list[0] != "":
			for song in request_list:
				print(str(i) + ". " + song)
				i = i+1
		else:
			print("No requests at this time")

	# Request a song to be played by the server
	def request_song(self, songname):
		self.request_sock.send(bytes("PLAY," + songname, "UTF-8"))
		data = self.request_sock.recv(100).decode("utf-8")
		print(data)

