import tkinter as tk

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

def update_station():
    global station, channel
    station = station_val.get()
    print(f"Selected station {station}")
    
    # Update channel options for the selected station
    channel_options = stations_dict[station]
    channel = channel_options[0]
    channel_val.set(channel_options[0])
    channel_menu["menu"].delete(0, "end")
    for chan in channel_options:
        channel_menu["menu"].add_command(label=chan, command=tk._setit(channel_val, chan))

def update_channel():
    global channel
    channel = channel_val.get()
    print(f"Selected channel {channel}")

stations_dict = {}
for station, channels in station_boundaries.items():
    stations_dict[station] = list(channels.keys())

station = "SS60" # This is the default station
channel = "HLN" # default channel

root = tk.Tk()
root.configure(background="white")

button_1 = tk.Button(master=root, text="Iniciar", font=('calbiri', 18))
button_2 = tk.Button(master=root, text="Parar", font=('calbiri', 18))

label_1 = tk.Label(master=root, text="Estación", font=("calbiri", 20), background="white")
label_2 = tk.Label(master=root, text="Canal", font=("calbiri", 20), background="white")

station_val = tk.StringVar(root)
channel_val = tk.StringVar(root)
station_val.set(station)
channel_val.set(channel)

station_options = list(stations_dict.keys())
channel_options = stations_dict[station]

station_menu = tk.OptionMenu(root, station_val, *station_options)
station_menu["menu"].configure(font=("calbiri", 15))
# station_menu["menu"].configure(bg="#85C1E9")
channel_menu = tk.OptionMenu(root, channel_val, *channel_options)
channel_menu["menu"].configure(font=("calbiri", 15))
# channel_menu["menu"].configure(bg="#85C1E9")

station_button = tk.Button(master=root, text="Seleccionar", command=update_station)
channel_button = tk.Button(master=root, text="Seleccionar", command=update_channel)

#print(station_menu["menu"].keys())

button_1.grid(row=0, column=0, padx=5, pady=4)
button_2.grid(row=0, column=1, padx=5, pady=4)

label_1.grid(row=0, column=5, padx=5, pady=4)
label_2.grid(row=0, column=6, padx=5, pady=4)

station_menu.grid(row=1, column=5, padx=2, pady=10, sticky="EW")
channel_menu.grid(row=1, column=6, padx=2, pady=10, sticky="EW")

station_button.grid(row=2, column=5, pady=4)
channel_button.grid(row=2, column=6, pady=4)

root.mainloop()