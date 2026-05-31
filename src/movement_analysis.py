# -*- coding: utf-8 -*-
import serial
import io
import numpy as np
from collections import deque
from scipy import fftpack, signal

f_s = 64
maxlen=256
queue =deque()
# new samples in the buffer
samples_non_overlaped = 64 # maxlen/4


ser = serial.Serial('COM6', 115200, timeout=15)
# now readline stops when encountering a \r char
ser_io = io.TextIOWrapper(io.BufferedRWPair(ser, ser, 1),
                               newline = '\r',
                               line_buffering = True)


def fourier(timestep, data):
    #-----Su código aquí
    
    # Calculo de la FFT
    data_fft = fftpack.fft(data)
    # Array de frecuencias
    freqs = fftpack.fftfreq(len(data), d=timestep)

    # Parte positiva del espectro
    N = len(data)//2
    data_fft = data_fft[:N]

    # Valor absoluto
    amp = np.abs(data_fft)

    # Obtener máximo
    ind = np.argmax(amp)
    k = freqs[ind]
    #------------------
    return k

def dominant(f_s, maxlen, queue):
        freq_rithm = 0
        i = 0
        iterator = maxlen*2
        queue = deque()
        cont = 0
        window = signal.windows.blackman(maxlen)
        while i <= iterator:
            try:
                line = ser_io.readline()
            except serial.SerialException as err:
                print("Error occurred while reading data: {}".format(err))
            if not line.endswith('\r'):
                print("Attempt to read from serial port timed out ... Exiting.")
                break  # terminate the loop and let the program exit
            if line.startswith('S,'):
                i += 1
                line = line.split(',')
                if len(line)==12:
                    number = int(line[2])
                # si cogiésemos accelx
                # number = int(line.split(',')[4])
                if (len(queue) == maxlen):
                    queue.popleft()
                    queue.append(number)
                else:
                    if (len(queue) < maxlen):
                        queue.append(number)
                if len(queue)==maxlen and (i % samples_non_overlaped == 0):
                    # f = fourier(1./f_s, queue)
                    f = fourier(1./f_s, queue * window)
                    freq_rithm = freq_rithm + f
                    cont = cont + 1
        return freq_rithm/cont


def calcula_frec_dom(num_calls):
    try:
        ser.isOpen()
    except:
        print('error_1')
        exit()

    i = 0
    while (i<num_calls):
        if (ser.isOpen()):
                ser.flushInput()
                df = dominant(f_s, maxlen, queue)
                print('La frecuencia dominante es: %.2f Hz'% df)
                i = i+1
        else:
            print('Cannot open serial port')