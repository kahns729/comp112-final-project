import socket, sys, os, threading, random, select
from time import sleep
from pydub import AudioSegment
from collections import deque
import pyaudio

class Stream(object):
	def __init__(self, port):
		# Socket to stream to (first client socket)
		self.sock = socket.socket()         # Create a socket object
		self.host = socket.gethostname() # Get local machine name
		self.port = port
		self.sock.bind((self.host, port + 1))        # Bind to the port
		self.sock.listen(5)                 # Now wait for client connection.
		# Socket to accept requests from all clients
		self.request_sock = socket.socket()
		self.request_sock.bind((self.host, port))
		self.request_sock.listen(5)
		print("server running on " + self.host + " " + str(port))
		# List of songs, and current song
		self.songlist = os.listdir("../songs")
		self.current_song = AudioSegment.from_mp3("../songs/" + random.choice(self.songlist))
		# Client sockets (all clients, including peers)
		self.clients = []
		# Client request sockets
		self.rclients = []
		# Songs that have been requested
		self.request_list = deque([])
		# Have we started our request thread yet
		self.request_thread_started = False
		# Deprecated: Size of song chunks
		self.chunk_size = None
		# Whether we have a client or not
		self.has_client = False
		# Offset to account for port assignment with disconnects
		self.disconnect_count = 0
		# Boolean to track whether we have finished handling current disconnect
		self.handling_disc = False

	def start(self):
		# Server runs until killed
		while True:
			# If we have a request, play it
			if len(self.request_list) != 0:
				self.current_song = AudioSegment.from_mp3("../songs/" + self.request_list.popleft())
			# Otherwise, play a random song
			else:
				self.current_song = AudioSegment.from_mp3("../songs/" + random.choice(self.songlist))
			self.new_song()
			# Stream the entire song
			for chunk in self.current_song:
				# Simply skip the time for the client
				if not self.has_client:
					sleep(0.001)
				else:
					# Stream chunk to first client
					client, address = self.clients[0]
					try:
						chunk = chunk.raw_data
						chunk = chunk[:self.chunk_size].ljust(self.chunk_size)
						chunk_length = str(len(chunk))
						client.sendto(bytes("SC" + chunk_length + (4-len(chunk_length))*" ", "UTF-8"), address)
						client.sendto(chunk, address)
					# Disconnects will be handled, just maybe not on time to avoid
					#	this error a few times. We just ignore the error
					except BrokenPipeError:
						pass

	def accept_incoming_connections(self):
		# Start a thread to accept connections
		self.connect_thread = threading.Thread(target=self.accept_connection, 
								args=[])
		self.connect_thread.daemon = True
		self.connect_thread.start()

		# If we haven't started our request handling thread, start it
		if not self.request_thread_started:
				self.request_thread = threading.Thread(target=self.request, args=[])
				self.request_thread.daemon = True
				self.request_thread.start()
				self.request_thread_started = True

	def accept_connection(self):
		while True:
			c, address = self.sock.accept()
			# New client that hasn't yet connected and needs a request socket
			if not self.handling_disc or not self.clients:
				# Add to request sockets, inform client of song information, and
				#	properly connect the client
				r, raddress = self.request_sock.accept()
				self.rclients.append((r, raddress))
				self.new_song(client=(c, address))
				# Pad and send the hostname to the client
				self.new_client(c, address)
				# Edge case: If all clients have disconnected, we are handling
				#	a disconnect but also connecting our first client.
				if len(self.clients) == 1:
					self.handling_disc = False
			else:
				# We have handled the disconnect after this
				self.handling_disc = False
				# Add the client that is connecting
				if self.clients:
					self.clients[0] = (c, address)
				else:
					self.clients.append((c, address))
			# Whether we had one before or not, we certainly have a client now
			self.has_client = True
			
	# Handle new client, including connecting them to the proper node
	def new_client(self, client, address):
		# TODO: Potentially repetitive code
		# If this is the first client, stream directly from server
		if not self.clients:
			client.sendto(bytes("HOST/" + self.host + (100 - len(self.host) - 5) * " ", "UTF-8"), address)
			peer_streaming_port = str(self.port + 2 + self.disconnect_count + len(self.clients))
			client.sendto(bytes("PORT/" + peer_streaming_port + (100 - 5 - len(peer_streaming_port)) * " ", "UTF-8"), address)
			client, address = self.sock.accept()
			socket.gethostbyaddr(address[0])[0]
			self.clients.append((client, address))
		# Not the first client, connect it to last client in list
		else:
			a = self.clients[-1][1]
			host = socket.gethostbyaddr(a[0])[0]
			client.sendto(bytes("HOST/" + host + (100 - len(host) - 5) * " ", "UTF-8"), address)
			peer_streaming_port = str(self.port + 2 + self.disconnect_count + len(self.clients))
			client.sendto(bytes("PORT/" + peer_streaming_port + (100 - 5 - len(peer_streaming_port)) * " ", "UTF-8"), address)
			self.clients.append((client, address))

	# Tell a single client, or all clients (depending on client argument)
	#	information about our current song
	def new_song(self, client=None):
		width = self.current_song.sample_width
		f_rate = self.current_song.frame_rate * 2
		# The size of chunk the client will be listening for
		self.chunk_size = len(self.current_song[0].raw_data)
		# Use forward slash as data delimeter (clients use this protocol too)
		data = str(width) + "/" + str(f_rate) + "/" + str(self.chunk_size)
		if client == None:
			# Pad data with whitespace so that we don't accidentally receive song data
			data = data + (100 - len(data)) * " "
			# Send information if we have clients (first client will forward the info)
			if self.has_client:
				c, a = self.clients[0]
				try:
					c.sendto(bytes("NS100 ", "UTF-8"), a)
					c.sendto(bytes(data, "UTF-8"), a)
				# Similarly to above, we will handle disconnect, just potentially
				#	not in time to avoid this error
				except BrokenPipeError:
					pass
		# First message the client will receive
		else:
			# Pad data with whitespace so that we don't accidentally receive song data
			data = "NS/" + data
			data = data + (100 - len(data)) * " "
			c = client[0]
			a = client[1]
			c.sendto(bytes(data, "UTF-8"), a)

	# Request thread. Handles client requests made from the command line
	#	interface, and handles disconnects
	def request(self):
		while True:
			# Get all our client request sockets
			socks = [client for client, address in self.rclients]
			try:
				# Select on the request sockets
				inputready, outputready, exceptready = select.select(socks,[],[],1)
			except select.error:
				continue
			# For each socket that has a request
			for s in inputready:
				data = s.recv(100)
				parsed_data = data.decode("utf-8").split(",")
				# Get the command header type
				command = parsed_data[0]
				try:
					# Get our client's address
					address = self.rclients[socks.index(s)][1]
				except IndexError:
					continue
				# Receive songlist request and send songlist, with "##" as delimeter
				if command == "SONGLIST":
					s.sendto(bytes((str(len(str(self.songlist))) + "##" + str(self.songlist)), "UTF-8"), address)
				# Receive and send requests list
				elif command == "REQUESTLIST":
					s.sendto(bytes((str(len(",".join(self.request_list))) + "##" + str(",".join(self.request_list))), "UTF-8"), address)
				# Receive request, and send whether successfully request
				elif command == "PLAY":
					song_name = parsed_data[1]
					# Check if song (by name or number) has already been requested
					if song_name in self.request_list or song_name in [str(self.songlist.index(song) + 1) for song in self.request_list]:
						s.send(bytes("Song has already been requested!", "UTF-8"))
					# If it has not, request it by name
					elif os.path.isfile("../songs/" + song_name):
						self.request_list.append(song_name)
						s.send(bytes("Song " + song_name + " requested!", "UTF-8"))
					# Or number
					elif song_name in [str(i) for i in range(1, len(self.songlist) + 1)] and os.path.isfile("../songs/" + self.songlist[int(song_name) - 1]):
						self.request_list.append(self.songlist[int(song_name)-1])
						s.send(bytes("Song " + self.songlist[int(song_name)-1] + " requested!", "UTF-8"))
					# Or it does not exist
					else:
						s.send(bytes("Song does not exist", "UTF-8"))
				# Disconnect request from client
				elif command == "DC":
					# If it's a disconnect from our immediate client
					if socks.index(s) == 0:
						self.clients.pop(0)
						self.rclients.pop(0)
						self.handling_disc = True
						# We no longer have a client, must find a new one
						self.has_client = False
					else:
						self.rclients.pop(socks.index(s))
						self.clients.pop(socks.index(s))
					# If we are losing our client with the highest port number
					if socks.index(s) == len(self.clients):
						port = int(parsed_data[4])
						# Make the disconnect_count correspond to the latest port
						self.disconnect_count = port - 2 - self.port - len(self.clients)
					else:
						# Simply increment disconnect_count
						self.disconnect_count += 1



	