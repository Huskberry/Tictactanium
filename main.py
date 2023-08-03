import numpy as np
import threading
import librosa

# Define the number of bins (equal to the number of motors)
num_bins = 4

# Define the sample rate and duration for audio recording
sample_rate = 44100  # Standard for most microphones
duration = 1.0  # Duration in seconds

# Function to read audio data from a music file in chunks
def read_audio_data(file_path, chunk_size, overlap):
    audio_data, sample_rate = librosa.load(file_path, sr=None, mono=True)
    hop_size = chunk_size - overlap
    num_chunks = (len(audio_data) - overlap) // hop_size
    for i in range(num_chunks):
        start = i * hop_size
        end = start + chunk_size
        yield audio_data[start:end], sample_rate

# Function to apply Fourier Transform
def apply_fourier_transform(audio_data):
    frequencies = np.fft.rfftfreq(len(audio_data), 1.0 / sample_rate)
    amplitudes = np.abs(np.fft.rfft(audio_data))
    return frequencies, amplitudes

# Function to control a motor
def control_motor(motor_number, intensity):
    # Replace this with your own function to control the motors
    print(f"Motor {motor_number} vibrating with intensity {intensity}")

# Function to perform binning and map bins to motors
def bin_and_map(frequencies, amplitudes, num_bins):
    bin_edges = np.linspace(frequencies.min(), frequencies.max(), num_bins + 1)
    bins = np.digitize(frequencies, bin_edges)
    threads = []
    for i in range(num_bins):
        bin_amplitudes = amplitudes[bins == i]
        if bin_amplitudes.size > 0:
            intensity = bin_amplitudes.max() / amplitudes.max()
            # Create a new thread for each motor control call
            thread = threading.Thread(target=control_motor, args=(i, intensity))
            threads.append(thread)
            thread.start()
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

# Main loop
for audio_chunk in read_audio_data('path_to_your_music_file.mp3', chunk_size=44100, overlap=22050):
    # Read a chunk of audio data from a music file
    audio_data, sample_rate = audio_chunk

    # Apply Fourier Transform
    frequencies, amplitudes = apply_fourier_transform(audio_data)

    # Perform binning and map bins to motors
    bin_and_map(frequencies, amplitudes, num_bins)


