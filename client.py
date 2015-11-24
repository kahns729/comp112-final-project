import socket, sys
import pyaudio
from stream_client import StreamClient

def main(argv):

	# Expecting 3 arguments: client.py, the host, and the port
	if len(argv) < 3:
		print("usage: python client.py [host] [port]")
		return 1
	host = argv[1]
	port = int(argv[2])
	streamClient = StreamClient(host, port)
	streamClient.start()

if __name__ == '__main__':
	main(sys.argv)