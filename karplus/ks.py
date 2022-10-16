"""
ks.py

Uses the Karplus String algorithm to generate musical notes 
in a pentatonic scale.

Author: Mahesh Venkitachalam
"""

import sys, os
import time, random 
import wave, argparse 
import numpy as np
from collections import deque
import matplotlib
# to fix graph display issues on OS X
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import pyaudio

# show plot of algorithm in action?
gShowPlot = False

# notes of a Pentatonic Minor scale
# piano C4-E(b)-F-G-B(b)-C5
pmNotes = {'C4': 262, 'Eb': 311, 'F': 349, 'G':391, 'Bb':466}

CHUNK = 1024

# initialize plotting 
fig, ax = plt.subplots(1)
line, = ax.plot([], [])

# write out WAVE file
def writeWAVE(fname, data):
    """Write data to WAV file."""
    # open file 
    file = wave.open(fname, 'wb')
    # WAV file parameters 
    nChannels = 1
    sampleWidth = 2
    frameRate = 44100
    nFrames = 44100
    # set parameters
    file.setparams((nChannels, sampleWidth, frameRate, nFrames,
                    'NONE', 'noncompressed'))
    file.writeframes(data)
    file.close()

def generateNote(freq):
    """Generate note using Karplus-Strong algorithm."""
    nSamples = 44100
    sampleRate = 44100
    N = int(sampleRate/freq)
    
    if gShowPlot:
        # set axis
        ax.set_xlim([0, N])
        ax.set_ylim([-1.0, 1.0])
        line.set_xdata(np.arange(0, N))
    
    # initialize ring buffer
    buf = deque([random.random() - 0.5 for i in range(N)], maxlen=N)       
    # init sample buffer
    samples = np.array([0]*nSamples, 'float32')
    for i in range(nSamples):
        samples[i] = buf[0]
        avg = 0.995*0.5*(buf[0] + buf[1])
        buf.append(avg)
        # plot of flag set 
        if gShowPlot:
            if i % 1000 == 0:
                line.set_ydata(buf)
                fig.canvas.draw()
                fig.canvas.flush_events()
      
    # samples to 16-bit to string
    # max value is 32767 for 16-bit
    samples = np.array(samples * 32767, 'int16')
    return samples.tobytes()

# play a wav file
class NotePlayer:
    # constr
    def __init__(self):
        # init pyaudio
        self.pa = pyaudio.PyAudio()
        # open stream 
        self.stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True)            
        # dictionary of notes
        self.notes = []
    def __del__(self):
        # destructor
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    # add a note
    def add(self, fileName):
        self.notes.append(fileName)
    # play a note
    def play(self, fileName):
        try:
            print("playing " + fileName)
            # open wave file
            wf = wave.open(fileName, 'rb')
            # read a chunk
            data = wf.readframes(CHUNK)
            # read rest 
            while data != b'':
                self.stream.write(data)
                data = wf.readframes(CHUNK)
            # clean up
            wf.close()
        except BaseException as err:
            print(f"Exception! {err=}, {type(err)=}.\nExiting.")
            exit(0)

    def playRandom(self):
        """play a random note"""
        index = random.randint(0, len(self.notes)-1)
        note = self.notes[index]
        self.play(note)

# main() function
def main():
    # declare global var
    global gShowPlot

    parser = argparse.ArgumentParser(description="Generating sounds with Karplus-Strong Algorithm.")
    # add arguments
    parser.add_argument('--display', action='store_true', required=False)
    parser.add_argument('--play', action='store_true', required=False)
    args = parser.parse_args()

    # show plot if flag set
    if args.display:
        gShowPlot = True
        #plt.ion()
        plt.show(block=False)

    # create note player
    nplayer = NotePlayer()

    print('creating notes...')
    for name, freq in list(pmNotes.items()):
        fileName = name + '.wav' 
        if not os.path.exists(fileName) or args.display:
            data = generateNote(freq) 
            print('creating ' + fileName + '...')
            writeWAVE(fileName, data) 
        else:
            print('fileName already created. skipping...')
        
        # add note to player
        nplayer.add(name + '.wav')
        
        # play note if display flag set
        if args.display:
            nplayer.play(name + '.wav')
            time.sleep(0.5)
    
    # play a random tune
    if args.play:
        while True:
            try: 
                nplayer.playRandom()
                # rest - 1 to 8 beats
                rest = np.random.choice([1, 2, 4, 8], 1, 
                                        p=[0.15, 0.7, 0.1, 0.05])
                time.sleep(0.25*rest[0])
            except KeyboardInterrupt:
                exit()
  
# call main
if __name__ == '__main__':
    main()
