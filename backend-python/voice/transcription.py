"""
Transcription handler using ElevenLabs API.
"""

from pathlib import Path
from typing import Optional, Dict
from elevenlabs import ElevenLabs
import tempfile
import os


class TranscriptionHandler:
    """Handle audio transcription using ElevenLabs API."""
    
    def __init__(self, api_key: str):
        """
        Initialize transcription handler.
        
        Args:
            api_key: ElevenLabs API key
        """
        self.client = ElevenLabs(api_key=api_key)
    
    def transcribe_file(self, audio_file: bytes, language: Optional[str] = "en") -> Dict:
        """
        Transcribe an audio file using ElevenLabs API.
        
        Args:
            audio_file: Audio file bytes (WAV, MP3, etc.)
            language: Language code (default: "en") or None for auto-detection
        
        Returns:
            Dictionary with transcription text and metadata:
            {
                "text": "transcribed text",
                "language": "en",
                "success": True
            }
        """
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_file)
                tmp_path = tmp_file.name
            
            try:
                # Read and transcribe the audio file
                with open(tmp_path, 'rb') as audio:
                    # Call ElevenLabs API
                    response = self.client.speech_to_text.convert(
                        file=audio,
                        model_id="scribe_v1",
                        language_code=language,  # or None for auto-detection
                        diarize=False,  # Disable speaker detection for simplicity
                        tag_audio_events=False  # Disable audio event detection for simplicity
                    )
                
                return {
                    "text": response.text,
                    "language": language or "auto",
                    "success": True
                }
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            return {
                "text": "",
                "language": language or "auto",
                "success": False,
                "error": str(e)
            }
    
    def transcribe_file_path(self, audio_path: Path, output_dir: Optional[Path] = None) -> Path:
        """
        Transcribe an audio file and save the result (legacy method for CLI).
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save transcription (optional)
        
        Returns:
            Path to saved transcription file
        """
        if output_dir is None:
            output_dir = Path("transcriptions")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Read the audio file
        with open(audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            result = self.transcribe_file(audio_bytes)
            
            if not result["success"]:
                raise Exception(f"Transcription failed: {result.get('error', 'Unknown error')}")
        
        # Generate output filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_path = output_dir / f"transcription_{timestamp}.txt"
        
        # Save plain text transcription
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(result["text"])
        
        return text_path

