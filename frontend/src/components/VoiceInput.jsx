import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

function VoiceInput({ onTranscript, disabled, apiUrl }) {
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [error, setError] = useState(null);
  const [useBackend, setUseBackend] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  useEffect(() => {
    // Try to use backend transcription first (better accuracy)
    // Fallback to Web Speech API if backend is not available
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';

      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        onTranscript(transcript);
        setIsListening(false);
      };

      recognitionInstance.onerror = (event) => {
        setError('Speech recognition error: ' + event.error);
        setIsListening(false);
      };

      recognitionInstance.onend = () => {
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
    }

    return () => {
      if (recognition) {
        recognition.stop();
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    };
  }, [onTranscript]);

  // Backend transcription using MediaRecorder API
  const startBackendRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        
        // Send to backend for transcription
        setIsTranscribing(true);
        try {
          const formData = new FormData();
          formData.append('audio_file', audioBlob, 'recording.webm');

          const response = await fetch(`${apiUrl || 'http://localhost:8000'}/api/transcribe-audio?language=en`, {
            method: 'POST',
            body: formData
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Transcription failed');
          }

          const data = await response.json();
          if (data.success && data.transcription) {
            onTranscript(data.transcription);
            setError(null);
          } else {
            throw new Error(data.error || 'Transcription failed');
          }
        } catch (err) {
          console.error('Backend transcription error:', err);
          setError(`Transcription error: ${err.message}. Using Web Speech API as fallback.`);
          // Fallback to Web Speech API if available
          if (recognition) {
            setUseBackend(false);
            startWebSpeechListening();
          }
        } finally {
          setIsTranscribing(false);
          setIsListening(false);
        }
      };

      mediaRecorder.start();
      setIsListening(true);
      setError(null);
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Could not access microphone. Using Web Speech API as fallback.');
      setIsListening(false);
      // Stop stream if it was created
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      // Fallback to Web Speech API if available
      if (recognition) {
        setUseBackend(false);
        startWebSpeechListening();
      }
    }
  };

  // Web Speech API transcription (fallback)
  const startWebSpeechListening = () => {
    if (recognition && !disabled) {
      setError(null);
      setIsListening(true);
      try {
        recognition.start();
      } catch (err) {
        console.error('Error starting recognition:', err);
        setError('Could not start voice recognition');
        setIsListening(false);
      }
    }
  };

  const startListening = () => {
    if (disabled) return;
    
    // Prefer backend transcription if API URL is available
    if (apiUrl) {
      setUseBackend(true);
      startBackendRecording();
    } else if (recognition) {
      // Fallback to Web Speech API
      setUseBackend(false);
      startWebSpeechListening();
    } else {
      setError('Voice input not available');
    }
  };

  const stopListening = () => {
    if (useBackend && mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    } else if (recognition) {
      try {
        recognition.stop();
      } catch (err) {
        console.error('Error stopping recognition:', err);
      }
    }
    setIsListening(false);
  };

  if (error && !recognition) {
    return (
      <div className="text-xs text-gray-500">
        Voice input not available
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      <motion.button
        type="button"
        onClick={isListening ? stopListening : startListening}
        disabled={disabled || !recognition}
        whileHover={{ scale: recognition && !disabled ? 1.1 : 1 }}
        whileTap={{ scale: recognition && !disabled ? 0.9 : 1 }}
        className={`p-2 rounded-full transition-all ${
          isListening
            ? 'bg-red-500 text-white animate-pulse'
            : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        title={isListening ? 'Stop listening' : 'Start voice input'}
      >
        {isListening ? (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4a1 1 0 11-2 0V7zM12 9a1 1 0 10-2 0v3a1 1 0 102 0V9z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        )}
      </motion.button>
      {isListening && !isTranscribing && (
        <span className="text-xs text-gray-600 animate-pulse">Listening...</span>
      )}
      {isTranscribing && (
        <span className="text-xs text-blue-600 animate-pulse">Transcribing...</span>
      )}
      {error && (
        <span className="text-xs text-red-500">{error}</span>
      )}
    </div>
  );
}

export default VoiceInput;

