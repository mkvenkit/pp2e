"""

laser_audio.py


Author: Mahesh Venkitachalam

"""

import RPi.GPIO as GPIO
import time
import argparse
import pyaudio
import wave
import numpy as np


# define pin numbers 
# uses TB6612FNG motor driver pin naming 
PWMA = 12
PWMB = 13
AIN1 = 7
AIN2 = 8
BIN1 = 5
BIN2 = 6
STBY = 22
LASER = 25

# global PWM objects
pwm_a = None
pwm_b = None

# size of audio data read in 
CHUNK = 2048
# FFT size
N = CHUNK

def init_pins():
    """set up pins"""
    global pwm_a, pwm_b

    # use BCM pin numbering 
    GPIO.setmode(GPIO.BCM)

    # put pins into a list 
    pins = [PWMA, PWMB, AIN1, AIN2, BIN1, BIN2, STBY, LASER]   

    # set up pins as outputs 
    GPIO.setup(pins, GPIO.OUT)

    # set PWM
    pwm_a = GPIO.PWM(PWMA, 100)
    pwm_b = GPIO.PWM(PWMB, 100)

def laser_on(on):
    """Turn laser MOSFET on/off"""
    # pin 25 controls laser ctrl mosfet
    GPIO.output(LASER, on)


def test_motors():
    """Test motors by manually setting speed and direction"""
    # turn laser on
    laser_on(True)

    # start motors
    start_motors()

    # read user input
    try:
        while True:
            print("Enter dca dcb dira dirb (eg. 50 100 1 0):")
            # read input 
            str_in = input()
            # parse values
            vals = [int(val) for val in str_in.split()]
            # sanity check
            if len(vals) == 4:
                set_motor_speed_dir(vals[0], vals[1], vals[2], vals[3]) 
            else:
                print("Input error!")
    except:
        print("Exiting motor test!")
    finally:    
        # stop motors
        stop_motors()
        # turn laser off
        laser_on(False)


def test_motors1():

    # laser on 
    laser_on(True)

    # enable driver chip
    GPIO.output(STBY, GPIO.HIGH)

    # set motor direction for channel A
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    # set motor direction for channel B
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)

    # set PWM for channel A
    freq = 100
    duty_cycle = 30
    pwm_a.start(duty_cycle)
    time.sleep(2.0)
    pwm_a.stop()

    # brake A
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.HIGH)

    # set PWM for channel B
    freq = 100
    duty_cycle = 30
    pwm_b.start(duty_cycle)
    time.sleep(2.0)
    pwm_b.stop()

    # brake B
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.HIGH)

    # disable driver chip
    GPIO.output(STBY, GPIO.LOW)

    # laser on 
    laser_on(False)

def start_motors():
    """Start both motors"""
    # enable driver chip
    GPIO.output(STBY, GPIO.HIGH)
    # set motor direction for channel A
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    # set motor direction for channel B
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    # set PWM for channel A
    duty_cycle = 0
    pwm_a.start(duty_cycle)
    # set PWM for channel B
    pwm_b.start(duty_cycle)

def stop_motors():
    """Stop both motors"""
    # stop PWM
    pwm_a.stop()
    pwm_b.stop()
    # brake A
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.HIGH)
    # brake B
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.HIGH)
    # disable driver chip
    GPIO.output(STBY, GPIO.LOW)

def set_motor_speed_dir(dca, dcb, dira, dirb):
    """Set speed and directon of motors."""
    # set duty cycle
    pwm_a.ChangeDutyCycle(dca)
    pwm_b.ChangeDutyCycle(dcb)
    # set direction A
    if dira:
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
    else:
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)
    if dirb:
        GPIO.output(BIN1, GPIO.HIGH)
        GPIO.output(BIN2, GPIO.LOW)
    else:
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH)
        
def process_audio(filename):
    """Reads WAV file, does FFT and controls motors"""
    
    print("opening {}...".format(filename))

    # open WAV file
    wf = wave.open(filename, 'rb')
    
    # print audio details 
    print("SW = {}, NCh = {}, SR = {}".format(wf.getsampwidth(), 
        wf.getnchannels(), wf.getframerate()))
    
    # check for supported format
    if wf.getsampwidth() != 2 or wf.getnchannels() != 1:
        print("Only single channel 16 bit WAV files are supported!")
        wf.close()
        return

    # create PyAudio object
    p = pyaudio.PyAudio()

    # open an output stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # read first frame
    data = wf.readframes(CHUNK)
    buf = np.frombuffer(data, dtype=np.int16)

    # store sample rate
    SR = wf.getframerate()

    # start motors
    start_motors()

    # laser on 
    laser_on(True)

    # read audio data from WAV file 
    try:
        # loop till there is no data to be read
        while len(data) > 0:
            # write stream to output
            stream.write(data)
            # ensure enough samples for FFT
            if len(buf) == N:  
                buf = np.frombuffer(data, dtype=np.int16)
                # do FFT 
                fft = np.fft.rfft(buf)
                fft = np.abs(fft) * 2.0/N
                # calc levels
                # get average of 3 frequency bands
                # 0-100 Hz, 100-1000 Hz and 1000-2500 Hz
                levels = [np.sum(fft[0:100])/100,
                            np.sum(fft[100:1000])/900,
                            np.sum(fft[1000:2500])/1500]
                # speed1
                dca = int(5*levels[0]) % 60
                # speed2
                dcb = int(100 + levels[1]) % 60
                # dir
                dira = False
                dirb = True
                if levels[2] > 0.1:
                    dira = True
                # set motor direction and speed
                set_motor_speed_dir(dca, dcb, dira, dirb)
            # read next 
            data = wf.readframes(CHUNK)

    except BaseException as err:
        print("Unexpected {}, type={}".format(err, type(err)))

    finally:
            print("Finally: Pyaudio clean up...")
            stream.stop_stream()
            stream.close()
            # stop motors
            stop_motors()
            # close WAV file
            wf.close()


def main():
    """main calling function"""

    # setup args parser
    parser = argparse.ArgumentParser(description="A laser audio display.")
    # add arguments
    parser.add_argument('--test_laser', action='store_true', required=False)
    parser.add_argument('--test_motors', action='store_true', required=False)
    parser.add_argument('--wav_file', dest='wav_file', required=False)
    args = parser.parse_args()

    # initialize pins
    init_pins()

    # main loop 
    try:    
        if args.test_laser:
            print("laser on...")
            laser_on(True)
            while True:
                time.sleep(1)
        elif args.test_motors:
            print("testing motors...")
            test_motors()
        elif args.wav_file:
            print("starting laser audio display...")
            process_audio(args.wav_file)
    except (Exception) as e:
        print("Exception: {}".format(e))
        print("Exiting.")

    # turn laser off
    laser_on(False)

    # call at the end 
    GPIO.cleanup()
    print("Done.")


# call main
if __name__ == '__main__':
    main()
