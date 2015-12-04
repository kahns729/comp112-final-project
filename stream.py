import socket, sys, os, threading, random, select
from time import sleep
from pydub import AudioSegment
from collections import deque
import pyaudio

class Stream(object):
	def __init__(self, port):
		self.sock = socket.socket()         # Create a socket object
		self.host = socket.gethostname() # Get local machine name
		self.port = port
		self.sock.bind((self.host, port + 1))        # Bind to the port
		self.sock.listen(5)                 # Now wait for client connection.
		self.request_sock = socket.socket()
		self.request_sock.bind((self.host, port))
		self.request_sock.listen(5)
		print("server running on " + self.host + " " + str(port))
		self.songlist = os.listdir("../songs")
		#self.current_song = AudioSegment.from_mp3("../songs/" + random.choice(self.songlist))
		self.current_song = AudioSegment.from_mp3("../songs/Snoop Dogg - Smoke Weed Everyday Sound Effect (music) for mlg.mp3")
		self.clients = []
		self.rclients = []
		self.request_list = deque([])
		self.request_thread_started = False
		self.chunk_size = None
		self.has_client = False
		self.disconnect_count = 0
		self.handling_disc = False
		# self.last_disc = -1
		# self.available_ports = []

	def start(self):
		while True:
			if len(self.request_list) != 0:
				self.current_song = AudioSegment.from_mp3("../songs/" + self.request_list.popleft())
			else:
				#self.current_song = AudioSegment.from_mp3("../songs/" + random.choice(self.songlist))
				self.current_song = AudioSegment.from_mp3("../songs/Snoop Dogg - Smoke Weed Everyday Sound Effect (music) for mlg.mp3")
			self.new_song()
			for chunk in self.current_song:
				# Simply skip the time for the client
				if not self.has_client:
					sleep(0.001)
				#for client, address in self.clients:
				else:
					client, address = self.clients[0]
					try:
						# chunk = chunk.raw_data[:self.chunk_size].l
						chunk = chunk.raw_data
						chunk = chunk[:self.chunk_size].ljust(self.chunk_size)
						if len(chunk) != self.chunk_size:
							print("poop")
						chunk_length = str(len(chunk))
						client.sendto(bytes("SC" + chunk_length + (4-len(chunk_length))*" ", "UTF-8"), address)
						client.sendto(chunk, address)
					except BrokenPipeError:
						# Remove client from request clients and clients list
						#self.rclients.pop(self.clients.index((client, address)))
						#self.clients.remove((client, address))
						# print("broke pipe")
						pass

	def accept_incoming_connections(self):
		self.connect_thread = threading.Thread(target=self.accept_connection, 
								args=[])
		self.connect_thread.daemon = True
		self.connect_thread.start()

		if not self.request_thread_started:
				self.request_thread = threading.Thread(target=self.request, args=[])
				self.request_thread.daemon = True
				self.request_thread.start()
				self.request_thread_started = True

	def accept_connection(self):
		while True:
			c, address = self.sock.accept()
			# if (address[0], int(address[1]) + 2) not in [addr for c, addr in self.rclients]:
			# New client that hasn't yet connected and needs a request socket
			print(self.handling_disc)
			if not self.handling_disc or not self.clients:
				# print(str(((address[0]), int(address[1]))))
				print("got past the if")
				r, raddress = self.request_sock.accept()
				self.rclients.append((r, raddress))
				self.new_song(client=(c, address))
				# Pad and send the hostname to the client
				self.new_client(c, address)
				if len(self.clients) == 1:
					self.handling_disc = False
			else:
				# client_queue = deque(self.clients)
				# self.clients = list(client_queue.appendleft(client_queue.pop(self.last_disc)))
				# self.clients = list(deque(self.clients).appendleft((c, address)))
				# first_client = self.clients[self.last_disc]
				# self.clients.pop(self.last_disc)
				# self.clients.insert(self.last_disc, (c, address))
				self.handling_disc = False
				if self.clients:
					self.clients[0] = (c, address)
				else:
					self.clients.append((c, address))
				# if (c, address) not in self.clients:
				# 	print("whyyyyy")
				# 	print((c, address))
				# 	print(self.clients)

			print(address)
			# print(raddress)
			print("found a client!")
			self.has_client = True
			

	def new_client(self, client, address):
		# If this is the first client, stream directly from server
		if not self.clients:
			client.sendto(bytes("HOST/" + self.host + (100 - len(self.host) - 5) * " ", "UTF-8"), address)
			# if self.available_ports:
			# 	peer_streaming_port = str(self.available_ports.pop(0))
			# else:
			peer_streaming_port = str(self.port + 2 + self.disconnect_count + len(self.clients))
			client.sendto(bytes("PORT/" + peer_streaming_port + (100 - 5 - len(peer_streaming_port)) * " ", "UTF-8"), address)
			client, address = self.sock.accept()
			print(address)
			socket.gethostbyaddr(address[0])[0]
			self.clients.append((client, address))
		# Not the first client, connect it to last client in list
		else:
			a = self.clients[-1][1]
			host = socket.gethostbyaddr(a[0])[0]
			client.sendto(bytes("HOST/" + host + (100 - len(host) - 5) * " ", "UTF-8"), address)
			# if self.available_ports:
			# 	peer_streaming_port = str(self.available_ports.pop(0))
			# else:
			peer_streaming_port = str(self.port + 2 + self.disconnect_count + len(self.clients))
			# peer_streaming_port = str(self.port + 2 + self.disconnect_count + len(self.clients))
			client.sendto(bytes("PORT/" + peer_streaming_port + (100 - 5 - len(peer_streaming_port)) * " ", "UTF-8"), address)
			self.clients.append((client, address))

	def new_song(self, client=None):
		width = self.current_song.sample_width
		f_rate = self.current_song.frame_rate * 2
		# The size of chunk the client will be listening for
		self.chunk_size = len(self.current_song[0].raw_data)
		data = str(width) + "/" + str(f_rate) + "/" + str(self.chunk_size)
		if client == None:
			# Pad data with whitespace so that we don't accidentally receive song data
			data = data + (100 - len(data)) * " "
			# for c, a in self.clients:
			if self.has_client:
				c, a = self.clients[0]
				try:
					c.sendto(bytes("NS100 ", "UTF-8"), a)
					c.sendto(bytes(data, "UTF-8"), a)
				except BrokenPipeError:
					pass
		# First message the client will receive
		else:
			# Pad data with whitespace so that we don't accidentally receive song data
			data = "NS/" + data
			# If first client
			# if not self.clients:
			# 	data = data + "/" + self.host
			data = data + (100 - len(data)) * " "
			c = client[0]
			a = client[1]
			c.sendto(bytes(data, "UTF-8"), a)

	def request(self):
		while True:
			socks = [client for client, address in self.rclients]
			# existing_socks = [client for client, address in self.clients]
			try:
				#print("select time what whaaaaaat")
				inputready, outputready, exceptready = select.select(socks,[],[],1)
			except select.error:
				print("continuing, bitch")
				continue
			#print("select is done")
			for s in inputready:
				print(len(inputready))
				print("ping")
				data = s.recv(100)
				#print("pong")
				parsed_data = data.decode("utf-8").split(",")
				command = parsed_data[0]
				#print(parsed_data)
				try:
					address = self.rclients[socks.index(s)][1]
				except IndexError:
					print("THIS IS BULLSHIT")
					continue
				if command == "SONGLIST":
					print("songlist requested")
					s.sendto(bytes((str(len(str(self.songlist))) + "##" + str(self.songlist)), "UTF-8"), address)
				elif command == "REQUESTLIST":
					s.sendto(bytes((str(len(",".join(self.request_list))) + "##" + str(",".join(self.request_list))), "UTF-8"), address)
				elif command == "PLAY":
					song_name = parsed_data[1]
					
					if song_name in self.request_list or song_name in [str(self.songlist.index(song) + 1) for song in self.request_list]:
						s.send(bytes("Song has already been requested!", "UTF-8"))
					elif os.path.isfile("../songs/" + song_name):
						self.request_list.append(song_name)
						s.send(bytes("Song " + song_name + " requested!", "UTF-8"))
					elif song_name in [str(i) for i in range(1, len(self.songlist) + 1)] and os.path.isfile("../songs/" + self.songlist[int(song_name) - 1]):
						self.request_list.append(self.songlist[int(song_name)-1])
						s.send(bytes("Song " + self.songlist[int(song_name)-1] + " requested!", "UTF-8"))
					else:
						s.send(bytes("Song does not exist", "UTF-8"))
				elif command == "DC":
					if socks.index(s) == 0:
						print("disconnecting")
						self.clients.pop(0)
						self.rclients.pop(0)
						self.handling_disc = True
						self.has_client = False
					else:
						self.rclients.pop(socks.index(s))
						self.clients.pop(socks.index(s))
						# If we are losing our client with the highest port number
					if socks.index(s) == len(self.clients):
						port = int(parsed_data[4])
						print(port)
						self.disconnect_count = port - 2 - self.port - len(self.clients)
						print(self.disconnect_count)
						# self.port + 2 + self.disconnect_count + len(self.clients) MUST EQUAL port - 1
						# peer_streaming_port = str(self.port + 2 + self.disconnect_count + len(self.clients))
					else:
						self.disconnect_count += 1
						

					# self.disconnect_count += 1
					# print("before: " + str(self.clients))
					
					# self.last_disc = socks.index(s)
					# self.clients.pop(socks.index(s))
					# self.rclients.pop(socks.index(s))
					# self.disc = (self.last_disc == 0)
					# self.has_client = (self.last_disc == 0)
					# print(self.has_client)
					# #print((s, address))
					# print(parsed_data)
					# host = parsed_data[2]
					# port = int(parsed_data[4]) - 1
					# self.available_ports.append(port)
					
					# print("after: " + str(self.clients))


	