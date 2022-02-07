# Earthworm Plotter

Earthworm station data plotter.

## Requirements

To use the earthworm plotter two things are required: an earthworm installation, and a conda envronment with pyearthworm.

## How to use it

1. Activate earthworm environmental variables.
```bash
source ew/cires/params/ew_linux.bash
```
2. Activate the conda environmente that has pyeathworm installed.
```bash
conda acivate pyew
```
3. go to ./plotter and run the program main.py. It accepts the folowing arguments:

- --estaciones. Can be "pozo" or "cires". This are thesations that will be plotted.

- --nmuestras. The sample rate (samples/second) If "pozo" is selected it should be 250. If "cires" is selected it should be 100. However this may vary.

Example usage

```bash
python main.py --estaciones cires --nmuestras 100 
```