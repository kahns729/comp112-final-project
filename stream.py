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
		self.sock.bind((self.host, port))        # Bind to the port
		self.sock.listen(5)                 # Now wait for client connection.
		self.request_sock = socket.socket()
		self.request_sock.bind((self.host, port + 1))
		self.request_sock.listen(5)
		print("server running on " + self.host + ":" + str(port))
		self.songlist = os.listdir("../songs")
		self.current_song = AudioSegment.from_mp3("../songs/" + random.choice(self.songlist))
		self.clients = []
		self.rclients = []
		self.request_list = deque([])
		self.request_thread_started = False
		self.chunk_size = None

	def start(self):
		while True:
			if len(self.request_list) != 0:
				self.current_song = AudioSegment.from_mp3("../songs/" + self.request_list.popleft())
			else:
				self.current_song = AudioSegment.from_mp3("../songs/" + random.choice(self.songlist))
			self.new_song()
			for chunk in self.current_song:
				# Simply skip the time for the client
				if len(self.clients) == 0:
					sleep(0.001)
				for client, address in self.clients:
					try:
						client.sendto(bytes("SC", "UTF-8"), address)
						client.sendto(chunk.raw_data[:self.chunk_size], address)
						#print(chunk.raw_data)
					except BrokenPipeError:
						# Remove client from request clients and clients list
						self.rclients.pop(self.clients.index((client, address)))
						self.clients.remove((client, address))

	def accept_incoming_connections(self):
		self.connect_thread = threading.Thread(target=self.accept_connection, 
								args=[])
		self.connect_thread.daemon = True
		self.connect_thread.start()

	def accept_connection(self):
		while True:
			c, address = self.sock.accept()
			r, raddress = self.request_sock.accept()
			print("found a client!")
			self.new_song(client=(c, address))
			self.clients.append((c, address))
			self.rclients.append((r, raddress))
			if not self.request_thread_started:
				self.request_thread = threading.Thread(target=self.request, args=[])
				self.request_thread.daemon = True
				self.request_thread.start()
				self.request_thread_started = True


	def new_song(self, client=None):
		width = self.current_song.sample_width
		f_rate = self.current_song.frame_rate * 2
		# The size of chunk the client will be listening for
		self.chunk_size = len(self.current_song[0].raw_data)
		data = str(width) + "/" + str(f_rate) + "/" + str(self.chunk_size)		
		if client == None:
			# Pad data with whitespace so that we don't accidentally receive song data
			data = data + (self.chunk_size - len(data)) * " "
			for c, a in self.clients:
				c.sendto(bytes("NS", "UTF-8"), a)
				c.sendto(bytes(data, "UTF-8"), a)
		else:
			# Pad data with whitespace so that we don't accidentally receive song data
			data = "NS/" + data
			data = data + (100 - len(data)) * " "
			c = client[0]
			a = client[1]
			c.sendto(bytes(data, "UTF-8"), a)

	def request(self):
		while True:
			print("merh")
			socks = [client for client, address in self.rclients]
			inputready, outputready, exceptready = select.select([],socks,[])
			print("select is done")
			for s in outputready:
				data = s.recv(100)
				parsed_data = data.decode("utf-8").split(",")
				command = parsed_data[0]
				print(parsed_data)
				address = self.rclients[socks.index(s)][1]
				if command == "SONGLIST":
					print("songlist requested")
					# s.sendto(bytes("SC", "UTF-8"), address)
					s.sendto(bytes(str(self.songlist), "UTF-8"), address)
				elif command == "REQUESTLIST":
					s.sendto(bytes(str(self.request_list), "UTF-8"), address)
				elif command == "PLAY":
					song_name = parsed_data[1]
					if os.path.isfile("../songs/" + song_name):
						self.request_list.append(song_name)
						s.send(bytes("Song requested!", "UTF-8"))
					else:
						s.send(bytes("Song does not exist", "UTF-8"))

		