from pathlib import Path
from elevenlabs import ElevenLabs
from datetime import datetime
import json

class TranscriptionHandler:
    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)
        
    def transcribe_file(self, audio_path: Path, output_dir: Path = Path("transcriptions")) -> Path:
        """
        Transcribe an audio file using ElevenLabs and save the result.
        Returns the path to the saved transcription file.
        """
        output_dir.mkdir(exist_ok=True)
        
        # Read the audio file
        with open(audio_path, 'rb') as audio_file:
            # Call ElevenLabs API
            response = self.client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v1",
                language_code="en",  # or None for auto-detection
                diarize=True,        # Enable speaker detection
                tag_audio_events=True # Enable audio event detection
            )
            
        # Generate output filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_path = output_dir / f"transcription_{timestamp}.txt"
        json_path = output_dir / f"transcription_{timestamp}.json"
        
        # Save plain text transcription
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        # Save full response with metadata (speakers, timestamps, etc)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(response.dict(), f, indent=2)
            
        print(f"Saved transcription to {text_path}")
        print(f"Saved detailed data to {json_path}")
        
        return text_path