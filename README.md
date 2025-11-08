## Blockchain Voice – ElevenLabs Speech to Text

A Python application for real-time audio recording and transcription using ElevenLabs' Speech-to-Text API. The project features a modular architecture with separate components for audio recording and transcription handling.

### 1. Prerequisites

1. **ElevenLabs API Key**: Create an ElevenLabs API key (starts with `sk_...`) and store it in a `.env` file at the repository root:
   ```env
   ELEVENLABS_API_KEY=your_key_here
   ```

2. **Install Dependencies**: Install the required packages using pip (ideally inside a virtual environment):
   ```bash
   pip install -e .
   ```

### 2. Project Structure

```
Blockchain_voice/
├── src/
│   ├── audio_recorder.py       # Handles audio recording
│   └── transcription_handler.py # Manages ElevenLabs API calls
├── recordings/                  # Stores recorded audio files
├── transcriptions/              # Stores transcription outputs
├── main.py                      # Main application entry point
└── .env                         # API credentials
```

### 3. Usage

Run the application:
```bash
python main.py
```

The script will:
1. Prompt you to enter the recording duration in seconds
2. Record audio from your microphone
3. Automatically transcribe the audio using ElevenLabs
4. Save both the recording and transcription with timestamps
5. Display the transcription in the terminal

### 4. Features

- **Audio Recording**: Record audio from system microphone at 16kHz mono (optimized for speech)
- **Automatic Transcription**: Transcribe audio using ElevenLabs Scribe v1 model
- **Speaker Diarization**: Identify different speakers in the audio
- **Audio Event Detection**: Tag audio events like laughter and applause
- **Timestamped Output**: All recordings and transcriptions saved with timestamps
- **Dual Output Format**: Saves both plain text (.txt) and detailed JSON (.json) with metadata

### 5. Components

#### AudioRecorder (`src/audio_recorder.py`)
- Records audio from the default microphone
- Saves recordings as WAV files with timestamps
- Configured for 16kHz mono audio (optimal for speech recognition)

#### TranscriptionHandler (`src/transcription_handler.py`)
- Interfaces with ElevenLabs Speech-to-Text API
- Supports speaker diarization and audio event tagging
- Saves transcriptions in both text and JSON formats

### 6. Output Files

All files are automatically timestamped:
- **Recordings**: `recordings/recording_YYYYMMDD_HHMMSS.wav`
- **Transcriptions**:
  - `transcriptions/transcription_YYYYMMDD_HHMMSS.txt` (plain text)
  - `transcriptions/transcription_YYYYMMDD_HHMMSS.json` (with metadata)

### 7. Notes

- Audio is processed in-memory before sending to ElevenLabs API
- For very large audio files, consider implementing chunking or streaming
- Network access required for ElevenLabs API calls
- The application creates `recordings/` and `transcriptions/` directories automatically
