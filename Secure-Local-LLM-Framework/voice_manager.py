import pyaudio
import json
import os
import sys

# --- TRY IMPORTING VOSK ---
try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    print("CRITICAL: 'vosk' not installed. Run: pip install vosk")
    Model = None

# --- CONFIG ---
RATE = 16000 
CHUNK = 4096 

class VoiceManager:
    def __init__(self):
        self.model = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.frames = [] # RAM BUFFER

    def _load_model(self):
        if self.model is None:
            # Dynamic path finding for EXE support
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            possible_paths = [
                os.path.join(base_path, "assets", "model"),
                os.path.join("assets", "model"),
                "model"
            ]
            model_path = next((p for p in possible_paths if os.path.exists(p)), None)
            
            if not model_path:
                raise FileNotFoundError("Vosk model not found in assets/model")

            from vosk import SetLogLevel
            SetLogLevel(-1) # Silence logs
            self.model = Model(model_path)
            print("Vosk model loaded.")

    def start_recording(self):
        """Records audio to RAM (self.frames)."""
        self.frames = []
        self.is_recording = True
        
        try:
            self.stream = self.audio.open(format=pyaudio.paInt16, 
                                          channels=1, 
                                          rate=RATE, 
                                          input=True, 
                                          frames_per_buffer=CHUNK)
            
            print("Recording started (Vosk RAM Buffer)...")
            
            while self.is_recording:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
                
        except Exception as e:
            print(f"Microphone Error: {e}")
            self.is_recording = False

    def stop_recording(self):
        print("Stopping recording...")
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def save_and_transcribe(self):
        """Feeds the RAM buffer into Vosk."""
        if not self.frames:
            return False, "No audio data."

        try:
            self._load_model()
            rec = KaldiRecognizer(self.model, RATE)
            
            print(f"Processing {len(self.frames)} audio chunks...")
            
            # Feed all buffered frames to Vosk
            for data in self.frames:
                rec.AcceptWaveform(data)
            
            # Get the final result
            res = json.loads(rec.FinalResult())
            text = res.get("text", "")
            
            if not text:
                return False, "No speech detected."
                
            return True, text

        except Exception as e:
            return False, f"Error: {str(e)}"
