"""
karplus_pico.py

Uses the Karplus String algorithm to generate musical notes in a pentatonic scale.
Runs on a Raspberry Pico. (MicroPython)

Author: Mahesh Venkitachalam
"""

import time
import array
import random
import os

from machine import I2S
from machine import Pin

# notes of a Pentatonic Minor scale
# piano C4-E(b)-F-G-B(b)-C5
pmNotes = {'C4': 262, 'Eb': 311, 'F': 349, 'G':391, 'Bb':466}

# button to note mapping
btnNotes = {0: ('C4', 262), 1: ('Eb', 311), 2: ('F', 349), 3: ('G', 391), 4: ('Bb', 466)}

# sample rate
SR = 16000

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

# generate note of given frequency
# @timed_function 
def generate_note(freq):
    nSamples = SR
    N = int(SR/freq)
    # initialize ring buffer
    buf = [2*random.random() - 1 for i in range(N)]

    # init sample buffer
    samples = array.array('h', [0]*nSamples)
    for i in range(nSamples):
        samples[i] = int(buf[0] * (2 ** 15 - 1))
        avg = 0.4975*(buf[0] + buf[1])
        buf.append(avg)
        buf.pop(0)

    return samples 

# generate note of given frequency - improved method
def generate_note2(freq):
    nSamples = SR
    sampleRate = SR
    N = int(sampleRate/freq)
    # initialize ring buffer
    buf = [2*random.random() - 1 for i in range(N)]

    # init sample buffer
    samples = array.array('h', [0]*nSamples)
    start = 0
    for i in range(nSamples):
        samples[i] = int(buf[start] * (2**15 - 1))
        avg = 0.4975*(buf[start] + buf[(start + 1) % N])
        buf[(start + N) % N] = avg
        start = (start + 1) % N

    return samples 

def play_note(note, audio_out):
    "Read note from file and send via I2S"
    fname = note[0] + ".bin"

    # open file
    try:
        print("opening {}...".format(fname)) 
        file_samples = open(fname, "rb")
    except:
        print("Error opening file: {}!".format(fname))
        return

    # allocate sample array
    samples = bytearray(1000)
    # memoryview used to reduce heap allocation
    samples_mv = memoryview(samples)

    # read samples and send tp I2S
    try:
        while True:
            num_read = file_samples.readinto(samples_mv)
            # end of file?
            if num_read == 0:
                break
            else:
                # send samples via I2S
                num_written = audio_out.write(samples_mv[:num_read])
    except (Exception) as e:
        print("Exception: {}".format(e))
    
    # close file
    file_samples.close()

def create_notes():
    "Create pentatonic notes and save to files in flash."
    files = os.listdir()
    for (k, v) in pmNotes.items():
        # set note file name 
        file_name = k + ".bin"
        # check if file already exists 
        # 
        if file_name in files:
            print("Found " + file_name + ". Skipping...")
            continue
        # generate note 
        print("Generating note " + k + "...")
        samples = generate_note(v)    
        # write to file 
        print("Writing " + file_name + "...")
        file_samples = open(file_name, "wb")
        file_samples.write(samples)
        file_samples.close()


def main():

    # set up LED 
    led = Pin(25, Pin.OUT)
    # turn on LED 
    led.toggle()

    # create notes and save in flash 
    create_notes()

    # create I2S object
    audio_out = I2S(
        0,                  # I2S ID
        sck=Pin(0),         # SCK Pin 
        ws=Pin(1),          # WS Pin 
        sd=Pin(2),          # SD Pin
        mode=I2S.TX,        # I2S transmitter
        bits=16,            # 16 bits per sample
        format=I2S.MONO,    # Mino - single channel
        rate=SR,            # sample rate 
        ibuf=2000,          # I2S buffer length 
    )

    # set up btns     
    btns = [Pin(3, Pin.IN, Pin.PULL_UP), 
            Pin(4, Pin.IN, Pin.PULL_UP),
            Pin(5, Pin.IN, Pin.PULL_UP),
            Pin(6, Pin.IN, Pin.PULL_UP),
            Pin(7, Pin.IN, Pin.PULL_UP)]

    # "ready" note 
    play_note(('C4', 262), audio_out)
    print("Piano ready!")

    # turn off LED 
    led.toggle()

    while True:
        for i in range(5):
            if btns[i].value() == 0:
                play_note(btnNotes[i], audio_out)
                break
        time.sleep(0.2)

# call main
if __name__ == '__main__':
    main()


