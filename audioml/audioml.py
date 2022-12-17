"""
    simple_audio.py

    This programs collects audio data from an I2S mic on the Raspberry Pi 
    and runs the TensorFlow Lite interpreter on a per-build model. 


    Author: Mahesh Venkitachalam
    Website: electronut.in

"""

from scipy.io import wavfile
from scipy import signal
import numpy as np
import argparse 
import pyaudio
import wave
import time

from tflite_runtime.interpreter import Interpreter
from multiprocessing import Process, Queue

VERBOSE_DEBUG = False
CHUNK = 4000                # choose a value divisible by SAMPLE_RATE
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000 
RECORD_SECONDS = 1
NCHUNKS = int((SAMPLE_RATE * RECORD_SECONDS) / CHUNK)
ND = 2 * SAMPLE_RATE * RECORD_SECONDS
NDH = ND // 2
# device index of microphone
dev_index = -1

def list_devices():
    """List Pyaudio devices"""
    # initialize pyaudio
    p = pyaudio.PyAudio()
    # get device list
    index = None
    nDevices = p.get_device_count()
    print('\naudioml.py:\nFound the following input devices:')
    for i in range(nDevices):
        deviceInfo = p.get_device_info_by_index(i)
        if deviceInfo['maxInputChannels'] > 0:
            print(deviceInfo['index'], deviceInfo['name'], deviceInfo['defaultSampleRate'])
    # clean up
    p.terminate()

def inference_process(dataq, interpreter):
    """Infererence process handler"""
    success = False
    while True:
        if not dataq.empty():
            # get data from queue
            inference_data = dataq.get()
            # run inference only if previous one was not success
            # otherwise we will get duplicate results because of 
            # overlap in input data 
            if not success:
                success = run_inference(inference_data, interpreter)
            else:
                # skipping, reset flag for next time
                success = False

def process_audio_data(waveform):
    """Process audio input.

    This function takes in raw audio data from a WAV file and does scaling 
    and padding to 16000 length.

    """

    if VERBOSE_DEBUG:
        print("waveform:", waveform.shape, waveform.dtype, type(waveform))
        print(waveform[:5])

    # compute peak to peak based on scaling by max 16 bit value
    PTP = np.ptp(waveform / 32768.0)

    if VERBOSE_DEBUG:
        print("peak-to-peak (16 bit scaling): {}".format(PTP))

    # return None if too silent 
    if PTP < 0.3:
        return []

    # normalize audio
    wabs = np.abs(waveform)
    wmax = np.max(wabs)
    waveform = waveform / wmax

    # compute peak to peak based on normalized waveform
    PTP = np.ptp(waveform)

    if VERBOSE_DEBUG:
        print("peak-to-peak (after normalize): {}".format(PTP))
        print("After normalisation:")
        print("waveform:", waveform.shape, waveform.dtype, type(waveform))
        print(waveform[:5])

    # scale and center
    waveform = 2.0*(waveform - np.min(waveform))/PTP - 1

    # extract 16000 len (1 second) of data   
    max_index = np.argmax(waveform)  
    start_index = max(0, max_index-8000)
    end_index = min(max_index+8000, waveform.shape[0])
    waveform = waveform[start_index:end_index]

    # Padding for files with less than 16000 samples
    if VERBOSE_DEBUG:
        print("After padding:")

    waveform_padded = np.zeros((16000,))
    waveform_padded[:waveform.shape[0]] = waveform

    if VERBOSE_DEBUG:
        print("waveform_padded:", waveform_padded.shape, waveform_padded.dtype, type(waveform_padded))
        print(waveform_padded[:5])

    return waveform_padded

def get_spectrogram(waveform):
    """computes spectrogram from audio data"""
    
    waveform_padded = process_audio_data(waveform)

    if not len(waveform_padded):
        return []

    # compute spectrogram 
    f, t, Zxx = signal.stft(waveform_padded, fs=16000, nperseg=255, 
        noverlap = 124, nfft=256)
    # Output is complex, so take abs value
    spectrogram = np.abs(Zxx)

    if VERBOSE_DEBUG:
        print("spectrogram:", spectrogram.shape, type(spectrogram))
        print(spectrogram[0, 0])
        
    return spectrogram


