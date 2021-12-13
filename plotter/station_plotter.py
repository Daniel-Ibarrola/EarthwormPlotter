## Program to plot the data obtained from earthworm of an SSN station. 

# Third Party
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import PyEW
# Standard library
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
# Flag to stop program
STOP = False
# Flag to start plotting
PLOT = False
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
vertical_lower_limit = station_boundaries[station][channel][0]
vertical_upper_limit = station_boundaries[station][channel][1]
y_data = []
x_data = []
x_size = n_samples * 20 # Size of x axis
x_lower_lim = 0
        
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
    global vertical_lower_limit, vertical_upper_limit
    global x_data, y_data, x_lower_lim, x_size
    update_vertical_range = False
    
    if PLOT:
        
        wave = wave_queue.get()
        
        y_data += wave["data"].tolist()
        if x_data:
            x_data += list(range(x_data[-1] + 1, x_data[-1] + n_samples + 1))
        else:
            x_data = list(range(0, n_samples))
        
        if len(y_data) == x_size:
            # Dynamically resize the x axis
            x_lower_lim = int(x_data[-1] - x_size / 2)
            ax.set_xlim(x_lower_lim, x_lower_lim + x_size)
            
            y_data = y_data[int(len(y_data) / 2) - 1: -1]
            x_data = x_data[int(len(x_data) / 2) - 1: -1]
            assert len(y_data) == x_size / 2, f"Y lenght is {len(y_data)}"
            assert len(x_data) == x_size / 2, f"X lenght is {len(x_data)}"
            
        assert len(y_data) <= x_size, f"Y data length is {len(y_data)}"
        assert len(y_data) == len(x_data), f"Y length is {len(y_data)} and X is {len(x_data)}"
        
        if update_vertical_range:
            wave_min = np.min(wave["data"])
            wave_max = np.max(wave["data"]) 
            if wave_min < vertical_lower_limit:
                vertical_lower_limit = wave_min
            if wave_max > vertical_upper_limit:
                vertical_upper_limit = wave_max
            
        lines.set_xdata(x_data)
        lines.set_ydata(y_data)
        
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
    """ Main function of the program. It creates a thread for receiveing data
        and another thread for processing and saving it.
    """
    
    global STOP
    global ax, canvas, lines
    global root
    
    t1 = threading.Thread(target=recieve_wave, daemon=True)
    t1.start()
    
    root = tk.Tk()
    root.title('Graficador Earthworm')
    root.configure(background = 'light blue')
    root.geometry("800x600") # set the window size

    fig = Figure()
    ax = fig.add_subplot(111)

    ax.set_title(f'Estación: {station}. Canal: {channel}')
    ax.set_xlabel('Tiempo')
    ax.set_ylabel('Frecuencia')
    ax.set_xlim(x_lower_lim, x_size)
    ax.set_ylim(int(vertical_lower_limit*1.0001), int(vertical_upper_limit*1.0001))
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


# Idea: plot wave based on time. So the plot will range from 0 to 24 hrs or from 0 to 60 minutes.