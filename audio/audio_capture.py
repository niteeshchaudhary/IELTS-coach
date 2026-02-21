"""
Real-time microphone capture using streamlit-webrtc.

Captures audio frames from the user's microphone via WebRTC,
feeds them through the VAD → Pause Detector pipeline, and
accumulates audio for transcription.
"""

import queue
import threading
import time
from typing import Optional

import numpy as np

try:
    import av
except ImportError:
    av = None

import config
from audio.vad import VoiceActivityDetector
from audio.pause_detector import PauseDetector, PauseState


class AudioBuffer:
    """Thread-safe buffer for accumulating audio frames during speech."""

    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()

    def add_frame(self, frame: np.ndarray):
        """Add an audio frame to the buffer."""
        with self._lock:
            self._frames.append(frame.copy())

    def get_audio(self) -> np.ndarray:
        """Get all accumulated audio as a single array."""
        with self._lock:
            if not self._frames:
                return np.array([], dtype=np.int16)
            return np.concatenate(self._frames)

    def clear(self):
        """Clear the buffer."""
        with self._lock:
            self._frames.clear()

    @property
    def duration_ms(self) -> float:
        """Approximate duration of buffered audio in milliseconds."""
        with self._lock:
            total_samples = sum(len(f) for f in self._frames)
            return (total_samples / config.AUDIO_SAMPLE_RATE) * 1000

    @property
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._frames) == 0


class AudioCapture:
    """
    Manages real-time audio capture and processing pipeline.

    Connects streamlit-webrtc audio frames to:
    1. VAD → detects speech vs silence
    2. PauseDetector → detects end-of-turn
    3. AudioBuffer → accumulates speech audio for STT

    Usage in Streamlit:
        capture = AudioCapture()

        webrtc_ctx = webrtc_streamer(
            key="mic",
            mode=WebRtcMode.SENDONLY,
            audio_frame_callback=capture.process_audio_frame,
            media_stream_constraints={"audio": True, "video": False},
        )

        # Check for completed turns
        if capture.has_completed_turn():
            audio = capture.get_turn_audio()
            transcription = stt.transcribe(audio)
    """

    def __init__(
        self,
        vad: Optional[VoiceActivityDetector] = None,
        pause_detector: Optional[PauseDetector] = None,
    ):
        self.vad = vad or VoiceActivityDetector()
        self.pause_detector = pause_detector or PauseDetector()

        self._audio_buffer = AudioBuffer()
        self._completed_turns: queue.Queue = queue.Queue()
        self._is_active = False

        # Status tracking for UI
        self._current_state = PauseState.SILENCE
        self._last_vad_confidence = 0.0

    def process_audio_frame(self, frame) -> Optional:
        """
        Process a single audio frame from streamlit-webrtc.

        This runs in the WebRTC callback thread — must be fast and thread-safe.

        Args:
            frame: av.AudioFrame from streamlit-webrtc

        Returns:
            The frame unchanged (passthrough for WebRTC)
        """
        if av is None:
            return frame

        # Convert av.AudioFrame to numpy array
        # to_ndarray() returns shape (channels, samples)
        audio_array = frame.to_ndarray()
        
        # Force mono by averaging channels if stereo
        if audio_array.ndim > 1 and audio_array.shape[0] > 1:
            audio_array = np.mean(audio_array, axis=0)
        else:
            audio_array = audio_array.flatten()

        # Resample to 16kHz if needed
        if frame.sample_rate != config.AUDIO_SAMPLE_RATE:
            audio_array = self._resample(
                audio_array, frame.sample_rate, config.AUDIO_SAMPLE_RATE
            )

        # Convert to int16 if float
        if audio_array.dtype in (np.float32, np.float64):
            audio_int16 = (audio_array * 32767).astype(np.int16)
        else:
            audio_int16 = audio_array.astype(np.int16)

        # Process in chunks of AUDIO_CHUNK_SAMPLES
        chunk_size = config.AUDIO_CHUNK_SAMPLES
        for i in range(0, len(audio_int16), chunk_size):
            chunk = audio_int16[i:i + chunk_size]
            if len(chunk) < chunk_size:
                # Pad short chunks with silence
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)))

            self._process_chunk(chunk)

        return frame

    def _process_chunk(self, chunk: np.ndarray):
        """Process a single audio chunk through VAD → PauseDetector → Buffer."""
        # Step 1: Voice Activity Detection
        vad_result = self.vad.process_chunk(chunk)
        self._last_vad_confidence = vad_result["confidence"]
        is_speech = vad_result["is_speech"]

        # Step 2: Pause Detection State Machine
        prev_state = self.pause_detector.state
        new_state = self.pause_detector.process(is_speech)
        self._current_state = new_state

        # Step 3: Buffer Management
        if new_state in (PauseState.SPEAKING, PauseState.MAYBE_DONE):
            # Accumulate audio during speech (including the silence gap in MAYBE_DONE)
            self._audio_buffer.add_frame(chunk)

        elif new_state == PauseState.TURN_COMPLETE:
            # User finished speaking — save the buffered audio
            if not self._audio_buffer.is_empty:
                completed_audio = self._audio_buffer.get_audio()
                self._completed_turns.put(completed_audio)
                self._audio_buffer.clear()

            # Reset for next turn
            self.pause_detector.reset()
            self.vad.reset()

        elif new_state == PauseState.SILENCE and prev_state == PauseState.SPEECH_STARTED:
            # False start (noise) — discard
            self._audio_buffer.clear()

    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        if orig_sr == target_sr:
            return audio
        try:
            from scipy.signal import resample
            num_samples = int(len(audio) * target_sr / orig_sr)
            return resample(audio, num_samples)
        except ImportError:
            # Simple linear interpolation fallback
            ratio = target_sr / orig_sr
            indices = np.arange(0, len(audio), 1 / ratio)
            indices = np.clip(indices.astype(int), 0, len(audio) - 1)
            return audio[indices]

    def has_completed_turn(self) -> bool:
        """Check if there's a completed user turn ready for processing."""
        return not self._completed_turns.empty()

    def get_turn_audio(self) -> Optional[np.ndarray]:
        """Get the audio from the next completed turn (or None if none available)."""
        try:
            return self._completed_turns.get_nowait()
        except queue.Empty:
            return None

    def get_status(self) -> dict:
        """Get current status for UI display."""
        return {
            "state": self._current_state.name,
            "vad_confidence": self._last_vad_confidence,
            "buffer_duration_ms": self._audio_buffer.duration_ms,
            "pending_turns": self._completed_turns.qsize(),
            "pause_stats": self.pause_detector.get_stats(),
        }

    def reset(self):
        """Full reset — clear all state."""
        self._audio_buffer.clear()
        self.pause_detector.reset()
        self.vad.reset()
        # Drain completed turns queue
        while not self._completed_turns.empty():
            try:
                self._completed_turns.get_nowait()
            except queue.Empty:
                break
