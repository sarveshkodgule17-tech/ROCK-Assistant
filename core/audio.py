import os
import pvporcupine
import struct
import pyaudio
import numpy as np
import pyttsx3
import speech_recognition as sr
import whisper
import torch
import torchaudio
from speechbrain.inference.speaker import EncoderClassifier
from dotenv import load_dotenv
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

load_dotenv()

class AudioCore:
    def __init__(self):
        print("[System] Initializing ROCK Audio Core...")
        self.volume_control = None
        self.was_muted = False
        
        # 1. TTS Setup
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170) # Slightly faster, confident pace
        
        # 2. Whisper STT Setup
        print("[System] Loading Whisper model (Base)...")
        # Base model is fast enough for RTX 3050 and accurate enough.
        self.whisper_model = whisper.load_model("base", device="cuda" if torch.cuda.is_available() else "cpu")
        self.recognizer = sr.Recognizer()
        
        # 3. Speaker Verification Setup
        self.voice_profile_path = "memory/user_voice.npy"
        self.has_voice_profile = os.path.exists(self.voice_profile_path)
        if self.has_voice_profile:
            self.user_embedding = np.load(self.voice_profile_path)
            self.spk_classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb", 
                run_opts={"device":"cuda" if torch.cuda.is_available() else "cpu"}
            )
        else:
            print("[Warning] No voice profile found. Anyone can wake me.")
            
        # 4. Wake Word Setup
        try:
            picovoice_key = os.environ.get("PICOVOICE_API_KEY")
            if not picovoice_key or picovoice_key == "your_api_key_here":
                raise ValueError("No valid Picovoice key")
            # We use the default 'computer' or 'jarvis' or 'porcupine' wake words 
            # if a custom 'rock' model isn't provided. For now, let's use 'jarvis' as a placeholder 
            # until you train a custom 'rock' wake word in the Picovoice Console.
            self.porcupine = pvporcupine.create(access_key=picovoice_key, keywords=['jarvis'])
            self.use_porcupine = True
        except Exception as e:
            print(f"[Warning] Porcupine Wake Word Engine not available ({e}). Using continuous fallback listening.")
            self.use_porcupine = False
            
    def speak(self, text):
        print(f"ROCK: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        
    def listen_for_command(self):
        """Listens for a command using SpeechRecognition and processes with Whisper."""
        with sr.Microphone(sample_rate=16000) as source:
            print("[System] Listening for command...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                # Save to temp file for Whisper and Speaker Verification
                with open("temp_cmd.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                    
                # Verify Speaker first
                if self.has_voice_profile:
                    if not self._verify_speaker("temp_cmd.wav"):
                        print("[Security] Voice unauthorized. Ignoring.")
                        os.remove("temp_cmd.wav")
                        return None
                        
                # If authorized, transcribe
                result = self.whisper_model.transcribe("temp_cmd.wav")
                text = result["text"].strip()
                os.remove("temp_cmd.wav")
                return text
                
            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                print(f"[Error] Audio Error: {e}")
                return None

    def _verify_speaker(self, wav_path):
        """Returns True if the voice matches the enrolled user."""
        import soundfile as sf
        data, fs = sf.read(wav_path)
        signal = torch.FloatTensor(data).unsqueeze(0)
        
        if fs != 16000:
            import torchaudio.transforms as T
            resampler = T.Resample(orig_freq=fs, new_freq=16000)
            signal = resampler(signal)
            
        with torch.no_grad():
            embedding = self.spk_classifier.encode_batch(signal).squeeze().cpu().numpy()
            
        # Cosine similarity
        cos_sim = np.dot(self.user_embedding, embedding) / (np.linalg.norm(self.user_embedding) * np.linalg.norm(embedding))
        print(f"[Security] Voice Match Confidence: {cos_sim:.2f}")
        
        # Threshold: 0.25 is usually a safe baseline for ECAPA-TDNN, but you can tune it.
        return cos_sim > 0.25
        
    def wait_for_wake_word(self):
        """Blocks until the wake word is detected."""
        if self.use_porcupine:
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length)
                
            print("\n[System] Waiting for Wake Word ('Jarvis' for now)...")
            try:
                while True:
                    pcm = audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    keyword_index = self.porcupine.process(pcm)
                    if keyword_index >= 0:
                        print("[Wake Word Detected]")
                        break
            finally:
                audio_stream.stop_stream()
                audio_stream.close()
                pa.terminate()
        else:
            # Fallback: continuous listening with Google STT (free, fast enough for wake word)
            print("\n[System] Waiting for Wake Word ('ROCK') via fallback engine...")
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                while True:
                    try:
                        audio = self.recognizer.listen(source, phrase_time_limit=3)
                        text = self.recognizer.recognize_google(audio).lower()
                        if "rock" in text or "atlas" in text:
                            print("[Wake Word Detected]")
                            break
                    except sr.UnknownValueError:
                        pass
                    except Exception as e:
                        print(f"Fallback wake word error: {e}")
                        break

    def mute_system(self):
        """Mutes system audio, remembering if it was already muted."""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_control = cast(interface, POINTER(IAudioEndpointVolume))
            self.was_muted = self.volume_control.GetMute()
            if not self.was_muted:
                print("[System Audio] Wake Word Detected. Muting system audio...")
                self.volume_control.SetMute(1, None)
        except Exception as e:
            print(f"[Warning] Failed to mute system audio: {e}")
            self.volume_control = None
            self.was_muted = False

    def unmute_system(self):
        """Restores system audio to its original state."""
        try:
            if self.volume_control and not self.was_muted:
                print("[System Audio] Restoring system audio...")
                self.volume_control.SetMute(0, None)
        except Exception as e:
            print(f"[Warning] Failed to unmute system audio: {e}")
