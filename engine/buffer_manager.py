"""
Smart Response Buffer Manager.

Handles the critical UX feature of buffering AI responses when the user
is still speaking, then deciding whether to continue, drop, or merge
the buffered response based on relevance and freshness.
"""

import time
from enum import Enum, auto
from typing import Optional
from dataclasses import dataclass, field

import config


class BufferAction(Enum):
    """Actions the buffer manager can take."""
    CONTINUE = auto()   # Use the buffered response as-is
    MERGE = auto()      # Merge buffer with new user input context
    DROP = auto()       # Discard buffer, generate fresh response
    NONE = auto()       # No buffer exists


@dataclass
class BufferedResponse:
    """A response held in the buffer waiting for a decision."""
    text: str
    created_at: float = field(default_factory=time.time)
    context_summary: str = ""  # Summary of what the user said when this was generated
    relevance_score: Optional[float] = None

    @property
    def age_ms(self) -> float:
        """Age of the buffered response in milliseconds."""
        return (time.time() - self.created_at) * 1000

    @property
    def is_expired(self) -> bool:
        """Check if buffer has exceeded max age."""
        return self.age_ms > config.BUFFER_MAX_AGE_MS


class BufferManager:
    """
    Manages smart response buffering.

    When the AI prepares a response while the user is still speaking,
    this manager holds it and decides what to do when the user finishes:

    Decision Logic:
        1. If buffer is expired (> BUFFER_MAX_AGE_MS) → DROP
        2. If relevance < BUFFER_RELEVANCE_THRESHOLD → DROP
        3. If user changed topics → DROP
        4. If relevant and fresh → MERGE or CONTINUE

    Relevance is computed by the LLM (via llm_engine) comparing
    the buffered context with the new user input.
    """

    def __init__(self):
        self._buffer: Optional[BufferedResponse] = None
        self._decision_history: list[dict] = []

    @property
    def has_buffer(self) -> bool:
        return self._buffer is not None

    @property
    def current_buffer(self) -> Optional[BufferedResponse]:
        return self._buffer

    def store(self, response_text: str, context_summary: str = ""):
        """
        Store a response in the buffer.

        Args:
            response_text: The AI response to buffer
            context_summary: Summary of what the user was saying when generated
        """
        self._buffer = BufferedResponse(
            text=response_text,
            context_summary=context_summary,
        )

    def decide(
        self,
        new_user_input: str,
        relevance_score: Optional[float] = None,
        topic_changed: bool = False,
    ) -> tuple[BufferAction, Optional[BufferedResponse]]:
        """
        Decide what to do with the buffered response.

        Args:
            new_user_input: What the user actually said (full turn)
            relevance_score: How relevant the buffer is to new input (0.0–1.0)
                            If None, defaults to DROP for safety
            topic_changed: Whether the user changed topics

        Returns:
            Tuple of (action, buffered_response)
            - If DROP: buffered_response is the dropped response (for logging)
            - If MERGE/CONTINUE: buffered_response is what to use
            - If NONE: no buffer existed
        """
        if self._buffer is None:
            return (BufferAction.NONE, None)

        buffer = self._buffer
        action = BufferAction.DROP  # Default to safe option

        # Decision tree
        if buffer.is_expired:
            action = BufferAction.DROP
            reason = f"expired (age={buffer.age_ms:.0f}ms > {config.BUFFER_MAX_AGE_MS}ms)"

        elif topic_changed:
            action = BufferAction.DROP
            reason = "user changed topics"

        elif relevance_score is not None:
            buffer.relevance_score = relevance_score

            if relevance_score >= config.BUFFER_RELEVANCE_THRESHOLD:
                if config.BUFFER_MERGE_ENABLED:
                    action = BufferAction.MERGE
                    reason = f"relevant ({relevance_score:.2f}) — merging with new context"
                else:
                    action = BufferAction.CONTINUE
                    reason = f"relevant ({relevance_score:.2f}) — using as-is"
            else:
                action = BufferAction.DROP
                reason = f"low relevance ({relevance_score:.2f} < {config.BUFFER_RELEVANCE_THRESHOLD})"
        else:
            action = BufferAction.DROP
            reason = "no relevance score provided — dropping for safety"

        # Log the decision
        self._decision_history.append({
            "action": action.name,
            "reason": reason,
            "buffer_age_ms": buffer.age_ms,
            "relevance_score": relevance_score,
            "topic_changed": topic_changed,
            "timestamp": time.time(),
        })

        # Keep history bounded
        if len(self._decision_history) > 50:
            self._decision_history = self._decision_history[-25:]

        # Clear the buffer
        result_buffer = self._buffer
        self._buffer = None

        return (action, result_buffer)

    def clear(self):
        """Clear the buffer without making a decision."""
        self._buffer = None

    def get_status(self) -> dict:
        """Get buffer status for UI display."""
        if self._buffer is None:
            return {"has_buffer": False}
        return {
            "has_buffer": True,
            "age_ms": self._buffer.age_ms,
            "is_expired": self._buffer.is_expired,
            "context_preview": self._buffer.context_summary[:50] + "..."
            if len(self._buffer.context_summary) > 50
            else self._buffer.context_summary,
        }

    def get_decision_history(self) -> list[dict]:
        """Get recent buffer decisions for debugging."""
        return self._decision_history[-10:]
