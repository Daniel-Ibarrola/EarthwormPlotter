## Program to plot the data obtained from earthworm of an SSN station. 

# Third Party
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import PyEW
# Standard library
from collections import deque
import queue
import time
import tkinter as tk
import threading

# Stations Names 'SS60', 'S160', 'S260', 'S360', 'IM40', 'D170', 'D270'

# Earthworm Module Data
installation_id = 76  
module_id = 151
wave_ring = 1000
heart_beats = 30.0
debug = False
# Earthworm module to recieve the data
data_mod = PyEW.EWModule(wave_ring, module_id, installation_id, heart_beats, debug)
data_mod.add_ring(1000)
# Station and channel
station = "SS60"
channel = "HLN"
# Queue of wave data
wave_queue = queue.Queue()
# Samples
sample_rate = 200
n_samples = 250
# Flags
STOP = False # to stop pyearthworm 
PLOT = False # to start plotting

# Dictionary with the min and max values of data for each station
station_boundaries = {
    'SS60': {'HLN': [-315638, -315404], 
             'HLE': [-157513, -157271], 
             'HLZ': [1270744, 1271098]}, 
    'C166': {'HLZ': [1613763, 1614967], 
             'HL1': [-10913, -9326], 
             'HL2': [-46786, -44677]}, 
    'S160': {'HLZ': [1576770, 1577201], 
             'HL1': [41405, 42137], 
             'HL2': [6533, 6918]}, 
    'C266': {'HLZ': [1562360, 1563266], 
             'HL1': [-36101, -35113], 
             'HL2': [-27432, -26334]}, 
    'S260': {'HLZ': [-23, 270], 
             'HL1': [314, 369], 
             'HL2': [-298, -4]}, 
    'C366': {'HLZ': [1627035, 1627344], 
             'HL1': [159, 616], 
             'HL2': [-122072, -121607]}, 
    'S360': {'HLZ': [-15996, -15927],
             'HL1': [-16101, -15771], 
             'HL2': [-18901, -18313]}, 
    'CS66': {'HLZ': [1187956, 1190246], 
             'HLN': [11307, 12533], 
             'HLE': [-103109, -101662]}, 
    'IM40': {'HLZ': [1281289, 1281932], 
             'HLN': [-72340, -71345], 
             'HLE': [-276915, -276311]}, 
    'D170': {'HLZ': [1605041, 1605688], 
             'HL1': [15333, 15684], 
             'HL2': [-34932, -34677]}, 
    'D270': {'HLZ': [1505097, 1505504], 
             'HL1': [-30548, -29970], 
             'HL2': [-9761, -9073]}
}

# Plotting variables
acc_lower_lim = station_boundaries[station][channel][0]
acc_upper_lim = station_boundaries[station][channel][1]
time_lower_lim = 0 
time_upper_lim = 60 # time in seconds
acc_data_queue = deque()
time_data = []
time_size = (n_samples / 2) * time_upper_lim # Size of time axis
time_lower_lim = 0
counter = 0
wave_splitter = np.arange(0, 250, 2) # To take just half the samples
        
def recieve_wave():
    """ Receieve wave data from Earthworm and put it in a queue.
    """
    ring_index = 0
    while True:
        if STOP:
            return 
        
        wave = data_mod.get_wave(ring_index)
        if len(wave) > 0 and wave["station"] == station and wave["channel"] == channel:
            wave_queue.put(wave)
        else:
            time.sleep(0.01)
       
def plot_data():
    """ Plot wave data from station"""
    global PLOT
    global ax, canvas, lines, root
    global counter
    global acc_lower_lim, acc_upper_lim
    global time_data, acc_data, time_lower_lim, time_size

    update_vertical_range = True
    step = int(n_samples / 2)
    
    if PLOT:
        
        wave = wave_queue.get()
   
        if len(time_data) == 0:
            time_data = list(range(0, step))
            acc_data_queue.append(wave["data"][wave_splitter])
        elif len(time_data) < time_size:
            counter += step
            time_data += list(range(counter + 1, counter + step + 1))
            acc_data_queue.append(wave["data"][wave_splitter])
        elif len(time_data) == time_size:
            acc_data_queue.popleft()
            acc_data_queue.appendleft(wave["data"][wave_splitter])
        
        if update_vertical_range:
            # Dynamically resize the vertical axis
            wave_min = np.min(wave["data"])
            wave_max = np.max(wave["data"]) 
            if wave_min < acc_lower_lim:
                acc_lower_lim = wave_min
                ax.set_ylim(int(acc_lower_lim), int(acc_upper_lim))
            if wave_max > acc_upper_lim:
                acc_upper_lim = wave_max
                ax.set_ylim(int(acc_lower_lim), int(acc_upper_lim))
        
        acc_data = np.array(acc_data_queue).reshape(-1)
        assert acc_data.shape[0] <= time_size, f"Acc data length is {len(acc_data)}"
        assert acc_data.shape[0] == len(time_data), f"Acc length is {len(acc_data)} and Time is {len(time_data)}"
        
        # print(time_data)
        # print(acc_data)
        lines.set_xdata(time_data)
        lines.set_ydata(acc_data)
        
        wave_queue.task_done()
        time.sleep(0.1)
        canvas.draw()
    
    root.after(1, plot_data)

def plot_start():
    global PLOT
    PLOT = True

def plot_stop():
    global PLOT
    PLOT = False
    
   
def main():
    """ Main function of the program. It creates a thread for receieving data
        and the GUI that contains the plot.
    """
    
    global STOP
    global ax, canvas, lines
    global root
    
    unit = "s"
    
    t1 = threading.Thread(target=recieve_wave, daemon=True)
    t1.start()
    
    root = tk.Tk()
    root.title('Graficador Earthworm')
    root.configure(background = 'light blue')
    root.geometry("800x600") # set the window size

    fig = Figure()
    ax = fig.add_subplot(111)
    
    ax.set_title(f'Estación: {station}. Canal: {channel}')
    ax.set_xlabel(f'Tiempo ({unit})')
    ax.set_ylabel('Frecuencia')
    ax.set_xlim(time_lower_lim, time_size)
    ax.set_ylim(int(acc_lower_lim), int(acc_upper_lim))
    # Set xticks for the plot
    if unit == "s":
        step = int((n_samples / 2) * 10)
        ax.set_xticks(np.arange(0, time_size + step, time_size / 6, dtype=np.int64))
        ax.set_xticklabels(list(range(0, time_upper_lim + 10, 10)))
    else:
        raise NotImplementedError
    
    lines = ax.plot([],[])[0]

    canvas = FigureCanvasTkAgg(fig, master=root)  
    # A tkinter drawing area.
    canvas.get_tk_widget().place(x=10, y=10, width=650, height=400)
    canvas.draw()

    root.update()
    start = tk.Button(root, text="Iniciar", font=('calbiri', 12), command=lambda : plot_start())
    start.place(x=100, y=450 )

    root.update()
    stop = tk.Button(root, text="Terminar", font=('calbiri', 12), command=lambda : plot_stop())
    stop.place(x=start.winfo_x() + start.winfo_reqwidth() + 20, y=450)

    root.after(1, plot_data)
    root.mainloop()
    
    STOP = True
    print('\n =============')
    print('Exit Main Loop...')    

    # Clean Exit
    data_mod.goodbye()
    print("\nSTATUS: Stopping, you hit ctl+C. ")

if __name__ == "__main__":
    main()