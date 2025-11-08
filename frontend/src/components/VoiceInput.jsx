import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

function VoiceInput({ onTranscript, disabled }) {
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
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
    } else {
      setError('Speech recognition not supported in this browser');
    }

    return () => {
      if (recognition) {
        recognition.stop();
      }
    };
  }, [onTranscript]);

  const startListening = () => {
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

  const stopListening = () => {
    if (recognition) {
      try {
        recognition.stop();
      } catch (err) {
        console.error('Error stopping recognition:', err);
      }
      setIsListening(false);
    }
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
      {isListening && (
        <span className="text-xs text-gray-600 animate-pulse">Listening...</span>
      )}
      {error && recognition && (
        <span className="text-xs text-red-500">{error}</span>
      )}
    </div>
  );
}

export default VoiceInput;

