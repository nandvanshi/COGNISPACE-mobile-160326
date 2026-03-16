import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Textarea } from './ui/textarea';
import { Mic, MicOff, Loader2, Square } from 'lucide-react';

// Singleton pipeline loader
let pipelineInstance = null;
let pipelineLoading = false;
let pipelineLoadPromise = null;

const loadWhisperPipeline = async () => {
  if (pipelineInstance) return pipelineInstance;
  if (pipelineLoadPromise) return pipelineLoadPromise;

  pipelineLoading = true;
  pipelineLoadPromise = (async () => {
    try {
      const { pipeline } = await import('@xenova/transformers');
      pipelineInstance = await pipeline(
        'automatic-speech-recognition',
        'Xenova/whisper-tiny',
        { quantized: true }
      );
      return pipelineInstance;
    } catch (err) {
      console.error('Whisper load failed:', err);
      pipelineLoadPromise = null;
      throw err;
    } finally {
      pipelineLoading = false;
    }
  })();

  return pipelineLoadPromise;
};

const VoiceInputButton = ({ onTranscript, disabled, className = '' }) => {
  const [status, setStatus] = useState('idle'); // idle | loading | recording | transcribing
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setStatus('loading');

      // Start loading model and getting mic access in parallel
      const [_, stream] = await Promise.all([
        loadWhisperPipeline(),
        navigator.mediaDevices.getUserMedia({ audio: true })
      ]);

      streamRef.current = stream;
      chunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        streamRef.current = null;

        if (chunksRef.current.length === 0) {
          setStatus('idle');
          return;
        }

        setStatus('transcribing');
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
          const audioUrl = URL.createObjectURL(blob);

          const transcriber = await loadWhisperPipeline();
          const result = await transcriber(audioUrl, {
            language: 'en',
            task: 'transcribe',
          });

          URL.revokeObjectURL(audioUrl);

          if (result?.text?.trim()) {
            onTranscript(result.text.trim());
          }
        } catch (err) {
          console.error('Transcription error:', err);
        } finally {
          setStatus('idle');
        }
      };

      mediaRecorder.start(1000);
      setStatus('recording');
    } catch (err) {
      console.error('Recording error:', err);
      setStatus('idle');
      if (err.name === 'NotAllowedError') {
        alert('Microphone access denied. Please allow microphone access in browser settings.');
      }
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const handleClick = () => {
    if (status === 'recording') {
      stopRecording();
    } else if (status === 'idle') {
      startRecording();
    }
  };

  const isActive = status === 'recording';
  const isBusy = status === 'loading' || status === 'transcribing';

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled || isBusy}
      className={`inline-flex items-center justify-center rounded-md transition-all duration-200 ${
        isActive
          ? 'bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-200 animate-pulse'
          : isBusy
          ? 'bg-muted text-muted-foreground cursor-wait'
          : 'bg-primary/10 text-primary hover:bg-primary/20'
      } ${className}`}
      style={{ width: 32, height: 32, minWidth: 32 }}
      title={
        isActive ? 'Stop recording' :
        status === 'loading' ? 'Loading speech model...' :
        status === 'transcribing' ? 'Transcribing...' :
        'Voice input'
      }
      data-testid="voice-input-btn"
    >
      {status === 'loading' && <Loader2 size={15} className="animate-spin" />}
      {status === 'recording' && <Square size={13} fill="currentColor" />}
      {status === 'transcribing' && <Loader2 size={15} className="animate-spin" />}
      {status === 'idle' && <Mic size={15} />}
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
    // Simulate onChange event with appended text
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
    <div className="relative">
      <Textarea
        ref={ref}
        value={value}
        onChange={onChange}
        disabled={disabled}
        {...props}
      />
      {!disabled && (
        <div className="absolute bottom-2 right-2">
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
