import socket, sys, os, threading
from pydub import AudioSegment
import pyaudio

def main(argv):
	s = socket.socket()         # Create a socket object

	# Expecting 3 arguments: client.py and the port
	if len(argv) < 2:
		print("usage: python server.py [port]")
		return 1

	host = socket.gethostname() # Get local machine name
	port = int(argv[1])                # Reserve a port for your service.

	s.bind((host, port))        # Bind to the port	

	s.listen(5)                 # Now wait for client connection.
	print("server running on " + host + ":" + str(port))
	song = AudioSegment.from_mp3("../audio/allstar.mp3")

	clients = []

	# c, addr = s.accept()     # Establish connection with client.

	connect_thread = threading.Thread(target=accept_connection, args=[s, clients, song])
	connect_thread.daemon = True
	connect_thread.start()

	for chunk in song:
		
		# c.send('Thank you for connecting')
		print(len(chunk.raw_data))
		for client, address in clients:
			client.sendto(chunk.raw_data, address)

		# c.close()                # Close the connection
	connect_thread.join()
	return 0

def accept_connection(sock, clients, song):
	while True:
		c, addr = sock.accept()
		width = song.sample_width
		f_rate = song.frame_rate * 2
		chunk_size = len(song[0])
		data = str(width + "," + f_rate + "," + chunk_size)
		client.sendto(data, addr)

		# Find the song's frame width
		# Find the song's framerate
		# Find the size of each chunk (i.e. len(song[0].raw_data))
		# Send this information to the client
		clients.append((c, addr))

if __name__ == '__main__':
	main(sys.argv)