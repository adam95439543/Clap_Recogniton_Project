import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import genfromtxt, sqrt
import serial
import keyboard
from datetime import datetime
import threading
import os
import psutil

current_system_pid = os.getpid()

MAX_INT = 2**31 - 1
N = 256 
__time__ = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

# set serial port
ser = serial.Serial('COM4', 115200, timeout = 1)
print("start serial")

# initializing plot lines
x = range(0, N)
y = np.arange(300, 500, 200/N)
x_half = range(0, N//2)
y_half = range(0, N, 2) 

# initializing graphs
plt.ion()
fig = plt.figure()
subplot1 = fig.add_subplot(211)
subplot2 = fig.add_subplot(212)
line1, = subplot1.plot(x, y, 'r-')
line2, = subplot2.plot(x_half, y_half, 'r-')

# general variables
volume = []
frequency = []
index = 0
state = False
start_time = datetime.now()

# file open
file_all_volume = open("[All] VOL " + __time__ + ".csv", 'w')
file_all_freq = open("[All] FREQ " + __time__ + ".csv", 'w')
file_label_volume = open("[Label] VOL " + __time__ + ".csv", 'w')
file_label_freq = open("[Label] FREQ " + __time__ + ".csv", 'w')

# keyboard input thread
class KeyboardWorker(threading.Thread):
    
    def run(self):
        global state
        global current_system_pid
        while True:
            key_buf = keyboard.read_key()
            keyboard.read_key() # clear buffer
            if key_buf == 'space':
                if state == True:
                    # file close
                    file_all_volume.close()
                    file_all_freq.close()
                    file_label_volume.close()
                    file_label_freq.close()
                state = not state
            if key_buf == 'esc':       
                ThisSystem = psutil.Process(current_system_pid)
                ThisSystem.terminate() # kill process
            
        

def process_serial_event(volume, frequency):
    ADCH = 0
    ADCL = 0
    volume.clear()
    frequency.clear()

    # combine two bytes into one integer
    for i in range(2 * N):
        buf = ser.read() # buf is an object of 'bytes class'
        buf = int.from_bytes(buf, byteorder='big', signed=False)
        if i % 2 == 0: # Even
            ADCH = buf & 0xFF
        else: # Odd
            ADCL = buf & 0xFF
            ADC = ADCH << 8 | ADCL
            volume.append(ADC)
    
    # get frequency data from Arduino
    for i in range(N // 2):
        buf = ser.read()
        frequency.append(int.from_bytes(buf, byteorder='big', signed=False))

def draw_graph(volume, frequency):
    line1.set_ydata(volume)
    line2.set_ydata(frequency) # fft power is symmetric around 128. So don't need to see [128:255]

    fig.canvas.draw()
    fig.canvas.flush_events()  

def process_data_out(file_all_volume, file_all_freq, volume, frequency, index, milliSeconds):
    if index < MAX_INT:    index += 1
    else:                  index = 0

    data_volume = str(index) + "," + str(milliSeconds) + ","
    data_freq = str(index) + "," + str(milliSeconds) + ","

    for i in range(128):
        data_volume += (str(volume[i]) + ",")
        data_freq += (str(frequency[i]) + ",")
    data_volume += "\n"
    data_freq += "\n"

    file_all_volume.write(data_volume)
    file_all_freq.write(data_freq)

thread = KeyboardWorker()
thread.daemon = True
thread.start() 

while True:
    if ser.readable() & (ser.read() == b'\xFF'): # start_byte = (ser.read() == b'\xFF')
        
        elapsed_time = datetime.now()
        milliSeconds = (elapsed_time - start_time).microseconds * 0.001

        process_serial_event(volume, frequency)
        
        if state:
            process_data_out(file_all_volume, file_all_freq, volume, frequency, index, milliSeconds)

        draw_graph(volume, frequency)

        
            

         
