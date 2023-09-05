import soundfile as sf
import numpy as np
import time
import argparse
import matplotlib
matplotlib.use('TkAgg')
from concurrent.futures import ThreadPoolExecutor
import queue
import RPi.GPIO as GPIO
import sounddevice as sd
from threading import Thread, Lock

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Audio processing to vibration motors')
parser.add_argument(
  '-f',
  '--filename', 
  type=str,
  help='The name of the audio file.',
  required=False,
  default=''
)

parser.add_argument(
  '-b', 
  '--bins', 
  type=int, 
  help='Number of bins',
  required=True
)

parser.add_argument(
  '-o', 
  '--output', 
  type=bool, 
  help='Whether to output the sound',
  required=False,
  default=False
)
args = parser.parse_args()

filename=args.filename
sample_rate = 32000

# Function to control a motor and write data to a CSV file
chunk_duration = 0.016 # 16 milliseconds
num_bins = args.bins
executor = ThreadPoolExecutor(max_workers=10)

pwms = []
# Setup
GPIO.setmode(GPIO.BCM)  # Use BCM numbering for GPIO pins
motor_pins = [17, 22, 23, 27]  # Replace with your GPIO pin numbers
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    pwm = GPIO.PWM(pin, 100)
    pwm.start(0)  # Start with a duty cycle of 0%
    pwms.append(pwm)

#control motor
def control_motor(motor_number, intensity):
    if intensity > 1:
        intensity = 1
    intensity = float(format(intensity * 100, ".0f"))
    # print(f"Motor {motor_number} vibrating with intensity {intensity}")
    pwms[motor_number].ChangeDutyCycle(intensity)
    time.sleep(0.1)  # Vibrate for 16 ms
    pwms[motor_number].ChangeDutyCycle(0)  # Stop the vibration

# Function to read audio data from a music file in chunks
def read_audio_data(file_path, chunk_size):
    with sf.SoundFile(file_path) as audio_file:
        # If chunk_size is None, calculate it based on the sample_rate from the file
        if chunk_size is None:
            chunk_size = int(audio_file.samplerate * chunk_duration)

        while True:
            audio_data = audio_file.read(chunk_size)
            if len(audio_data) == 0:
                break
            yield audio_data

def get_sample_rate_from_file(file_path):
    with sf.SoundFile(file_path) as audio_file:
        return audio_file.samplerate

def get_sample_rate_from_device(device_index):
    dev_info = sd.query_devices(device_index)
    return dev_info['default_samplerate']

# Function to apply Fourier Transform and plot it
def apply_fourier_transform(audio_data):
    amplitudes = np.abs(np.fft.rfft(audio_data))
    frequencies = np.fft.rfftfreq(len(audio_data), 1.0 / sample_rate)
    return frequencies, amplitudes

# Initialize variables
running_means = np.zeros(num_bins)
smoothing_factor = 0.03
dynamic_ceiling = 0
max_activation_count = 100  # Adjust as needed
activation_counts = np.zeros(num_bins)

# Function to update running mean
def update_running_mean(bin, amplitude):
    global running_means, activation_counts
    activation_counts[bin] += 1
    dynamic_smoothing_factor = smoothing_factor * max_activation_count / (activation_counts[bin] + max_activation_count)
    running_means[bin] = (1 - dynamic_smoothing_factor) * running_means[bin] + dynamic_smoothing_factor * amplitude
    print(f"Running means {running_means}")

last_update_time = time.time()
decay_rate = 0.97  # More aggressive decay
max_ceiling = 100  # Upper limit
reset_time = 1  # Time in seconds to reset the dynamic ceiling

# Function to update dynamic ceiling
def update_dynamic_ceiling(amplitude):
    global dynamic_ceiling, last_update_time
    start_time = time.time()

    # print(f"amplitude: {amplitude}")

    current_time = time.time()

    # Decay the dynamic ceiling over time
    time_diff = current_time - last_update_time
    decay_factor = decay_rate ** time_diff
    dynamic_ceiling *= decay_factor
    
    # Update the dynamic ceiling if a louder sound is encountered
    dynamic_ceiling = max(min(max_ceiling, amplitude), dynamic_ceiling)
    
    # Reset the dynamic ceiling if no loud sound has been encountered for 'reset_time' seconds
    if current_time - last_update_time > reset_time:
        dynamic_ceiling = 0
    
    last_update_time = current_time

    print(f"dynamic_ceiling: {dynamic_ceiling}")

    end_time = time.time()
    # print(f"Time taken for update_dynamic_ceiling: {end_time - start_time} seconds")

