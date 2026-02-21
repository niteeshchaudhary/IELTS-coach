"""
Conversation State Machine.

Master orchestrator for the entire conversation flow.
Manages transitions between IDLE, LISTENING, PROCESSING, SPEAKING, and BUFFERING states.
"""

from enum import Enum, auto
from typing import Optional
import time


class ConversationState(Enum):
    """States of the conversation flow."""
    IDLE = auto()          # App loaded, waiting for user to start
    LISTENING = auto()     # Mic active, VAD running, collecting user speech
    PROCESSING = auto()    # Transcribing + generating LLM response
    SPEAKING = auto()      # Playing TTS audio
    BUFFERING = auto()     # AI has response but user is still speaking — hold it


# Valid state transitions
_VALID_TRANSITIONS = {
    ConversationState.IDLE: {ConversationState.LISTENING},
    ConversationState.LISTENING: {ConversationState.PROCESSING, ConversationState.IDLE},
    ConversationState.PROCESSING: {ConversationState.SPEAKING, ConversationState.LISTENING},
    ConversationState.SPEAKING: {ConversationState.LISTENING, ConversationState.BUFFERING, ConversationState.IDLE},
    ConversationState.BUFFERING: {ConversationState.PROCESSING, ConversationState.LISTENING},
}


class ConversationStateMachine:
    """
    Finite state machine managing the conversation lifecycle.

    State transitions:
        IDLE → LISTENING           (user opens mic)
        LISTENING → PROCESSING     (pause detected → turn complete)
        PROCESSING → SPEAKING      (LLM response ready, TTS starts)
        SPEAKING → LISTENING       (TTS playback complete)
        SPEAKING → BUFFERING       (user speaks during AI playback)
        BUFFERING → PROCESSING     (user turn complete, merge buffers)
    """

    def __init__(self):
        self._state = ConversationState.IDLE
        self._state_enter_time = time.time()
        self._transition_history: list[dict] = []

    @property
    def state(self) -> ConversationState:
        return self._state

    @property
    def state_duration_ms(self) -> float:
        """How long we've been in the current state (ms)."""
        return (time.time() - self._state_enter_time) * 1000

    def transition_to(self, new_state: ConversationState) -> bool:
        """
        Attempt a state transition.

        Args:
            new_state: The target state

        Returns:
            True if transition was valid and executed, False otherwise

        Raises:
            ValueError: If the transition is not valid from the current state
        """
        if new_state not in _VALID_TRANSITIONS.get(self._state, set()):
            raise ValueError(
                f"Invalid transition: {self._state.name} → {new_state.name}. "
                f"Valid targets: {[s.name for s in _VALID_TRANSITIONS.get(self._state, set())]}"
            )

        old_state = self._state
        self._state = new_state
        self._state_enter_time = time.time()

        self._transition_history.append({
            "from": old_state.name,
            "to": new_state.name,
            "timestamp": self._state_enter_time,
        })

        # Keep history bounded
        if len(self._transition_history) > 100:
            self._transition_history = self._transition_history[-50:]

        return True

    def can_transition_to(self, target: ConversationState) -> bool:
        """Check if a transition to the target state is valid."""
        return target in _VALID_TRANSITIONS.get(self._state, set())

    # ── Convenience transition methods ──

    def start_listening(self):
        """User begins speaking / mic activated."""
        self.transition_to(ConversationState.LISTENING)

    def start_processing(self):
        """User turn complete, begin transcription + LLM."""
        self.transition_to(ConversationState.PROCESSING)

    def start_speaking(self):
        """LLM response ready, begin TTS playback."""
        self.transition_to(ConversationState.SPEAKING)

    def start_buffering(self):
        """User interrupted — hold AI response."""
        self.transition_to(ConversationState.BUFFERING)

    def back_to_listening(self):
        """Return to listening after speaking or from idle."""
        self.transition_to(ConversationState.LISTENING)

    def back_to_idle(self):
        """Return to idle state."""
        self.transition_to(ConversationState.IDLE)

    def reset(self):
        """Hard reset to IDLE state (bypasses transition validation)."""
        self._state = ConversationState.IDLE
        self._state_enter_time = time.time()
        self._transition_history.clear()

    def get_status(self) -> dict:
        """Get status for UI display."""
        state_labels = {
            ConversationState.IDLE: "Ready to start",
            ConversationState.LISTENING: "🎙️ Listening...",
            ConversationState.PROCESSING: "🧠 Thinking...",
            ConversationState.SPEAKING: "🔊 Speaking...",
            ConversationState.BUFFERING: "⏸️ Waiting for you to finish...",
        }
        return {
            "state": self._state.name,
            "label": state_labels.get(self._state, ""),
            "duration_ms": self.state_duration_ms,
            "transitions": len(self._transition_history),
        }
