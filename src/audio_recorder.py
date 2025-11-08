import sounddevice as sd
import soundfile as sf
from pathlib import Path
from datetime import datetime
import wave
import numpy as np

class AudioRecorder:
    def __init__(self, output_dir: str = "recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Default audio parameters (these work well with ElevenLabs)
        self.sample_rate = 16000  # 16kHz
        self.channels = 1         # Mono
        
    def record(self, duration: float) -> Path:
        """
        Record audio for specified duration and save as WAV file.
        Returns the path to the saved file.
        """
        print(f"Recording for {duration} seconds...")
        
        # Record audio
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32'
        )
        sd.wait()  # Wait until recording is done
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"recording_{timestamp}.wav"
        
        # Save as WAV file
        sf.write(output_path, recording, self.sample_rate)
        print(f"Saved recording to {output_path}")
        
        return output_path