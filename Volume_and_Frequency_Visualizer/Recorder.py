'''
# press 'space' to start record
# press 'enter' to capture the data
# press 'esc' to stop program
'''
import matplotlib.pyplot as plt
import numpy as np
import serial
import keyboard
from datetime import datetime
import threading
import os
import psutil

current_system_pid = os.getpid()

# constants
MAX_INT = 2**31 - 1
N = 256 
__time__ = datetime.now().strftime('%Y-%m-%d %H-%M-%S') # set in file's name

# set serial port
ser = serial.Serial('COM4', 115200, timeout = 1) # change to your computer's port name
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
state = False
capture = False
volume = []
frequency = []
volume_queue = []
frequency_queue = []

# file open
file_all_volume = open("[All] VOL " + __time__ + ".csv", 'w')
file_all_freq = open("[All] FREQ " + __time__ + ".csv", 'w')
file_label_volume = open("[Label] VOL " + __time__ + ".csv", 'w')
file_label_freq = open("[Label] FREQ " + __time__ + ".csv", 'w')

# keyboard input thread
class KeyboardWorker(threading.Thread):
    
    def run(self):
        global state
        global capture
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

            if key_buf == 'enter':
                if state == True and capture == False:
                    file_label_volume.write('\n')
                    file_label_freq.write('\n') 
                   
                    # write past data in file_label
                    for data_volume in volume_queue:
                        file_label_volume.write(data_volume)
                    
                    for data_freq in frequency_queue:
                        file_label_freq.write(data_freq)        

                    capture = True # start capture incoming data

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
    line2.set_ydata(frequency)

    fig.canvas.draw()
    fig.canvas.flush_events()  

class DataProcess:
    index = 0
    capture_count = 0

    def count_index(self):
        if DataProcess.index < MAX_INT:    DataProcess.index += 1
        else:                              DataProcess.index = 0

    def process_data_out(self, file_volume, file_freq, volume, frequency, current_time):
        self.data_volume = str(DataProcess.index) + "," + str(current_time) + ","
        self.data_freq = str(DataProcess.index) + "," + str(current_time) + ","

        for i in range(128):
            self.data_volume += (str(volume[i]) + ",")
            self.data_freq += (str(frequency[i]) + ",")
        self.data_volume += "\n"
        self.data_freq += "\n"
        
        file_volume.write(self.data_volume)
        file_freq.write(self.data_freq)

    def data_enqueue(self):
        '''
        # 한번 시리얼 input을 받은 직후부터, 다음 시리얼 input을 받을 때까지의 평균 시간 간격 : 85 ms
        # 0.5 초 동안 받는 시리얼 input의 평균 개수 : 500 ms / 85 ms = 6 개 (5.88 개)
        # 따라서 6개의 데이터들을 볼륨, 프리퀀시 큐에 담아두었다가 
        엔터 입력 시 라벨 파일에 우선 기록 한 후, 그 후로 들어오는 6개의 데이터를 추가로 기록한다.
        
        따라서 총 12개 (약 1.1초)의 데이터를 캡쳐하여 라벨 파일에 기록한다
        '''
        # insert to queue
        volume_queue.append(self.data_volume)
        frequency_queue.append(self.data_freq)

        # set queue size to 6
        if len(volume_queue) > 6:
            volume_queue.pop(0)
            frequency_queue.pop(0)
    
    def capture_counter(self):
        global capture

        if DataProcess.capture_count < 5: # capture_count starts from 0
            DataProcess.capture_count += 1
        elif DataProcess.capture_count == 5: # when capture_count == 5, there are 6 data rows
            DataProcess.capture_count = 0
            capture = False

data = DataProcess()
thread = KeyboardWorker()
thread.daemon = True
thread.start() 
start_time = datetime.now()

while True:
    if ser.readable() & (ser.read() == b'\xFF'): # start_byte = (ser.read() == b'\xFF')
        
        elapsed_time = datetime.now()
        milliSeconds = (elapsed_time - start_time).microseconds * 0.001
        current_time = (elapsed_time - start_time).seconds + milliSeconds * 0.001

        process_serial_event(volume, frequency)
        
        if state:
            data.count_index()
            data.process_data_out(file_all_volume, file_all_freq, volume, frequency, current_time)
            data.data_enqueue()

        if capture:
            data.process_data_out(file_label_volume, file_label_freq, volume, frequency, current_time)
            data.capture_counter()

        draw_graph(volume, frequency)

        
            

         
