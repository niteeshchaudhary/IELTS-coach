"""
Turn Manager — Orchestrates natural turn-taking.

Coordinates pause detection, conversation state, buffer management,
and ensures the AI never interrupts the user.
"""

import time
import threading
from typing import Optional, Callable

import numpy as np

import config
from audio.audio_capture import AudioCapture
from audio.stt import SpeechToText
from audio.tts import TextToSpeech
from engine.conversation_state import ConversationStateMachine, ConversationState
from engine.buffer_manager import BufferManager, BufferAction
from engine.memory import ConversationMemory


class TurnManager:
    """
    Orchestrates the conversation turn-taking loop.

    Responsibilities:
    1. Polls AudioCapture for completed user turns
    2. Transcribes speech via STT
    3. Checks buffer for pending AI responses
    4. Generates new responses via LLM
    5. Synthesizes speech via TTS
    6. Adds natural delays before AI speaks

    The LLM engine is injected to avoid circular imports.
    """

    def __init__(
        self,
        audio_capture: AudioCapture,
        stt: SpeechToText,
        tts: TextToSpeech,
        state_machine: ConversationStateMachine,
        buffer_manager: BufferManager,
        memory: ConversationMemory,
        llm_generate: Optional[Callable] = None,
        llm_classify_relevance: Optional[Callable] = None,
        llm_merge_response: Optional[Callable] = None,
        on_transcription: Optional[Callable] = None,
        on_ai_response: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
    ):
        self.capture = audio_capture
        self.stt = stt
        self.tts = tts
        self.state = state_machine
        self.buffer = buffer_manager
        self.memory = memory

        # LLM functions (injected to avoid circular imports)
        self._llm_generate = llm_generate
        self._llm_classify_relevance = llm_classify_relevance
        self._llm_merge_response = llm_merge_response

        # UI callbacks
        self._on_transcription = on_transcription
        self._on_ai_response = on_ai_response
        self._on_state_change = on_state_change

        # Internal state
        self._is_running = False
        self._last_user_text = ""

    def process_turn(self) -> Optional[dict]:
        """
        Check for and process a completed user turn.

        This should be called periodically from the Streamlit main loop
        (e.g., in a st.empty() refresh cycle).

        Returns:
            dict with turn results if a turn was processed, None otherwise.
            Keys: user_text, ai_response, ai_audio_bytes, buffer_action
        """
        # Check if there's a completed turn from audio capture
        if not self.capture.has_completed_turn():
            return None

        audio_data = self.capture.get_turn_audio()
        if audio_data is None or len(audio_data) == 0:
            return None

        # Transition to PROCESSING
        try:
            self.state.start_processing()
            self._notify_state_change()
        except ValueError:
            # State transition not valid — likely already processing
            return None

        # Step 1: Transcribe the audio
        transcription = self.stt.transcribe(audio_data)
        user_text = transcription["text"].strip()

        if not user_text:
            # Empty transcription — go back to listening
            self.state.back_to_listening()
            self._notify_state_change()
            return None

        self._last_user_text = user_text
        if self._on_transcription:
            self._on_transcription(user_text, transcription)

        # Step 2: Check buffer for pending AI response
        buffer_action = BufferAction.NONE
        ai_response_text = ""

        if self.buffer.has_buffer:
            # Compute relevance of buffered response to new input
            relevance = 0.0
            topic_changed = False

            if self._llm_classify_relevance:
                relevance = self._llm_classify_relevance(
                    self.buffer.current_buffer.text,
                    user_text,
                )
                topic_changed = relevance < 0.3  # Low relevance = topic change

            action, buffered = self.buffer.decide(
                new_user_input=user_text,
                relevance_score=relevance,
                topic_changed=topic_changed,
            )
            buffer_action = action

            if action == BufferAction.MERGE and self._llm_merge_response and buffered:
                # Merge buffered response with new context
                ai_response_text = self._llm_merge_response(
                    buffered.text, user_text
                )
            elif action == BufferAction.CONTINUE and buffered:
                ai_response_text = buffered.text
            # else: DROP — generate fresh below

        # Step 3: Generate fresh response if needed
        if not ai_response_text and self._llm_generate:
            # Add user turn to memory
            self.memory.add_turn("user", user_text)

            # Generate response
            ai_response_text = self._llm_generate(
                user_text,
                self.memory.get_context(),
            )

        if ai_response_text:
            # Add AI turn to memory
            self.memory.add_turn("assistant", ai_response_text)

            if self._on_ai_response:
                self._on_ai_response(ai_response_text)

        # Step 4: Natural delay before speaking (feels more human)
        time.sleep(config.AI_RESPONSE_DELAY_MS / 1000)

        # Step 5: Synthesize speech
        ai_audio_bytes = None
        if ai_response_text:
            ai_audio_bytes = self.tts.synthesize_to_wav_bytes(ai_response_text)

            # Transition to SPEAKING
            try:
                self.state.start_speaking()
                self._notify_state_change()
            except ValueError:
                pass

        # After playback finishes, return to LISTENING
        # (The UI is responsible for transitioning after audio playback)

        return {
            "user_text": user_text,
            "ai_response": ai_response_text,
            "ai_audio_bytes": ai_audio_bytes,
            "buffer_action": buffer_action.name,
            "transcription_confidence": transcription.get("confidence", 0.0),
        }

    def finish_speaking(self):
        """Called by the UI when TTS playback completes."""
        try:
            self.state.back_to_listening()
            self._notify_state_change()
        except ValueError:
            pass

    def _notify_state_change(self):
        """Notify UI of state change."""
        if self._on_state_change:
            self._on_state_change(self.state.get_status())

    def get_status(self) -> dict:
        """Get full turn manager status for UI/debugging."""
        return {
            "conversation_state": self.state.get_status(),
            "audio_status": self.capture.get_status(),
            "buffer_status": self.buffer.get_status(),
            "memory_turns": self.memory.turn_count,
            "last_user_text": self._last_user_text[:50] + "..."
            if len(self._last_user_text) > 50
            else self._last_user_text,
        }
