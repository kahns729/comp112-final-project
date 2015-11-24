import socket, sys
import pyaudio
import threading
from stream_client import StreamClient

def main(argv):

	# Expecting 3 arguments: client.py, the host, and the port
	if len(argv) < 3:
		print("usage: python client.py [host] [port]")
		return 1
	host = argv[1]
	port = int(argv[2])
	streamClient = StreamClient(host, port)
	streaming_thread = threading.Thread(target=streamClient.start, 
								args=[])
	streaming_thread.daemon = True
	streaming_thread.start()
	print("Welcome to Generic Music Stream!")
	print("To see a list of songs on the server, type 'SONGS'")
	print("To see the queue of songs waiting to be played, type 'REQUESTS'")
	print("To request a song, type 'PLAY [songname]'")
	cmd = input("")
	while cmd != "END":
		if cmd == "SONGS":
			print("TRYING TO GET SONGSSSSS")
			# SONGLIST
			streamClient.request_songlist()
		elif cmd == "REQUESTS":
			# REQUESTLIST
			streamClient.request_queue()
		elif "PLAY" in cmd:
			# PLAY,songname
			streamClient.request_song(cmd[5:])
		cmd = input("")
	streamClient.stop()
	streaming_thread.join()

if __name__ == '__main__':
	main(sys.argv)