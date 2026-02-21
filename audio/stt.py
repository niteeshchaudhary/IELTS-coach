"""
Speech-to-Text using Faster-Whisper.

Transcribes accumulated audio when the pause detector signals TURN_COMPLETE.
Optimized for non-native English speakers with VAD pre-filtering.
"""

import io
import threading
from typing import Optional

import numpy as np

import config


class SpeechToText:
    """Faster-Whisper transcription engine."""

    def __init__(
        self,
        model_size: str = config.WHISPER_MODEL_SIZE,
        device: str = config.WHISPER_DEVICE,
        compute_type: str = config.WHISPER_COMPUTE_TYPE,
    ):
        self._model = None
        self._lock = threading.Lock()
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._load_model()

    def _load_model(self):
        """Load Faster-Whisper model (downloaded on first run)."""
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type,
        )

    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = config.AUDIO_SAMPLE_RATE,
    ) -> dict:
        """
        Transcribe audio data to text.

        Args:
            audio_data: numpy array of audio samples (int16 or float32)
            sample_rate: sample rate of the audio

        Returns:
            dict with keys:
                - text (str): Transcribed text
                - language (str): Detected language
                - confidence (float): Average transcription confidence
                - segments (list): Individual segment details
        """
        with self._lock:
            # Convert to float32 normalized to [-1, 1] if needed
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.float32:
                audio_float = audio_data
            else:
                audio_float = audio_data.astype(np.float32)

            # Transcribe with VAD filter
            segments, info = self._model.transcribe(
                audio_float,
                language=config.WHISPER_LANGUAGE,
                beam_size=config.WHISPER_BEAM_SIZE,
                vad_filter=config.WHISPER_VAD_FILTER,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200,
                ),
            )

            # Collect all segments
            segment_list = []
            full_text_parts = []
            total_confidence = 0.0
            segment_count = 0

            for segment in segments:
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "avg_logprob": segment.avg_logprob,
                    "no_speech_prob": segment.no_speech_prob,
                })
                full_text_parts.append(segment.text.strip())
                # Convert log probability to confidence
                import math
                total_confidence += math.exp(segment.avg_logprob)
                segment_count += 1

            full_text = " ".join(full_text_parts)
            avg_confidence = (total_confidence / segment_count) if segment_count > 0 else 0.0

            return {
                "text": full_text,
                "language": info.language,
                "confidence": avg_confidence,
                "segments": segment_list,
                "duration_seconds": info.duration,
            }

    def transcribe_stream(self, audio_data: np.ndarray) -> str:
        """
        Simple transcription that returns just the text.
        Convenience method for the conversation pipeline.
        """
        result = self.transcribe(audio_data)
        return result["text"]
