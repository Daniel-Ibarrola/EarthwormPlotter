## Program to plot the data obtained from earthworm of an SSN station. 

from custom_queue import Queue
# Third Party
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import PyEW
# Standard library
import argparse
import logging
import pickle
import time
import tkinter as tk
import threading

# Stations Names 'SS60', 'S160', 'S260', 'S360', 'IM40', 'D170', 'D270'


# Queue of wave data for all stations
wave_queue = Queue()
# Queue for the station and channel that will be plotted
station_queue  = Queue()
# Plotting configuration
plt.style.use('bmh')
# Logging 
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
# logging file handler
fileHandler = logging.FileHandler("../logs/main.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
# logging console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)


class EstacionInvalida(ValueError):
    pass

### The GUI class and methods    
class PlotterApp:
    """ Class that handles the GUI."""
    
    def __init__(self, stations_file, sample_rate, 
                root=tk.Tk()):
        
         # Station data
        self.station_boundaries, self.stations_dict = self.load_station_data(stations_file)
        
        # Data for Plotting
        self.acc_data = [] # List of lists where each list contains wave data for a given timestep.
        self.time_data = []
        self.time_step_counter = 0
        self.acc_data_counter = 0
        self.wave_splitter = np.arange(0, sample_rate, 2) # To take just half the samples
        self.n_samples = sample_rate
        # Plot limits data
        self.acc_lower_lim = self.station_boundaries[station][channel][0]
        self.acc_upper_lim = self.station_boundaries[station][channel][1]
        self.time_lower_lim = 0 
        self.time_upper_lim = 60 # time in seconds
        self.time_size = (self.n_samples / 2) * self.time_upper_lim # Size of time axis
        # Plotting Flag
        self.PLOT = False
        # To check if we have data in the queue. If it passes a treshold the stop_plot method will be called
        self.data_status = 0
        
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
        
        self.button_1 = tk.Button(master=self.options_frame, 
                                  text="Iniciar", 
                                  font=('calbiri', 18), 
                                  command=self.plot_start)
        self.button_2 = tk.Button(master=self.options_frame, 
                                  text="Parar", 
                                  font=('calbiri', 18),
                                  command=self.plot_stop)

        self.status_val = tk.StringVar(root)
        self.status_val.set("Conectado")
        self.station_label = tk.Label(master=self.options_frame, text="Estación", font=("calbiri", 20), background="white")
        self.channel_label = tk.Label(master=self.options_frame, text="Canal", font=("calbiri", 20), background="white")
        self.status_label = tk.Label(master=self.options_frame, textvariable=self.status_val, 
                                     font=("calbiri", 20), background="white")

        self.station_val = tk.StringVar(root)
        self.channel_val = tk.StringVar(root)
        self.station_val.set(station)
        self.channel_val.set(channel)

        self.station_options = list(self.stations_dict.keys())
        self.channel_options = self.stations_dict[station]

        self.station_menu = tk.OptionMenu(self.options_frame, self.station_val, *self.station_options)
        self.station_menu["menu"].configure(font=("calbiri", 15))
        self.channel_menu = tk.OptionMenu(self.options_frame, self.channel_val, *self.channel_options)
        self.channel_menu["menu"].configure(font=("calbiri", 15))

        self.station_button = tk.Button(master=self.options_frame, text="Seleccionar", command=self.update_station)
        self.channel_button = tk.Button(master=self.options_frame, text="Seleccionar", command=self.update_channel)

        self.button_2.grid(row=0, column=1, padx=5, pady=4)
        self.button_1.grid(row=0, column=0, padx=5, pady=4)

        self.station_label.grid(row=0, column=2, padx=5, pady=4)
        self.channel_label.grid(row=0, column=3, padx=5, pady=4)
        self.status_label.grid(row=0, column=4, padx=5, pady=4)

        self.station_menu.grid(row=1, column=2, padx=2, pady=10, sticky="EW")
        self.channel_menu.grid(row=1, column=3, padx=2, pady=10, sticky="EW")

        self.station_button.grid(row=2, column=2, pady=4)
        self.channel_button.grid(row=2, column=3, pady=4)
    
    def create_figure(self):
        """ Creates a matplotlib figure where station data will be plotted.
        
            Returns
            -------
            fig: matplotlib.figure.Figure
                A matplotlib figure
            
            ax : matplotlib.ax
                An axis object asociated with the figure. This object is modified by other functions
                to change the plot labels, and limits.
            
            lines : matplotlib.lines.Lines2D
                Lines that contain the data of the plot. This is updated by the plot_data method.
        """
        global station, channel
        unit = "s" 
        
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.set_title(f'Estación: {station}. Canal: {channel}')
        ax.set_xlabel(f'Tiempo ({unit})')
        ax.set_ylabel('Amplitud')
        ax.set_xlim(self.time_lower_lim, self.time_size)
        ax.set_ylim(int(self.acc_lower_lim), int(self.acc_upper_lim))
        # Set xticks for the plot
        step = int((self.n_samples / 2) * 10)
        ax.set_xticks(np.arange(0, self.time_size + step, self.time_size / 6, dtype=np.int64))
        ax.set_xticklabels(list(range(0, self.time_upper_lim + 10, 10)))
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        lines = ax.plot([],[])[0]
        lines.alpha = 0.5
        lines.set_color("#B03A2E")
        
        return fig, ax, lines
    
    def update_station(self):
        """ Updates the plot after selecting a different station in the program
            by using the station menu and buttons.
            
            The channel menu options are updated as well.
            
            It also clears the station_queue so that data for new stations can be plotted.
        """
        global station, channel
        station = self.station_val.get()
        # Update channel options for the selected station
        channel_options = self.stations_dict[station]
        channel = channel_options[0]
        self.channel_val.set(channel_options[0])
        self.channel_menu["menu"].delete(0, "end")
        for chan in channel_options:
            self.channel_menu["menu"].add_command(label=chan, command=tk._setit(self.channel_val, chan))
        # Update plot title and x and y limits
        self.ax.set_title(f'Estación: {station}. Canal: {channel}')
        self.ax.set_ylim(self.station_boundaries[station][channel][0], self.station_boundaries[station][channel][1])
        self.canvas.draw()
        self.plot_stop()
        self.restart_plot()
        
        logging.info(f"Changed Station to {station}. Current channel: {channel}")
        

    def update_channel(self):
        """ Updates the plot after selecting a different channel in the program
            by using the channel menu and buttons.
            
            It also clears the station_queue so that data for a new station channel can be plotted.
        """
        global channel
        channel = self.channel_val.get()
        # Update plot title and x and y limits
        self.ax.set_title(f'Estación: {station}. Canal: {channel}')
        self.ax.set_ylim(self.station_boundaries[station][channel][0], self.station_boundaries[station][channel][1])
        self.canvas.draw()
        self.plot_stop()    
        self.restart_plot()
        
        logging.info(f"Changed channel to {channel}. Current station: {station}")
        
    def plot_data(self):
        """ Plot wave data from station"""

        update_vertical_range = True
        step = int(self.n_samples / 2)
        
        if self.PLOT:
            
            if not station_queue.empty():
                wave = station_queue.get()

                # When the plot starts time_data needs to be updated dinamically. Once it reaches the time limit
                # it is no longer necesary to update time_data as the new wave data that arrives will be superimposed
                # on the previous data.
                if len(self.time_data) == 0:
                    self.time_data = list(range(0, step))
                    self.acc_data.append(wave["data"][self.wave_splitter])
                elif len(self.time_data) < self.time_size:
                    self.time_step_counter += step
                    self.time_data += list(range(self.time_step_counter + 1, self.time_step_counter + step + 1))
                    self.acc_data.append(wave["data"][self.wave_splitter])
                elif len(self.time_data) == self.time_size:
                    # Here each sublist of acc_data will be replaced by the corresponding timestep. But time_data
                    # stays fixed.
                    if self.acc_data_counter >= self.time_upper_lim:
                        self.acc_data_counter = 0
                    self.acc_data[self.acc_data_counter] = wave["data"][self.wave_splitter]
                    self.acc_data_counter += 1
                
                if update_vertical_range:
                    # Dynamically resize the vertical axis in case wave samples with a higher or lower value than the
                    # limits if the vertical axis are found.  
                    wave_min = np.min(wave["data"])
                    wave_max = np.max(wave["data"]) 
                    if wave_min < self.acc_lower_lim:
                        self.acc_lower_lim = wave_min
                        self.ax.set_ylim(int(self.acc_lower_lim), int(self.acc_upper_lim))
                    if wave_max > self.acc_upper_lim:
                        self.acc_upper_lim = wave_max
                        self.ax.set_ylim(int(self.acc_lower_lim), int(self.acc_upper_lim))
                
                acc_data = np.array(self.acc_data).reshape(-1)
                assert acc_data.shape[0] <= self.time_size, f"Acc data length is {len(acc_data)}"
                assert acc_data.shape[0] == len(self.time_data), f"Acc length is {len(acc_data)} and Time is {len(self.time_data)}"
                
                # print(self.time_data)
                # print(acc_data)
                self.lines.set_xdata(self.time_data)
                self.lines.set_ydata(acc_data)
                
                station_queue.task_done()
                self.canvas.draw()
                if self.data_status > 0:
                    self.data_status = 0
                    if self.status_val.get() == "Desconectado":
                        self.change_status()
            else:
                if self.data_status > 2:
                    logging.warning("Station queue is empty")
                elif self.data_status > 10:
                    logging.info("No data in queue. Stopping plot.")
                    self.plot_stop()
                    self.change_status()
                self.data_status += 1
                time.sleep(1)
        
        self.root.after(1, self.plot_data)
    
    def plot_start(self):
        """ Change the flag to start plotting."""
        self.PLOT = True

    def plot_stop(self):
        """ Change the flag to stop plotting."""
        self.PLOT = False
        
    def restart_plot(self):
        """ Restarts plot data so a new plot can be drawn when changing the station and/or
            channel via ine if the buttons.
        """
        # Clear time and wave data
        station_queue.clear()
        self.acc_data.clear()
        self.time_data.clear()
        # Reset counters
        self.acc_data_counter = 0
        self.time_step_counter = 0
        # Reobtain the lower and upper limits
        self.acc_lower_lim = self.station_boundaries[station][channel][0]
        self.acc_upper_lim = self.station_boundaries[station][channel][1]
    
    @staticmethod    
    def load_station_data(path):
        """ Load station names and channels with it's boundaries as computed from the
            script station_boundaries.py. 
        """
        with open(path, "rb") as station_file:
            station_boundaries = pickle.load(station_file)
        
        stations_dict = {}
        for st, ch in station_boundaries.items():
            stations_dict[st] = list(ch.keys())
        
        return station_boundaries, stations_dict
    
    def change_status(self):
        """ To display a label in the gui when no data is being recieved."""
        if self.status_val.get() == "Conectado":
            self.status_val.set("Desconectado")     
            self.status_label.config(fg="red")
        else:
            self.status_val.set("Conectado")
            self.status_label.config(fg="black")
        
    def start(self):
        """ Starts tkinter mainloop"""
        self.root.after(1, self.plot_data)
        self.root.mainloop()    
    
    def quit(self, *args):
        self.root.destroy()

### Earthworm module and functions.
class EarthwormWaveAcquirer:
    """ Class that creates and eartwhorm module and a thread that will aquire wave data from
        earthworm and put it in a queue that can be used by other threads.
    """
    
    def __init__(self, ring=1000, module_id=151, installation_id=76, heart_beats=30, debug=False):
        # Earthworm module to recieve the data
        self.data_mod = PyEW.EWModule(ring, module_id, installation_id, heart_beats, debug)
        self.data_mod.add_ring(1000)
        
        logging.info(f"Created pyearthworm module with id: {module_id}, installation: {installation_id}"
                    f",ring: {ring}")
        
        self.recieve_thread = threading.Thread(target=self.recieve_wave, daemon=True)
        self.filter_thread = threading.Thread(target=self.filter_data, daemon=True)
        self.check_status_thread = threading.Thread(target=self.check_status, daemon=True)
        
        self.STOP = False # flag to stop pyearthworm 
        
    def recieve_wave(self):
        """ Recieve wave data from Earthworm and put it in a queue.
        """
        ring_index = 0
        self.counter = 0 # To keep track of whether data is being recieved.
        while True:
            if self.STOP:
                return 
            
            wave = self.data_mod.get_wave(ring_index)
            if len(wave) > 0:
                wave_queue.put(wave)
                self.counter = 0
            else:
                time.sleep(1)
                self.counter += 1
    
    def filter_data(self):
        """ Filters the wave_queue to only get data from a particular station and channel
            and puts it in station_queue
        """
        while True:
            if self.STOP:
                return

            wave = wave_queue.get()
            if wave["station"] == station and wave["channel"] == channel:
                station_queue.put(wave)
            wave_queue.task_done()
        
                
    def check_status(self):
        """ To check whether wave data is being recieved from earthworm."""
        # Checks every 60 seconds to see if we are receiving data.
        while True:
            if self.STOP:
                return
            
            if self.counter >= 20:
                logging.warning("Not recieving wave data")
            
            time.sleep(60)
             
    def start(self):
        """ Starts the thread to aquire wave data."""
        self.recieve_thread.start()
        self.filter_thread.start()
        self.check_status_thread.start()
        
    def stop(self):
        """ Stops all threads and the earthworm module in a clean way."""
        self.STOP = True
        print('\n=============')
        print('Stopping pyearthworm module...')    

        # Clean Exit
        self.data_mod.goodbye()
        logging.info("Stopped pyearthworm module")
       

def main():
    """ Main function of the program. It creates an instance of the waveacquirer class and an instance 
        of the plotter class.
    """
    global channel, station

    parser = argparse.ArgumentParser(description="Graficador de estaciones de earthworm")
    parser.add_argument("--estaciones", dest="stations", required=True,
                        help="Estaciones que se van a graficar. Puede ser 'pozo' o 'cires'")
    parser.add_argument("--nmuestras", dest="srate", required=True,
                        help="Numero de muestras por segundo de las estaciones")

    args = parser.parse_args()
    if args.stations.lower() == "pozo":
        stations_file = "./stations_pozo"
        # Station and channel. These values will be used at the start of the program.
        station = "SS60"
        channel = "HLN"
    elif args.stations.lower() == "cires":
        stations_file = "./stations_cires"
        station = "CU80"
        channel = "HLZ"
    else:
        raise EstacionInvalida("Nombre invalido para estaciones. Debe ser pozo o cires")

    sample_rate = int(args.srate)
    # Earthworm Module Data
    installation_id = 76  
    module_id = 151
    wave_ring = 1000
    heart_beats = 30.0
    debug = False

    wave_acquirer = EarthwormWaveAcquirer(wave_ring, module_id, installation_id, heart_beats, debug)
    wave_acquirer.start()
    
    plotter = PlotterApp(stations_file, sample_rate)
    plotter.start()
    
    wave_acquirer.stop()
    

if __name__ == "__main__":
    main()