# Modified bin_and_map function
def bin_and_map(frequencies, amplitudes, num_bins):
    global running_means, dynamic_ceiling
    bin_edges = np.linspace(300, 7500, num_bins + 1)  # Frequency range of 300 to 7500 Hz
    # bin_edges = np.linspace(frequencies.min(), frequencies.max(), num_bins + 1)  # Frequency range of 300 to 7500 Hz
    bins = np.digitize(frequencies, bin_edges)
    selected_bin = -1
    max_amplitude = 0

    for i in range(num_bins):
        indices = np.where(bins == i+1)[0]
        bin_amplitudes = amplitudes[indices]
        # print(f"Running means: {running_means} seconds")
        if bin_amplitudes.size > 0:
            max_bin_amplitude = bin_amplitudes.max()
            if max_bin_amplitude > running_means[i]:  # 20 dB SPL threshold
                if max_bin_amplitude > max_amplitude:
                    max_amplitude = max_bin_amplitude
                    selected_bin = i
    print(f"Selected bin: {selected_bin} bin")
    
    if selected_bin != -1:
        update_running_mean(selected_bin, max_amplitude)
        update_dynamic_ceiling(max_amplitude)
        intensity = (max_amplitude - running_means[selected_bin]) / (dynamic_ceiling - running_means[selected_bin])
        intensity = intensity ** 0.5  # Apply exponential scaling
        motor_number = selected_bin  # Directly map the selected bin to a motor
        executor.submit(control_motor, motor_number, intensity)  # Run control_motor on its own thread

audio_queue = queue.Queue()
# Function to play audio from the queue
def play_audio_from_queue():
    while True:
        audio_chunk = audio_queue.get()
        if audio_chunk is None:
            break
        try:
            sd.play(audio_chunk, samplerate=sample_rate, blocksize=2048)
            sd.wait()
        except Exception as e:
            print(f"Audio playback error: {e}")

audio_buffer = np.array([])
buffer_lock = Lock()
chunk_samples = None
def callback(indata, frames, time, status):
    global audio_buffer
    audio_data = indata[:, 0]
    # Append incoming audio data to the buffer
    audio_buffer = np.concatenate((audio_buffer, audio_data))
    
    # Check if the buffer has enough data for a chunk
    while len(audio_buffer) >= chunk_samples:
        # Extract chunk and remove it from buffer
        audio_chunk = audio_buffer[:chunk_samples]
        audio_buffer = audio_buffer[chunk_samples:]
        
        # Process the chunk
        if args.output:
            audio_queue.put(audio_chunk)
        
        frequencies, amplitudes = apply_fourier_transform(audio_chunk)
        bin_and_map(frequencies, amplitudes, num_bins)

def select_audio_devices():
    device_count = len(sd.query_devices())
    print(f"Number of devices: {device_count}")
    for i in range(device_count):
        dev = sd.query_devices(i)
        print(f"{i}: {dev['name']} (Max input channels: {dev['max_input_channels']}, Max output channels: {dev['max_output_channels']})")

    # Select a device for input
    input_device_index = int(input("Select a device index for input: "))
    
    if input_device_index >= device_count:
        print("Invalid input device index.")
        return None, None, None
    
    # Get sample rate of the selected input device
    input_dev_info = sd.query_devices(input_device_index)
    input_sample_rate = input_dev_info['default_samplerate']
    input_channels = max(1, input_dev_info['max_input_channels'])
    
    # Select a device for output
    output_device_index = int(input("Select a device index for output: "))
    
    if output_device_index >= device_count:
        print("Invalid output device index.")
        return None, None, None

    return input_device_index, output_device_index, input_sample_rate, input_channels

# Main loop
try:
  # Start the audio playback thread
  audio_thread = Thread(target=play_audio_from_queue,)
  audio_thread.start()
  if filename:  # If filename is provided, play the audio file
      sample_rate = get_sample_rate_from_file(f'./piper/output/{filename}')
      chunk_size = int(sample_rate * chunk_duration)
      for audio_chunk in read_audio_data(f'./piper/output/{filename}', chunk_size):
          start_time = time.time()

          audio_data = audio_chunk

          if args.output:
              audio_queue.put(audio_data)

          frequencies, amplitudes = apply_fourier_transform(audio_data)
          bin_and_map(frequencies, amplitudes, num_bins)

          end_time = time.time()
          processing_time = end_time - start_time
          
          time.sleep(chunk_duration)  # Wait for the duration of the audio chunk
          chunk_size = int(sample_rate * chunk_duration)
  else:  # If filename is not provided, use the microphone
      input_device_index, output_device_index, sample_rate, input_channels = select_audio_devices()
      if input_device_index is not None and output_device_index is not None:
          chunk_samples = int(chunk_duration * sample_rate)
          print(f"Using {input_channels} input channels and {sample_rate} Hz sample rate.")
          with sd.InputStream(device=input_device_index, channels=1, samplerate=sample_rate, callback=callback):
              print("Press Ctrl+C to stop")
              while True:
                  time.sleep(chunk_duration)
                  pass
  # Remember to cleanup GPIO settings after use
except KeyboardInterrupt:
    pass
finally:  
    for pwm in pwms:
        pwm.stop()
    GPIO.cleanup()
    audio_queue.put(None)
    audio_thread.join()