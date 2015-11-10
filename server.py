import socket, sys, os
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

	c, addr = s.accept()     # Establish connection with client.
	for chunk in song:
		
		print(addr)
		# c.send('Thank you for connecting')
		print(len(chunk.raw_data))
		c.sendto(chunk.raw_data, addr)

		# c.close()                # Close the connection
	return 0

if __name__ == '__main__':
	main(sys.argv)