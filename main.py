import soundfile as sf
import numpy as np
import csv
import time
import random
import threading
import datetime
import argparse
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
import queue

data_queue = queue.Queue()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Audio processing to vibration motors')
parser.add_argument(
  '-f',
  '--filename', 
  type=str,
  help='The name of the audio file.',
  required=True
)

parser.add_argument(
  '-p', 
  '--plot', 
  type=bool, 
  help='Whether to plot a graph. Default: False',
  default=False,
  required=False
)

parser.add_argument(
  '-b', 
  '--bins', 
  type=int, 
  help='Number of bins',
  required=True
)

parser.add_argument(
  '-v', 
  '--volume', 
  type=int, 
  help='Volume. Value from 0 - 100',
  required=True,
  choices=range(1, 101)
)

parser.add_argument(
  '-s', 
  '--samplerate', 
  type=int, 
  help='Sample rate.',
  required=False,
  default=44100
)

parser.add_argument(
  '-t', 
  '--time', 
  type=float, 
  help='Duration of chunk to read. Default is 16 ms',
  required=False,
  default=0.016
)
args = parser.parse_args()

filename=args.filename

# Function to control a motor and write data to a CSV file
sample_rate = args.samplerate  # Assuming a sample rate of 44100 Hz
chunk_duration = args.time # 16 milliseconds
num_bins = args.bins

# matplotlib stuff
fig, ax = plt.subplots()

# Create a line object for the plot
line, = ax.plot([], [], lw=2)

# Set the plot limits
ax.set_ylim(-0.5, 1.5)  # Adjust this to match the range of your data
ax.set_xlim(0, num_bins)  # Adjust this to match the range of your data

# Set the plot labels
ax.set_xlabel('Bin')
ax.set_ylabel('Intensity')
ax.set_title(filename)

# Show the plot in interactive mode
plt.ion()
plt.show()
# Define the maximum window size
window_size = 1000  # Adjust this to your preference

# Create a list to store the data points
data_points = []
# Create a list of line objects
lines = [ax.plot([], [], lw=2)[0] for _ in range(num_bins)]


executor = ThreadPoolExecutor(max_workers=50)
#control motor
def control_motor(motor_number, intensity):
    intensity = format(intensity*100, ".2f")
    print(f"Motor {motor_number} vibration intensity {intensity}")

# Function to read audio data from a music file in chunks
def read_audio_data(file_path, chunk_size):
    with sf.SoundFile(file_path) as audio_file:
        while True:
            audio_data = audio_file.read(chunk_size)
            if len(audio_data) == 0:
                break
            yield audio_data, audio_file.samplerate

# Function to apply Fourier Transform and plot it
def apply_fourier_transform(audio_data):
    amplitudes = np.abs(np.fft.rfft(audio_data))
    frequencies = np.fft.rfftfreq(len(amplitudes), 1.0 / sample_rate)
    return frequencies, amplitudes

plot_thread = None  # Define plot_thread outside the function
# Function to perform binning and map bins to motors
def bin_and_map(frequencies, amplitudes, num_bins):
    global plot_thread
    bin_edges = np.linspace(frequencies.min(), frequencies.max(), num_bins + 1)
    bins = np.digitize(frequencies, bin_edges)
    threads = []
    intensities = np.zeros(num_bins)  # Create an array to store the intensities
    for i in range(num_bins):
        indices = np.where(bins == i+1)[0]  # Get the indices of frequencies in this bin
        bin_amplitudes = amplitudes[indices]  # Get the corresponding amplitudes
        if bin_amplitudes.size > 0 and amplitudes.max() > 0:
          intensity = bin_amplitudes.max() / amplitudes.max()
          intensities[i] = intensity  # Store the intensity
          executor.submit(control_motor, i, intensity)

    data_queue.put(intensities)
    # Remove old data points if the window size is exceeded
    if len(data_points) > 20:
        data_points.pop(0)

# Function to update the plot
def update_plot(data_points, lines):
    # Update each line object
    for i, line in enumerate(lines):
        line.set_ydata([point[i] for point in data_points])
        line.set_xdata(range(len(data_points)))
    # Update the x-axis limit
    ax.set_xlim(0, len(data_points))
    plt.draw()
    plt.pause(0.01)

# Main loop
chunk_size = int(sample_rate * chunk_duration)  # Calculate the chunk size
volume = args.volume # Set the volume to 100%
for audio_chunk in read_audio_data(f'./sample/{filename}', chunk_size):
    audio_data, sample_rate = audio_chunk
    audio_data = audio_data * (args.volume/100)  # Adjust the volume
    frequencies, amplitudes = apply_fourier_transform(audio_data)
    bin_and_map(frequencies, amplitudes, num_bins)
    # Check the queue for new data
    while not data_queue.empty():
        intensities = data_queue.get()
        # Add the new data point to the list
        data_points.append(intensities)
        # Remove old data points if the window size is exceeded
        if len(data_points) > 20:
            data_points.pop(0)
        # Update the plot
        if args.plot:
          update_plot(data_points, lines)
    
    time.sleep(chunk_duration)  # Wait for the duration of the audio chunk