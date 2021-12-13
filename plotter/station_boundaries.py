## Program to get each SSN station top and lower values so it can be used
## to set the limits of the vertical axis of a plot.

# Third Party
import numpy as np
import PyEW
# Standard library
from collections import defaultdict
import queue
import time
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


station_boundaries = defaultdict(dict)

def get_boundaries():
    """ Populate station boundaries dictionary with the upper and lower limit
        of each station and channel.
    """
    while True:
        if STOP:
            return 
        
        wave = wave_queue.get()
        wave_min = np.min(wave["data"])
        wave_max = np.max(wave["data"])
        
        try:
            len(station_boundaries[wave["station"]][wave["channel"]])
        except KeyError:
            station_boundaries[wave["station"]][wave["channel"]] = [wave_min, wave_max]
        
        try:
            if wave_min < station_boundaries[wave["station"]][wave["channel"]][0]:
                station_boundaries[wave["station"]][wave["channel"]][0] = wave_min
            if wave_max > station_boundaries[wave["station"]][wave["channel"]][1]:
                station_boundaries[wave["station"]][wave["channel"]][1] = wave_max
        except KeyError:
            pass 
        
        wave_queue.task_done()
        

def recieve_wave():
    """ Receieve wave data from Earthworm and put it in a queue.
    """
    ring_index = 0
    while True:
        if STOP:
            return 
        
        wave = data_mod.get_wave(ring_index)
        if len(wave) > 0:
            wave_queue.put(wave)
        else:
            time.sleep(0.01)
       
     
def main():
    """ Main function of the program. It creates a thread for receiveing data
        and another thread for processing and saving it.
    """
    
    global STOP
    
    t1 = threading.Thread(target=recieve_wave, daemon=True)
    t2 = threading.Thread(target=get_boundaries, daemon=True)
    
    t1.start()
    t2.start()
    
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        STOP = True
        print("Stations Dictionary\n")
        print(dict(station_boundaries))
        
        print('\n\n=============')
        print('Exit Main Loop...')    

        ## Clean Exit
        data_mod.goodbye()
        print("\nSTATUS: Stopping, you hit ctl+C. ")

if __name__ == "__main__":
    main()
