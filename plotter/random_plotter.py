# Program to create a real time plot of random data using 
# a tkinter gui. 

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

import tkinter as tk
import time


### Global variables
data_y = []
data_x = []
counter = 0
cond = False
# Size of x axis
x_size = 300
x_lower_lim = 0

def plot_data():
    global cond, counter
    global data_y, data_x
    global x_size, x_lower_lim
    
    if (cond == True):
        
        data_y.append(np.random.randint(20, 80, size=None))
        data_x.append(counter)
        counter += 1
        
        if len(data_y) == x_size:
            # Dynamically resize the x axis
            x_lower_lim = int(counter - x_size / 2)
            ax.set_xlim(x_lower_lim, x_lower_lim + x_size)
            
            data_y = data_y[int(len(data_y) / 2) - 1: -1]
            data_x = data_x[int(len(data_x) / 2) - 1: -1]
            assert len(data_y) == x_size / 2, f"Y lenght is {len(data_y)}"
            assert len(data_x) == x_size / 2, f"X lenght is {len(data_x)}"
            
        assert len(data_y) <= x_size, f"Y data length is {len(data_y)}"
        assert len(data_y) == len(data_x), f"Y length is {len(data_y)} and X is {len(data_x)}"
       
        lines.set_xdata(data_x)
        lines.set_ydata(data_y)
        
        time.sleep(0.05)
        
        canvas.draw()
    
    root.after(1, plot_data)

def plot_start():
    global cond
    cond = True

def plot_stop():
    global cond
    cond = False
    

root = tk.Tk()
root.title('Real Time Plot')
root.configure(background = 'light blue')
root.geometry("700x500") # set the window size

fig = Figure()
ax = fig.add_subplot(111)

ax.set_title('Random Data')
ax.set_xlabel('Y')
ax.set_ylabel('X')
ax.set_xlim(x_lower_lim, x_size)
ax.set_ylim(0, 100)
lines = ax.plot([],[])[0]

canvas = FigureCanvasTkAgg(fig, master=root)  
# A tkinter drawing area.
canvas.get_tk_widget().place(x=10, y=10, width=500, height=400)
canvas.draw()

root.update()
start = tk.Button(root, text="Start", font=('calbiri', 12), command=lambda : plot_start())
start.place(x = 100, y = 450 )

root.update()
stop = tk.Button(root, text="Stop", font =('calbiri', 12), command=lambda : plot_stop())
stop.place(x=start.winfo_x() + start.winfo_reqwidth() + 20, y=450)

root.after(1, plot_data)
root.mainloop()