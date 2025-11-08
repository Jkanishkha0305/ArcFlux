import os
from pathlib import Path
from dotenv import load_dotenv
from src.audio_recorder import AudioRecorder
from src.transcription_handler import TranscriptionHandler

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    # Create output directories
    recordings_dir = Path("recordings")
    transcriptions_dir = Path("transcriptions")
    recordings_dir.mkdir(exist_ok=True)
    transcriptions_dir.mkdir(exist_ok=True)
    
    # Initialize components
    recorder = AudioRecorder(output_dir=recordings_dir)
    transcriber = TranscriptionHandler(api_key=api_key)
    
    try:
        # Record audio (adjust duration as needed)
        duration = float(input("Enter recording duration in seconds: "))
        audio_path = recorder.record(duration)
        
        # Transcribe the recording
        transcription_path = transcriber.transcribe_file(
            audio_path, 
            output_dir=transcriptions_dir
        )
        
        # Print the transcription
        print("\nTranscription:")
        print("-" * 40)
        with open(transcription_path, 'r', encoding='utf-8') as f:
            print(f.read())
            
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()