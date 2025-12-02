import pyaudio
import wave
import numpy as np
from skey import detect_key
import tempfile
import os
from collections import Counter
import serial
import time

arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)

def detect_key_live():
    # Audio settings
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1  # Mono
    RATE = 44100

    # Accuracy settings
    BUFFER_SECONDS = 15
    OVERLAP_SECONDS = 10
    MAX_HISTORY = 3
    
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
                
                 # Convert flat keys to sharp equivalents for simplicity
                case_map = {
                    'Ab Major': 'G# Major',
                    'Bb Major': 'A# Major',
                    'Cb Major': 'B Major',
                    'Db Major': 'C# Major',
                    'Eb Major': 'D# Major',
                    'Fb Major': 'E Major',
                    'Gb Major': 'F# Major'
                }
                if key_detected in case_map:
                    key_detected = case_map[key_detected]
                # Convert minor keys to major equivalents for simplicity
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
                    'G minor': 'A# Major',
                    'C minor': 'D# Major',
                    'F minor': 'G# Major'
                }
                if key_detected in case_map:
                    key_detected = case_map[key_detected]
                
                # Add to history
                recent_predictions.append(key_detected)
                if len(recent_predictions) > MAX_HISTORY:
                    recent_predictions.pop(0)
                
                # Get smoothed result (most common key in recent history)
                key_counts = Counter(recent_predictions)
                smoothed_key = key_counts.most_common(1)[0][0]
                confidence = key_counts.most_common(1)[0][1]
                
                # Format key for Arduino (remove " Major", convert "b" to "#")
                arduino_key = smoothed_key.replace(" Major", "")
                
                # Send to Arduino
                arduino.write((arduino_key + '\n').encode())
                
                # Print results
                print(f"Raw detection: {key_detected}")
                print(f"Smoothed key: {smoothed_key} (confidence: {confidence}/{len(recent_predictions)})")
                print(f"Sent to Arduino: {arduino_key}")
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

# Run the detection
detect_key_live()
