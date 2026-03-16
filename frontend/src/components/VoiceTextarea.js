import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Textarea } from './ui/textarea';
import { Mic, MicOff, Loader2, Square } from 'lucide-react';

// Check browser support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const VoiceInputButton = ({ onTranscript, disabled, className = '' }) => {
  const [status, setStatus] = useState('idle'); // idle | recording
  const recognitionRef = useRef(null);
  const transcriptRef = useRef('');

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }
    };
  }, []);

  const startRecording = useCallback(() => {
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      transcriptRef.current = '';

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-IN'; // English (India) - handles Indian accent well
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        let finalText = '';
        let interimText = '';
        for (let i = 0; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalText += result[0].transcript + ' ';
          } else {
            interimText += result[0].transcript;
          }
        }
        transcriptRef.current = finalText.trim();
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
          alert('Microphone access denied. Please allow microphone permission.');
        }
        setStatus('idle');
      };

      recognition.onend = () => {
        if (transcriptRef.current) {
          onTranscript(transcriptRef.current);
        }
        setStatus('idle');
      };

      recognition.start();
      setStatus('recording');
    } catch (err) {
      console.error('Speech recognition start error:', err);
      setStatus('idle');
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
  }, []);

  const handleClick = () => {
    if (status === 'recording') {
      stopRecording();
    } else {
      startRecording();
    }
  };

  if (!SpeechRecognition) return null;

  const isActive = status === 'recording';

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className={`inline-flex items-center justify-center rounded-md transition-all duration-200 ${
        isActive
          ? 'bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-200'
          : 'bg-primary/10 text-primary hover:bg-primary/20'
      } ${className}`}
      style={{ width: 32, height: 32, minWidth: 32 }}
      title={isActive ? 'Stop recording' : 'Voice input (Hindi/English)'}
      data-testid="voice-input-btn"
    >
      {isActive ? (
        <div className="relative">
          <Square size={12} fill="currentColor" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-white rounded-full animate-ping" />
        </div>
      ) : (
        <Mic size={15} />
      )}
    </button>
  );
};

// Drop-in replacement for Textarea with voice input
const VoiceTextarea = React.forwardRef(({ value, onChange, onVoiceTranscript, disabled, ...props }, ref) => {
  const handleTranscript = useCallback((text) => {
    if (onVoiceTranscript) {
      onVoiceTranscript(text);
      return;
    }
    const currentVal = value || '';
    const separator = currentVal && !currentVal.endsWith(' ') && !currentVal.endsWith('\n') ? ' ' : '';
    const newVal = currentVal + separator + text;

    if (onChange) {
      const syntheticEvent = {
        target: { value: newVal, name: props.name },
        currentTarget: { value: newVal, name: props.name },
      };
      onChange(syntheticEvent);
    }
  }, [value, onChange, onVoiceTranscript, props.name]);

  return (
    <div className="relative group">
      <Textarea
        ref={ref}
        value={value}
        onChange={onChange}
        disabled={disabled}
        {...props}
        style={{ ...(props.style || {}), paddingRight: disabled ? undefined : '40px' }}
      />
      {!disabled && SpeechRecognition && (
        <div className="absolute bottom-2 right-2 opacity-60 group-hover:opacity-100 transition-opacity">
          <VoiceInputButton
            onTranscript={handleTranscript}
            disabled={disabled}
          />
        </div>
      )}
    </div>
  );
});

VoiceTextarea.displayName = 'VoiceTextarea';

export { VoiceInputButton, VoiceTextarea };
export default VoiceTextarea;
