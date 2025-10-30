import pyaudio
import wave
import numpy as np
from skey import detect_key
import tempfile
import os
from collections import Counter

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 44100

# Accuracy settings
BUFFER_SECONDS = 15  # Longer analysis window for better accuracy
OVERLAP_SECONDS = 10  # How much to overlap between analyses
MAX_HISTORY = 3  # Number of recent predictions to smooth over

# Device setting
DEVICE = "cpu"

# Initialize
p = pyaudio.PyAudio()
recent_predictions = []

# Open stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print(f"Starting live key detection...")
print(f"- Buffer: {BUFFER_SECONDS} seconds")
print(f"- Overlap: {OVERLAP_SECONDS} seconds")
print(f"- Smoothing: last {MAX_HISTORY} predictions")
print(f"- Device: {DEVICE}")
print("Press Ctrl+C to stop\n")

# Pre-record buffer for overlap
overlap_frames = []

try:
    while True:
        frames = []
        
        # Add overlap from previous analysis
        if overlap_frames:
            frames.extend(overlap_frames)
        
        # Calculate how many new frames we need
        new_frames_needed = int(RATE / CHUNK * (BUFFER_SECONDS - OVERLAP_SECONDS)) if overlap_frames else int(RATE / CHUNK * BUFFER_SECONDS)
        
        # Record new audio
        for i in range(new_frames_needed):
            data = stream.read(CHUNK)
            frames.append(data)
        
        # Save overlap for next iteration
        overlap_frame_count = int(RATE / CHUNK * OVERLAP_SECONDS)
        overlap_frames = frames[-overlap_frame_count:]
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            
            wf = wave.open(temp_path, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
        
        # Detect key
        try:
            result = detect_key(temp_path, extension="wav", device=DEVICE)
            
            # Handle result - it might be a list or dict
            if isinstance(result, list):
                key_detected = result[0] if result else "Unknown"
            elif isinstance(result, dict):
                key_detected = result.get('key', 'Unknown')
            else:
                key_detected = str(result)
            
            # Add to history
            recent_predictions.append(key_detected)
            if len(recent_predictions) > MAX_HISTORY:
                recent_predictions.pop(0)
            
            # Get smoothed result (most common key in recent history)
            key_counts = Counter(recent_predictions)
            smoothed_key = key_counts.most_common(1)[0][0]
            confidence = key_counts.most_common(1)[0][1]
            
            # Convert Minors to relative Majors for simplicity
            case_map = {
                'A minor': 'C Major',
                'E minor': 'G Major',
                'B minor': 'D Major',
                'F# minor': 'A Major',
                'C# minor': 'E Major',
                'G# minor': 'B Major',
                'D# minor': 'F# Major',
                'A# minor': 'C# Major',
                'D minor': 'F Major',
                'G minor': 'Bb Major',
                'C minor': 'Eb Major',
                'F minor': 'Ab Major'
            }
            if smoothed_key in case_map:
                smoothed_key = case_map[smoothed_key]
            # Print results


            print(f"Raw detection: {key_detected}")
            print(f"Smoothed key: {smoothed_key} (confidence: {confidence}/{len(recent_predictions)})")
            print(f"Recent history: {recent_predictions}")
            print("-" * 50)
            
        except Exception as e:
            print(f"Error during detection: {e}")
        finally:
            # Clean up temp file
            os.unlink(temp_path)

except KeyboardInterrupt:
    print("\n\nStopping live key detection...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Done!")