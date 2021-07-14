import matplotlib.pyplot as plt
import numpy as np
import time

# please select All or Label
select_All = False    # All 파일을 읽어올려면 True 를 입력해주세용
__name__ = "[All]" if select_All else "[Label]"

# please set time
__time__ = "2021-07-14 18-20-00"    # 파일의 날짜와 시간을 입력해주세용

# file open
file_volume = open(__name__ + " VOL " + __time__ + ".csv", 'r')
file_freq = open(__name__ + " FREQ " + __time__ + ".csv", 'r')

# constants
MAX_INT = 2**31 - 1
N = 256 
delay_time = 0.084 # delay time을 수정하여 좀 더 천천히 읽어들이거나, 빨리 읽어들일 수 있음. 0.084 s 일때 실제와 가장 비슷

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

def draw_graph(volume, frequency):
    line1.set_ydata(volume)
    line2.set_ydata(frequency)

    fig.canvas.draw()
    fig.canvas.flush_events() 

def detection_code(volume, frequency, current_time):
    return False

# global variables
count = 0

while True:
    data_volume = file_volume.readline()
    data_freq = file_freq.readline()

    if not data_volume or not data_freq: break # readline() returns ""(empty string) when there are no lines to read

    if data_volume == '\n' and data_freq == '\n':
        print(f'{count}th captured data')
        count += 1
        continue

    index = int(data_volume.split(',')[0]) if data_volume.split(',')[0] == data_freq.split(',')[0] else False
    current_time = float(data_volume.split(',')[1]) if data_volume.split(',')[1] == data_freq.split(',')[1] else False

    if not index or not current_time: print("volume file and freq file are different")
    
    volume = [int(data) for data in data_volume.split(',')[2:-1]] # 256 elements
    frequency = [int(data) for data in data_freq.split(',')[2:-1]] # 128 elements

    draw_graph(volume, frequency)

    time.sleep(delay_time)

    if detection_code(volume, frequency, current_time): False