def run_inference(waveform, interpreter):
    # start timing
    start = time.perf_counter()

    # get spectrogram data 
    spectrogram = get_spectrogram(waveform)

    if not len(spectrogram):
        if VERBOSE_DEBUG:
            print("Too silent. Skipping...")
        return False
    
    if VERBOSE_DEBUG:
        print("spectrogram: %s, %s, %s" % (type(spectrogram), spectrogram.dtype, spectrogram.shape))

    # Get input and output tensors details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    if VERBOSE_DEBUG:
        print("input_details: {}".format(input_details))
        print("output_details: {}".format(output_details))

    # reshape spectrogram to match interperter requirement 
    spectrogram = np.reshape(spectrogram, (-1, spectrogram.shape[0], spectrogram.shape[1], 1))

    # set input
    input_data = spectrogram.astype(np.float32)
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # run interpreter
    print("running inference...")
    interpreter.invoke()

    # get output
    output_data = interpreter.get_tensor(output_details[0]['index'])
    yvals = output_data[0]
    if VERBOSE_DEBUG:
        print(output_data)

    print(yvals)

    # Important! This should exactly match training labels/ids.
    commands = ['up', 'no', 'stop', 'left', 'right', 'go', 'down', 'yes']
    print(">>> " + commands[np.argmax(output_data[0])].upper())

    # stop timing
    end = time.perf_counter()
    print("run_inference: {}s".format(end - start))
    # return sucess
    return True

def get_live_input(interpreter):
    """This function gets live input from the microphone and runs inference on it"""

    # create a queue object
    dataq = Queue()
    # start inference process
    proc = Process(target = inference_process, args=(dataq, interpreter))
    proc.start()

    # initialize pyaudio
    p = pyaudio.PyAudio()

    print('opening stream...')
    stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = SAMPLE_RATE,
                    input = True,
                    frames_per_buffer = CHUNK,
                    input_device_index = dev_index)

    # discard first 1 second
    for i in range(0, NCHUNKS):
        data = stream.read(CHUNK, exception_on_overflow = False)

    # count for gathering two frames at a time
    count = 0
    inference_data = np.zeros((ND,), dtype=np.int16)
    print("Listening...")
    try:
        while True:
            #print("Listening...")

            chunks = []
            for i in range(0, NCHUNKS):
                data = stream.read(CHUNK, exception_on_overflow = False)
                chunks.append(data)

            # process data
            buffer = b''.join(chunks)
            audio_data = np.frombuffer(buffer, dtype=np.int16)

            if count == 0:
                # set first half 
                inference_data[:NDH] = audio_data
                count += 1
            elif count == 1:
                # set second half 
                inference_data[NDH:] = audio_data
                # add data to queue
                dataq.put(inference_data)
                count += 1
            else:
                # move second half to first half
                inference_data[:NDH] = inference_data[NDH:]
                # set second half
                inference_data[NDH:] = audio_data
                # add data to queue
                dataq.put(inference_data)
            
            #print("queue: {}".format(dataq.qsize()))
            
    except KeyboardInterrupt:
        print("exiting...")
           
    stream.stop_stream()
    stream.close()
    p.terminate()


def main():
    """main function for the program."""
    # globals set in this function
    global VERBOSE_DEBUG
    # create parser
    descStr = "This program does ML inference on audio data."
    parser = argparse.ArgumentParser(description=descStr)
    # add a mutually exclusiv egroup
    group = parser.add_mutually_exclusive_group(required=True)
    # add mutually exclusive arguments
    group.add_argument('--list', action='store_true', required=False)
    group.add_argument('--input', dest='wavfile_name', required=False)
    group.add_argument('--index', dest='index', required=False)    
    # add other arguments
    parser.add_argument('--verbose', action='store_true', required=False)

    # parse args
    args = parser.parse_args()

    # load TF Lite model
    interpreter = Interpreter('audioml.tflite')
    interpreter.allocate_tensors()
    
    # check verbose flag
    if args.verbose:
        VERBOSE_DEBUG = True

    # test WAV file
    if args.wavfile_name:
        wavfile_name = args.wavfile_name
        # get audio data 
        rate, waveform = wavfile.read(wavfile_name)
        # run inference
        run_inference(waveform, interpreter)
    elif args.list:
        # list devices
        list_devices()
    else:
        # store device index 
        dev_index = int(args.index)
        # get live audio
        get_live_input(interpreter)

    print("done.")

# main method
if __name__ == '__main__':
    main()
