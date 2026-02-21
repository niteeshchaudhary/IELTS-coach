"""
Pause Detection State Machine.

Detects when the user has finished speaking by monitoring silence duration.
Implements debouncing to filter out brief pauses within speech.

State flow:
    SILENCE → SPEECH_STARTED → SPEAKING → MAYBE_DONE → TURN_COMPLETE
                                    ↑          ↓
                                    └──────────┘  (speech resumes)
"""

import time
from enum import Enum, auto
from typing import Optional, Callable

import config


class PauseState(Enum):
    """States of the pause detection state machine."""
    SILENCE = auto()          # No speech detected
    SPEECH_STARTED = auto()   # Speech began, but not yet confirmed (debouncing)
    SPEAKING = auto()         # Confirmed active speech
    MAYBE_DONE = auto()       # Silence detected after speech — waiting for threshold
    TURN_COMPLETE = auto()    # User has finished speaking


class PauseDetector:
    """
    Finite state machine for detecting end-of-turn pauses.

    Monitors VAD results and transitions between states:
    - Filters out brief noise/coughs via debouncing (VAD_MIN_SPEECH_MS)
    - Detects true end-of-turn via configurable silence threshold (PAUSE_THRESHOLD_MS)
    - Reports state changes via callbacks
    """

    def __init__(
        self,
        pause_threshold_ms: int = config.PAUSE_THRESHOLD_MS,
        min_speech_ms: int = config.VAD_MIN_SPEECH_MS,
        chunk_ms: int = config.AUDIO_CHUNK_MS,
        on_speech_start: Optional[Callable] = None,
        on_turn_complete: Optional[Callable] = None,
    ):
        self.pause_threshold_chunks = int(pause_threshold_ms / chunk_ms)
        self.min_speech_chunks = int(min_speech_ms / chunk_ms)
        self.chunk_ms = chunk_ms

        # Callbacks
        self.on_speech_start = on_speech_start
        self.on_turn_complete = on_turn_complete

        # State
        self._state = PauseState.SILENCE
        self._speech_chunk_count = 0
        self._silence_chunk_count = 0
        self._speech_start_time: Optional[float] = None

    @property
    def state(self) -> PauseState:
        return self._state

    @property
    def is_user_speaking(self) -> bool:
        return self._state in (PauseState.SPEECH_STARTED, PauseState.SPEAKING)

    @property
    def speech_duration_ms(self) -> float:
        """Duration of current speech segment in milliseconds."""
        if self._speech_start_time is None:
            return 0.0
        return (time.time() - self._speech_start_time) * 1000

    def process(self, is_speech: bool) -> PauseState:
        """
        Feed one VAD result (per chunk) and return current state.

        Args:
            is_speech: True if VAD detected speech in this chunk

        Returns:
            Current PauseState after processing
        """
        if self._state == PauseState.SILENCE:
            if is_speech:
                self._state = PauseState.SPEECH_STARTED
                self._speech_chunk_count = 1
                self._silence_chunk_count = 0

        elif self._state == PauseState.SPEECH_STARTED:
            if is_speech:
                self._speech_chunk_count += 1
                if self._speech_chunk_count >= self.min_speech_chunks:
                    # Enough continuous speech — confirmed real speech
                    self._state = PauseState.SPEAKING
                    self._speech_start_time = time.time()
                    if self.on_speech_start:
                        self.on_speech_start()
            else:
                # Speech stopped before reaching threshold — just noise
                self._state = PauseState.SILENCE
                self._speech_chunk_count = 0

        elif self._state == PauseState.SPEAKING:
            if is_speech:
                self._silence_chunk_count = 0
            else:
                self._silence_chunk_count = 1
                self._state = PauseState.MAYBE_DONE

        elif self._state == PauseState.MAYBE_DONE:
            if is_speech:
                # Speech resumed — user was just pausing mid-sentence
                self._state = PauseState.SPEAKING
                self._silence_chunk_count = 0
            else:
                self._silence_chunk_count += 1
                if self._silence_chunk_count >= self.pause_threshold_chunks:
                    # Enough silence — user is done speaking
                    self._state = PauseState.TURN_COMPLETE
                    if self.on_turn_complete:
                        self.on_turn_complete()

        elif self._state == PauseState.TURN_COMPLETE:
            # Stay in TURN_COMPLETE until explicitly reset
            pass

        return self._state

    def reset(self):
        """Reset to SILENCE state. Call after processing a completed turn."""
        self._state = PauseState.SILENCE
        self._speech_chunk_count = 0
        self._silence_chunk_count = 0
        self._speech_start_time = None

    def get_stats(self) -> dict:
        """Return current detector stats for debugging/UI."""
        return {
            "state": self._state.name,
            "speech_chunks": self._speech_chunk_count,
            "silence_chunks": self._silence_chunk_count,
            "speech_duration_ms": self.speech_duration_ms,
            "pause_threshold_chunks": self.pause_threshold_chunks,
            "min_speech_chunks": self.min_speech_chunks,
        }
