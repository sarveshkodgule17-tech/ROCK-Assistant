import os
import time
import torch
import torchaudio
import pyaudio
import wave
import numpy as np
from speechbrain.inference.speaker import EncoderClassifier

# Ensure memory directory exists
os.makedirs("memory", exist_ok=True)

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 3

def record_audio(filename):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* Recording...")
    frames = []

    for i in range(0, int(RATE / CHANNELS / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* Done recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def enroll_voice():
    print("=========================================")
    print(" ROCK Voice Biometric Enrollment ")
    print("=========================================")
    print("I need to learn your voice to ensure only you can wake me.")
    print("You will be asked to say 'Hello ROCK' 3 times.")
    
    # Load SpeechBrain Encoder
    print("\nLoading speaker recognition model... (this may take a minute on first run)")
    classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", run_opts={"device":"cuda" if torch.cuda.is_available() else "cpu"})
    
    embeddings = []
    
    for i in range(3):
        input(f"\nPress Enter and say 'Hello ROCK' (Recording #{i+1})...")
        temp_file = f"temp_enroll_{i}.wav"
        record_audio(temp_file)
        
        # Extract embedding
        signal, fs = torchaudio.load(temp_file)
        # Ensure correct sample rate
        if fs != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=fs, new_freq=16000)
            signal = resampler(signal)
            
        with torch.no_grad():
            embedding = classifier.encode_batch(signal)
            embeddings.append(embedding.squeeze().cpu().numpy())
            
        os.remove(temp_file)
        print("Got it.")
        time.sleep(1)
        
    # Calculate average embedding
    avg_embedding = np.mean(embeddings, axis=0)
    
    # Save to disk
    profile_path = "memory/user_voice.npy"
    np.save(profile_path, avg_embedding)
    print(f"\nEnrollment complete! Voice print saved to {profile_path}.")
    print("ROCK is now locked to your voice.")

if __name__ == "__main__":
    enroll_voice()
