import matplotlib.pyplot as plt
import numpy as np
import time

# please select All or Label
select_All = False    # All 파일을 읽어올려면 True 를 입력해주세용
__name__ = "[All]" if select_All else "[Label]"

# please set time
__time__ = "2021-07-18 08-07-08"    # 파일의 날짜와 시간을 입력해주세용

#----------------------------------------------------------------------------------------------------------------------
# file open
file_volume = open(__name__ + " VOL " + __time__ + ".csv", 'r')
file_freq = open(__name__ + " FREQ " + __time__ + ".csv", 'r')

# constants
MAX_INT = 2**31 - 1
FFT_N = 256 
delay_time = 0.084 # delay time을 수정하여 좀 더 천천히 읽어들이거나, 빨리 읽어들일 수 있음. 0.084 s 일때 실제와 가장 비슷

# initializing plot lines
x = range(0, FFT_N)
y = np.arange(300, 500, 200/FFT_N)
x_half = range(0, FFT_N//2)
y_half = range(0, FFT_N, 2) 

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

#----------------------------------------------------------------------------------------------------------------------
# detection code variables
T = 0
mean = 0
sd = 1
standard_score =  [0 for i in range(FFT_N // 2)]
N = 0
sound_detected = False
detected_clock_count = 0

# get average of array
def AVR(arr, powered_avg = False):
    sum = 0
    if powered_avg :
        for i in arr :
            sum += (i * i)
    else :
        for i in arr:
            sum += i
    return sum / len(arr)

# get number of elements bigger than the cut off
def COUNT(arr, cutOff = -1):
    cnt = 0
    for i in arr:
        if i > cutOff: cnt += 1
    return cnt

def detection_code(fft_log_out):
    global T, mean, sd, standard_score, N
    global sound_detected, detected_clock_count
    clap_detected = False

    if T % 10: # 85 ms * 11 = 935 ms. while루프가 한 번 도는데 85 ms 걸리므로 11번 카운트하면 대충 1000 ms 가 된다.
        mean = AVR(fft_log_out)
        sd = np.sqrt(AVR(fft_log_out, True) - mean * mean)
        T = 0
    T += 1
    
    for i in range(len(fft_log_out)):
        standard_score[i] = (fft_log_out[i] - mean)/sd * 10 + 50

    '''
    # 저주파 범위의 주파수들은 기본적으로 큰 값을 갖음 -> 애네가 평균을 dominant 하게 잡아먹음
    # 조용한 상태에서 cut off 보다 큰 표준 점수 값을 갖는 저주파 주파수들이 default로 2~3개 정도 존재함
    # 그래서 아래 라인에서 논문과는 다르게 N은 3이하로 잡아줬다.
    # cut off도 논문처럼 70이면 저주파 주파수의 표준점수만 cuf off를 넘길래
      일부러 65 정도로 낮춰서 고주파 주파수의 표준점수들도 cut off를 쉽게 넘길 수 있도록 하였음.

    # 만약 시끄러운 상태라면 디폴트 저주파의 표준 점수 값이 작아질지도? (추측임)
    '''
    if N <= 3:
        N = COUNT(standard_score, cutOff=65)
        if not sound_detected and N > 3:
            sound_detected = True
    else:
        N = COUNT(standard_score, cutOff=65)

    # print(f'N is {N}')
    # print(f'sound detected : {sound_detected}')

    if sound_detected and N > 3:
        detected_clock_count += 1
    elif sound_detected: #and N == 0:
        sound_detected = False
        if detected_clock_count <= 1:
            clap_detected = True
        detected_clock_count = 0

    return clap_detected
#----------------------------------------------------------------------------------------------------------------------

# global variables
count = 0

while True:
    data_volume = file_volume.readline()
    data_freq = file_freq.readline()

    if not data_volume or not data_freq: break # readline() returns ""(empty string) when there are no lines to read

    if data_volume == '\n' and data_freq == '\n':
        count += 1
        print(f'{count}th captured data')        
        continue

    index = int(data_volume.split(',')[0]) if data_volume.split(',')[0] == data_freq.split(',')[0] else False
    current_time = float(data_volume.split(',')[1]) if data_volume.split(',')[1] == data_freq.split(',')[1] else False

    if not index or not current_time: print("volume file and freq file are different")
    
    volume = [int(data) for data in data_volume.split(',')[2:-1]] # 256 elements
    frequency = [int(data) for data in data_freq.split(',')[2:-1]] # 128 elements

    draw_graph(volume, frequency)

    time.sleep(delay_time)

    if detection_code(frequency): 
        print(f'{count}th clap detected!!   [Index : {index}, Time : {current_time}]')


