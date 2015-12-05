# Comp 112 Final Project -- P2P Music Stream

## Overview
We have implemented an application that streams mp3 files to multiple clients. The server grabs music files out of a static directory, and streams to clients. Clients may view songs available on the server, request songs to be played from the server, or view previous song requests.

## Installation
Both the server and client for the application are written in Python 3, which can be [installed here](https://www.python.org/downloads/). We use a few Python packages, most notably [pydub](https://github.com/jiaaro/pydub). Importantly, you must install ffmpeg in order to use the client and/or server. [Here](https://github.com/adaptlearning/adapt_authoring/wiki/Installing-FFmpeg) is a good place to find how to download ffmpeg for your operating system.

When you have Python 3, you must install the required dependencies, which can be found in the `requirements.txt` file. We recommend using a virtual environment, though it is not strictly necessary. To install the requirements, run `pip3 install -r requirements.txt`.

## Use
### Server
A directory in a level above the directory the server is running from called “songs” must exist (../songs) with at least 1 .mp3 file in it in order for the program to run.
To run the server, use:
`python3 server.py [port]`

### Client
To run the client, use:
`python3 client.py [server_hostname] [server_port]`

## User Interface
While the server has no user interface, the client has a number of requests that can be made to the server. To request a list of songs, simply type `SONGS`. To view the queue of songs that have been requested, type `REQUESTS`. Songs closer to the top of this list will be played earlier than songs later in the list (first come, first served). To request a song, type `PLAY` followed by the index of the song in the numbered song list (the list received when you request `SONGS`).
