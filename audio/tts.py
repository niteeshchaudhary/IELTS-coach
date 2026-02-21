"""
Text-to-Speech using Piper TTS.

Converts LLM text responses to natural-sounding speech audio.
Runs locally on CPU with low latency.
"""

import io
import subprocess
import threading
import wave
from typing import Optional

import numpy as np

import config


class TextToSpeech:
    """Piper TTS synthesis engine."""

    def __init__(
        self,
        model_name: str = config.PIPER_MODEL_NAME,
        speaker_id: int = config.PIPER_SPEAKER_ID,
        length_scale: float = config.PIPER_LENGTH_SCALE,
    ):
        self._model_name = model_name
        self._speaker_id = speaker_id
        self._length_scale = length_scale
        self._lock = threading.Lock()
        self._piper_available = self._check_piper()

    def _check_piper(self) -> bool:
        """Check if piper-tts is available."""
        try:
            import piper
            return True
        except ImportError:
            # Fall back to command-line piper or gTTS
            try:
                result = subprocess.run(
                    ["piper", "--help"],
                    capture_output=True,
                    timeout=5,
                )
                return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return False

    def synthesize(self, text: str) -> dict:
        """
        Convert text to speech audio.

        Args:
            text: Text to synthesize

        Returns:
            dict with keys:
                - audio_data (np.ndarray): Audio samples as int16
                - sample_rate (int): Sample rate of the audio
                - duration_seconds (float): Duration of the audio
        """
        if not text or not text.strip():
            return {
                "audio_data": np.array([], dtype=np.int16),
                "sample_rate": config.AUDIO_SAMPLE_RATE,
                "duration_seconds": 0.0,
            }

        with self._lock:
            if self._piper_available:
                return self._synthesize_piper(text)
            else:
                return self._synthesize_fallback(text)

    def _synthesize_piper(self, text: str) -> dict:
        """Synthesize using Piper TTS library."""
        try:
            import piper

            # Use piper Python API
            model_path = config.BASE_DIR / f"{self._model_name}.onnx"
            voice = piper.PiperVoice.load(str(model_path))
            from piper.config import SynthesisConfig

            # Configure speech parameters
            syn_config = SynthesisConfig(
                speaker_id=self._speaker_id,
                length_scale=self._length_scale,
                noise_scale=config.PIPER_NOISE_SCALE,
                noise_w_scale=config.PIPER_NOISE_W,
            )

            # Generate audio chunks
            chunks = voice.synthesize(text, syn_config=syn_config)
            
            # Combine chunks
            audio_data_list = []
            sample_rate = config.AUDIO_SAMPLE_RATE
            for chunk in chunks:
                sample_rate = chunk.sample_rate
                audio_data_list.append(chunk.audio_int16_array)

            if audio_data_list:
                audio_data = np.concatenate(audio_data_list)
            else:
                audio_data = np.array([], dtype=np.int16)

            duration = len(audio_data) / sample_rate

            return {
                "audio_data": audio_data,
                "sample_rate": sample_rate,
                "duration_seconds": duration,
            }

        except Exception as e:
            print(f"Piper TTS error: {e}, falling back to alternative")
            return self._synthesize_fallback(text)

    def _synthesize_fallback(self, text: str) -> dict:
        """
        Fallback TTS using gTTS (Google Text-to-Speech) for development.
        Not ideal for production but works without model downloads.
        """
        try:
            from gtts import gTTS
            from pydub import AudioSegment

            tts = gTTS(text=text, lang="en", slow=False)
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)

            # Convert MP3 to WAV
            audio_segment = AudioSegment.from_mp3(mp3_buffer)
            audio_segment = audio_segment.set_frame_rate(config.AUDIO_SAMPLE_RATE)
            audio_segment = audio_segment.set_channels(1)

            audio_data = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
            duration = len(audio_data) / config.AUDIO_SAMPLE_RATE

            return {
                "audio_data": audio_data,
                "sample_rate": config.AUDIO_SAMPLE_RATE,
                "duration_seconds": duration,
            }

        except ImportError:
            # Ultimate fallback — return silence with a warning
            print("WARNING: No TTS engine available. Install piper-tts or gTTS.")
            duration = 1.0
            silence = np.zeros(int(config.AUDIO_SAMPLE_RATE * duration), dtype=np.int16)
            return {
                "audio_data": silence,
                "sample_rate": config.AUDIO_SAMPLE_RATE,
                "duration_seconds": duration,
            }

    def synthesize_to_wav_bytes(self, text: str) -> bytes:
        """
        Synthesize text and return as WAV file bytes.
        Useful for Streamlit st.audio() playback.
        """
        result = self.synthesize(text)
        audio_data = result["audio_data"]
        sample_rate = result["sample_rate"]

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        return wav_buffer.getvalue()

    def synthesize_to_mp3_bytes(self, text: str) -> Optional[bytes]:
        """
        Synthesize text directly to MP3 bytes using gTTS.
        Much faster than synthesize_to_wav_bytes when Piper is unavailable,
        since it skips the MP3→WAV conversion entirely.
        Returns None if gTTS is not available.
        """
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang="en", slow=False)
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            return mp3_buffer.getvalue()
        except Exception:
            return None

    def synthesize_to_playable_bytes(self, text: str) -> tuple[bytes, str]:
        """
        Synthesize text and return audio bytes in the best available format.
        Returns (audio_bytes, mime_type) for use with st.audio().

        Tries in order:
        1. Piper TTS → WAV
        2. gTTS → MP3 (fast, no conversion needed)
        3. Silence WAV (last resort)
        """
        if not text or not text.strip():
            return b"", "audio/wav"

        # If Piper is available, use WAV path
        if self._piper_available:
            return self.synthesize_to_wav_bytes(text), "audio/wav"

        # Try gTTS → direct MP3 (no pydub/ffmpeg needed)
        mp3 = self.synthesize_to_mp3_bytes(text)
        if mp3:
            return mp3, "audio/mp3"

        # Last resort: silence WAV
        return self.synthesize_to_wav_bytes(text), "audio/wav"
