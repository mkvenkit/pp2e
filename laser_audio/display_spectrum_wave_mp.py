"""

Play a wavefile and show the waveform and spectrum in real-time.


Author: Mahesh Venkitachalam

"""

import pyaudio
import wave
import sys
import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Process, Queue

CHUNK = 2048
N = CHUNK

def plot_process(dataq):
    freqs = []
    fft = []

    fig, (ax1, ax2) = plt.subplots(2, figsize=(10, 5))

    #x = np.arange(0, N, 0.01)
    ax1.set_xlim([0, N])
    ax1.set_ylim([-32800, 32800])
    ax2.set_xlim([0.1, 5000])
    ax2.set_ylim([0.1, 5000])
    
    #plt.yscale('log')
    plt.xscale('log')

    # fill initial values 
    x = np.arange(0, N)

    line, = ax1.plot(x, x)
    line_fft, = ax2.plot([], [])

    # show plot but don't block 
    plt.show(block=False)

    while True:
        if not dataq.empty():
            buf, freqs, fft = dataq.get()
            # set value 
            line.set_ydata(buf)
            # set FFT value 
            line_fft.set_data(freqs, fft)
            # update
            fig.canvas.draw()
            fig.canvas.flush_events()

def main():

    if len(sys.argv) < 2:
        print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
        sys.exit(-1)

    filename = sys.argv[1]

    # create plot process
    dataq = Queue()
    proc = Process(target = plot_process, args=(dataq,))
    proc.start()

    wf = wave.open(filename, 'rb')

    # print audio details 
    print("SW = {}, NCh = {}, SR = {}".format(wf.getsampwidth(), 
        wf.getnchannels(), wf.getframerate()))

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)
    data_type = np.int16
    buf = np.frombuffer(data, dtype=data_type)

    SR = wf.getframerate()

    frame = 0
    try:
        while data != '':
            stream.write(data)
            if len(buf) == N:  
                buf = np.frombuffer(data, dtype=data_type)
                # do FFT 
                fft = np.fft.rfft(buf)
                fft = np.abs(fft) * 2.0/N
                freqs = np.fft.rfftfreq(N, 1./SR)
                dataq.put((buf, freqs, fft))
            # read next 
            data = wf.readframes(CHUNK)
            frame += 1

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")

    finally:
        print("Finally: Pyaudio process exiting...")
        stream.stop_stream()
        stream.close()
    
    print("plot exiting!")
    proc.join()
    proc.terminate()
    proc.close()

# call main
if __name__ == '__main__':
    main()
