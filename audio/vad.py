"""
Silero VAD (Voice Activity Detection) wrapper.

Processes 30ms audio chunks and returns speech/silence classification.
Thread-safe for use in streamlit-webrtc callbacks.
"""

import threading
import numpy as np

import config


class VoiceActivityDetector:
    """Wrapper around Silero VAD for real-time speech detection."""

    def __init__(self, threshold: float = config.VAD_THRESHOLD):
        self.threshold = threshold
        self._model = None
        self._lock = threading.Lock()
        self._load_model()

    def _load_model(self):
        """Load Silero VAD model via torch.hub (downloaded on first run)."""
        import torch
        self._model, self._utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        self._model.eval()
        self._get_speech_timestamps = self._utils[0]

    def process_chunk(self, audio_chunk: np.ndarray) -> dict:
        """
        Process a single audio chunk and return VAD result.

        Args:
            audio_chunk: numpy array of audio samples (int16 or float32).
                         Expected length: config.AUDIO_CHUNK_SAMPLES (512 at 16kHz/32ms)

        Returns:
            dict with keys:
                - is_speech (bool): True if speech detected
                - confidence (float): Speech probability 0.0–1.0
        """
        import torch

        with self._lock:
            # Convert to float32 tensor normalized to [-1, 1]
            if audio_chunk.dtype == np.int16:
                audio_float = audio_chunk.astype(np.float32) / 32768.0
            elif audio_chunk.dtype == np.float32:
                audio_float = audio_chunk
            else:
                audio_float = audio_chunk.astype(np.float32)

            tensor = torch.from_numpy(audio_float)

            # Get speech probability
            speech_prob = self._model(tensor, config.AUDIO_SAMPLE_RATE).item()

            return {
                "is_speech": speech_prob >= self.threshold,
                "confidence": speech_prob,
            }

    def reset(self):
        """Reset VAD internal state (call between utterances)."""
        with self._lock:
            self._model.reset_states()
