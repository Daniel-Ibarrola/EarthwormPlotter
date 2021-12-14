## Program to plot the data obtained from earthworm of an SSN station. 

# Third Party
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
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

stations_dict = {}
for st, ch in station_boundaries.items():
    stations_dict[st] = list(ch.keys())

# Plotting configuration
plt.style.use('bmh')

### The GUI class and methods    
class PlotterApp:
    """ Class that handles the GUI."""
    def __init__(self, root=tk.Tk()):
        
        # Baic config of the app gui
        self.root = root
        self.root.title('Graficador Earthworm')
        self.root.geometry("1500x600")
        self.root.minsize(1500, 600)
        self.root.maxsize(1500, 600)
        self.root.configure(background='white')
        self.root.rowconfigure(0, minsize=400, weight=1)
        self.root.rowconfigure(1, minsize=150, weight=1)
        self.root.columnconfigure(0, minsize=800, weight=1)
       
        # The part that draws the plot
        self.canvas_frame = tk.Frame(master=root, background="white")
        self.canvas_frame.grid(row=0, column=0, sticky="NWES")
        self.figure, self.ax, self.lines = self.create_figure()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.canvas_frame)  
        # A tkinter drawing area.
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH)
        self.root.update()
        
        # Options part of the gui that includes buttons to plot. 
        self.options_frame = tk.Frame(master=self.root, background="white")
        self.options_frame.grid(row=1, column=0, padx=250, sticky="NEWS")
        
        self.button_1 = tk.Button(master=self.options_frame, text="Iniciar", font=('calbiri', 18))
        self.button_2 = tk.Button(master=self.options_frame, text="Parar", font=('calbiri', 18))

        self.label_1 = tk.Label(master=self.options_frame, text="Estación", font=("calbiri", 20), background="white")
        self.label_2 = tk.Label(master=self.options_frame, text="Canal", font=("calbiri", 20), background="white")

        self.station_val = tk.StringVar(root)
        self.channel_val = tk.StringVar(root)
        self.station_val.set(station)
        self.channel_val.set(channel)

        self.station_options = list(stations_dict.keys())
        self.channel_options = stations_dict[station]

        self.station_menu = tk.OptionMenu(self.options_frame, self.station_val, *self.station_options)
        self.station_menu["menu"].configure(font=("calbiri", 15))
        self.channel_menu = tk.OptionMenu(self.options_frame, self.channel_val, *self.channel_options)
        self.channel_menu["menu"].configure(font=("calbiri", 15))

        self.station_button = tk.Button(master=self.options_frame, text="Seleccionar", command=self.update_station)
        self.channel_button = tk.Button(master=self.options_frame, text="Seleccionar", command=self.update_channel)


        self.button_2.grid(row=0, column=1, padx=5, pady=4)
        self.button_1.grid(row=0, column=0, padx=5, pady=4)

        self.label_1.grid(row=0, column=2, padx=5, pady=4)
        self.label_2.grid(row=0, column=3, padx=5, pady=4)

        self.station_menu.grid(row=1, column=2, padx=2, pady=10, sticky="EW")
        self.channel_menu.grid(row=1, column=3, padx=2, pady=10, sticky="EW")

        self.station_button.grid(row=2, column=2, pady=4)
        self.channel_button.grid(row=2, column=3, pady=4)
        
        # Data for Plotting
        self.acc_data_queue = deque()
        self.time_data = []
        self.counter = 0
        self.wave_splitter = np.arange(0, 250, 2) # To take just half the samples
        self.acc_lower_lim = station_boundaries[station][channel][0]
        self.acc_upper_lim = station_boundaries[station][channel][1]
        self.time_lower_lim = 0 
        self.time_upper_lim = 60 # time in seconds
        self.time_size = (n_samples / 2) * self.time_upper_lim # Size of time axis
        # Plotting Flag
        self.PLOT = False
    
    def create_figure(self):
        
        default_station = "SS60"
        default_channel = "HLN"
        unit = "s" 
        
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.set_title(f'Estación: {default_station}. Canal: {default_channel}')
        ax.set_xlabel(f'Tiempo ({unit})')
        ax.set_ylabel('Frecuencia')
        ax.set_xlim(self.time_lower_lim, self.time_size)
        ax.set_ylim(int(self.acc_lower_lim), int(self.acc_upper_lim))
        # Set xticks for the plot
        step = int((n_samples / 2) * 10)
        ax.set_xticks(np.arange(0, self.time_size + step, self.time_size / 6, dtype=np.int64))
        ax.set_xticklabels(list(range(0, self.time_upper_lim + 10, 10)))
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        lines = ax.plot([],[])[0]
        lines.alpha = 0.5
        lines.set_color("#B03A2E")
        
        return fig, ax, lines
    
    def update_station(self):
        global station, channel
        station = self.station_val.get()
        # Update channel options for the selected station
        channel_options = stations_dict[station]
        channel = channel_options[0]
        self.channel_val.set(channel_options[0])
        self.channel_menu["menu"].delete(0, "end")
        for chan in channel_options:
            self.channel_menu["menu"].add_command(label=chan, command=tk._setit(self.channel_val, chan))
        # Update plot title and x and y limits
        self.ax.set_title(f'Estación: {station}. Canal: {channel}')
        self.ax.set_ylim(station_boundaries[station][channel][0], station_boundaries[station][channel][1])
        self.canvas.draw()
        self.plot_stop()
        # Clear the queue
        wave_queue.clear()

    def update_channel(self):
        global channel
        channel = self.channel_val.get()
        # Update plot title and x and y limits
        self.ax.set_title(f'Estación: {station}. Canal: {channel}')
        self.ax.set_ylim(station_boundaries[station][channel][0], station_boundaries[station][channel][1])
        self.canvas.draw()
        self.plot_stop()    
        # Clear the queue
        wave_queue.clear()
        
    def plot_start(self):
        self.PLOT = True

    def plot_stop(self):
        self.PLOT = False
    
    def plot_data(self):
        """ Plot wave data from station"""

        update_vertical_range = True
        step = int(n_samples / 2)
        
        if self.PLOT:
            
            wave = wave_queue.get()
    
            if len(self.time_data) == 0:
                self.time_data = list(range(0, step))
                self.acc_data_queue.append(wave["data"][self.wave_splitter])
            elif len(self.time_data) < self.time_size:
                self.counter += step
                self.time_data += list(range(self.counter + 1, self.counter + step + 1))
                self.acc_data_queue.append(wave["data"][self.wave_splitter])
            elif len(self.time_data) == self.time_size:
                self.acc_data_queue.popleft()
                self.acc_data_queue.appendleft(wave["data"][self.wave_splitter])
            
            if update_vertical_range:
                # Dynamically resize the vertical axis
                wave_min = np.min(wave["data"])
                wave_max = np.max(wave["data"]) 
                if wave_min < self.acc_lower_lim:
                    self.acc_lower_lim = wave_min
                    self.ax.set_ylim(int(self.acc_lower_lim), int(self.acc_upper_lim))
                if wave_max > self.acc_upper_lim:
                    self.acc_upper_lim = wave_max
                    self.ax.set_ylim(int(self.acc_lower_lim), int(self.acc_upper_lim))
            
            acc_data = np.array(self.acc_data_queue).reshape(-1)
            assert acc_data.shape[0] <= self.time_size, f"Acc data length is {len(acc_data)}"
            assert acc_data.shape[0] == len(self.time_data), f"Acc length is {len(acc_data)} and Time is {len(self.time_data)}"
            
            # print(self.time_data)
            # print(acc_data)
            self.lines.set_xdata(self.time_data)
            self.lines.set_ydata(acc_data)
            
            wave_queue.task_done()
            time.sleep(0.1)
            self.canvas.draw()
        
        self.root.after(1, self.plot_data)

    def start(self):
        self.root.mainloop()    
    
    def quit(self, *args):
        self.root.destroy()

### Function to recieve wave data from earthworm.
def recieve_wave():
    """ Recieve wave data from Earthworm and put it in a queue.
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
       

def main():
    """ Main function of the program. It creates a thread for receieving data
        and the GUI that contains the plot.
    """
    global STOP
    
    plotter = PlotterApp()
    plotter.start()
    
    t1 = threading.Thread(target=recieve_wave, daemon=True)
    t1.start()
    
    STOP = True
    print('\n =============')
    print('Exit Main Loop...')    

    # Clean Exit
    data_mod.goodbye()
    print("\nSTATUS: Stopping, you hit ctl+C. ")

if __name__ == "__main__":
    main()