from pydub import AudioSegment, playback
import pyaudio

song = AudioSegment.from_mp3("../audio/allstar.mp3")

first_ten_seconds = song[0:10000]

# instantiate PyAudio (1)
p = pyaudio.PyAudio()

print("width: " + str(song.sample_width))
print("frame_rate: " + str(song.frame_rate))


# open stream (2)
stream = p.open(format=p.get_format_from_width(song.sample_width),
				channels=1,
                rate=song.frame_rate*2,
                output=True)

for chunk in song:
	stream.write(chunk.raw_data)