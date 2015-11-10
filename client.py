import socket, sys
import pyaudio

def main(argv):
	s = socket.socket()         # Create a socket object
	# host = socket.gethostname() # Get local machine name
	# Expecting 3 arguments: client.py, the host, and the port
	if len(argv) < 3:
		print("usage: python client.py [host] [port]")
		return 1
	host = argv[1]
	# port = 12345                # Reserve a port for your service.
	port = int(argv[2])

	s.connect((host, port))
	# Retrieve the information from the server, and replace the hard coded sections below

	# instantiate PyAudio (1)
	p = pyaudio.PyAudio()

	# open stream (2)
	stream = p.open(format=p.get_format_from_width(2), # Hard coded
					channels=1,
	                rate=88200, # Hard coded
	                output=True)
	# print s.recv(1024)
	while True:
		chunk, addr = s.recvfrom(176) # Hard coded
		stream.write(chunk)
	s.close                     # Close the socket when done

if __name__ == '__main__':
	main(sys.argv)