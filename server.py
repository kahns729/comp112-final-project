import socket, sys, os, threading, random
from stream import Stream
from time import sleep
from pydub import AudioSegment
import pyaudio

def main(argv):
	if len(argv) < 2:
		print("usage: python server.py [port]")
		return 1
	port = int(argv[1])
	stream = Stream(port)
	stream.accept_incoming_connections()
	stream.start()

if __name__ == '__main__':
	main(sys.argv)