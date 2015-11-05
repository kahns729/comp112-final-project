import socket, sys

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
	print s.recv(1024)
	s.close                     # Close the socket when done

if __name__ == '__main__':
	main(sys.argv)