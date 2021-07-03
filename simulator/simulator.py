import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import fftpack
from numpy import genfromtxt

detection = [1,2,3]
answer = []
time_step = 0.02
period = 5.

def one_step(x,fig,time_vec,line1,line2):
     np.random.seed(x)
     
     sig = (np.sin(2 * np.pi / period * time_vec) + 0.5 * np.random.randn(time_vec.size))
     line1.set_ydata(sig)
          
     #FFT의 Power를 계산합니다.
     # The FFT of the signal
     sig_fft = fftpack.fft(sig)

     # And the power (sig_fft is of complex dtype)
     power = np.abs(sig_fft)

     if detecting_algorithm():
         detection.append(x)


     line2.set_ydata(power)

     fig.canvas.draw()
     fig.canvas.flush_events()

def detecting_algorithm():
    return False

# x line of plot
time_vec = np.arange(0, 20, time_step)[:512]
sample_freq = fftpack.fftfreq(time_vec.size, d=time_step)
# initailizing y line of subplot not important
y = (np.sin(2 * np.pi / period * time_vec) + 0.5 * np.random.randn(time_vec.size))
y_ = np.abs(fftpack.fft(y))

# You probably won't need this if you're embedding things in a tkinter plot...
plt.ion()
answer = genfromtxt('answer.csv', delimiter=',').tolist()
fig = plt.figure()
a1 = fig.add_subplot(121)
a2 = fig.add_subplot(122)
line1, = a1.plot(time_vec, y, 'r-') # Returns a tuple of line objects, thus the comma
line2, = a2.plot(sample_freq, y_, 'r-')
for i in range(0,10): 
   one_step(i,fig,time_vec,line1,line2)
print('detect is :',detection)
print('answer is :',answer)
dataframe = pd.DataFrame(detection)
dataframe.to_csv("result.csv",header=False,index=False)