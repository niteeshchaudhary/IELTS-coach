"""
Conversation Memory Manager.

Maintains rolling context window, session state, and persistence
for cross-session continuity.
"""

import json
import sqlite3
import time
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field

import config


@dataclass
class Turn:
    """A single conversation turn."""
    role: str          # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class ConversationMemory:
    """
    Manages conversation context and history.

    Features:
    - Rolling context window (last N turns) for LLM prompts
    - Session state for current conversation
    - SQLite persistence for cross-session continuity
    - Vocabulary tracking integration
    """

    def __init__(
        self,
        max_turns: int = config.CONVERSATION_HISTORY_MAX_TURNS,
        db_path: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self._max_turns = max_turns
        self._turns: list[Turn] = []
        self._session_id = session_id if session_id else f"session_{int(time.time())}"
        self._db_path = db_path if db_path else str(config.get_db_path("default"))
        self._vocab_words: list[str] = []  # Today's vocabulary words

        # Initialize database
        self._init_db()
        
        # Load existing session if provided
        if session_id:
            self._load_session()

    def _load_session(self):
        """Load conversation history for the current session from database."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp, metadata FROM conversation_history WHERE session_id = ? ORDER BY timestamp ASC",
                (self._session_id,)
            )
            rows = cursor.fetchall()
            for row in rows:
                turn = Turn(
                    role=row[0],
                    content=row[1],
                    timestamp=row[2],
                    metadata=json.loads(row[3]) if row[3] else {}
                )
                self._turns.append(turn)
            conn.close()
            # Trim to max turns
            if len(self._turns) > self._max_turns:
                 self._turns = self._turns[-self._max_turns:]
        except Exception as e:
            print(f"Warning: Failed to load session: {e}")

    def _init_db(self):
        """Initialize SQLite database for persistence."""
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS session_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                summary TEXT NOT NULL,
                turn_count INTEGER DEFAULT 0,
                started_at DATETIME NOT NULL,
                ended_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS vocabulary_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                date_introduced TEXT NOT NULL,
                times_seen INTEGER DEFAULT 0,
                times_used_correctly INTEGER DEFAULT 0,
                times_used_incorrectly INTEGER DEFAULT 0,
                is_mastered BOOLEAN DEFAULT 0,
                last_seen_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(word, date_introduced)
            );

            CREATE TABLE IF NOT EXISTS daily_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                total_speaking_time_sec REAL DEFAULT 0,
                total_turns INTEGER DEFAULT 0,
                words_practiced INTEGER DEFAULT 0,
                estimated_band_score REAL,
                games_played INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_history(session_id);
            CREATE INDEX IF NOT EXISTS idx_vocab_word ON vocabulary_progress(word);
            CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_progress(date);
        """)

        conn.commit()
        conn.close()

    def add_turn(self, role: str, content: str, metadata: Optional[dict] = None):
        """
        Add a conversation turn.

        Args:
            role: "user" or "assistant"
            content: The turn content
            metadata: Optional metadata (e.g., confidence, vocab usage)
        """
        turn = Turn(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._turns.append(turn)

        # Trim to max turns
        if len(self._turns) > self._max_turns:
            self._turns = self._turns[-self._max_turns:]

        # Persist to database
        self._persist_turn(turn)

    def _persist_turn(self, turn: Turn):
        """Save a turn to SQLite."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO conversation_history
                   (session_id, role, content, timestamp, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    self._session_id,
                    turn.role,
                    turn.content,
                    turn.timestamp,
                    json.dumps(turn.metadata),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to persist turn: {e}")

    def get_context(self) -> list[dict]:
        """
        Get conversation context formatted for LLM.

        Returns:
            List of dicts with 'role' and 'content' keys,
            compatible with OpenAI chat format.
        """
        return [
            {"role": turn.role, "content": turn.content}
            for turn in self._turns
        ]

    def get_context_with_vocab(self) -> list[dict]:
        """
        Get conversation context with vocabulary reminders injected.

        Adds a system message about today's vocabulary words
        every REINFORCEMENT_INTERVAL_TURNS turns.
        """
        context = self.get_context()

        if self._vocab_words and len(self._turns) > 0:
            turn_count = len(self._turns)
            if turn_count % config.REINFORCEMENT_INTERVAL_TURNS == 0:
                vocab_reminder = (
                    f"[VOCABULARY REMINDER] Today's words: {', '.join(self._vocab_words)}. "
                    f"Try to naturally weave these into the conversation."
                )
                context.append({"role": "system", "content": vocab_reminder})

        return context

    def set_daily_vocab(self, words: list[str]):
        """Set today's vocabulary words for reinforcement."""
        self._vocab_words = words

    @property
    def turn_count(self) -> int:
        return len(self._turns)

    @property
    def last_user_text(self) -> str:
        """Get the last user turn text."""
        for turn in reversed(self._turns):
            if turn.role == "user":
                return turn.content
        return ""

    @property
    def last_assistant_text(self) -> str:
        """Get the last assistant turn text."""
        for turn in reversed(self._turns):
            if turn.role == "assistant":
                return turn.content
        return ""

    def get_session_summary(self) -> str:
        """Generate a summary of the current session for persistence."""
        if not self._turns:
            return "No conversation yet."

        user_turns = [t for t in self._turns if t.role == "user"]
        topics = set()
        for turn in user_turns[-5:]:
            # Simple topic extraction — just use first few words
            words = turn.content.split()[:5]
            topics.add(" ".join(words))

        return f"Session with {len(self._turns)} turns. Recent topics: {'; '.join(topics)}"

    def save_session(self):
        """Save session summary to database."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO session_summaries
                   (session_id, summary, turn_count, started_at, ended_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    self._session_id,
                    self.get_session_summary(),
                    len(self._turns),
                    datetime.fromtimestamp(self._turns[0].timestamp).isoformat()
                    if self._turns else datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to save session: {e}")

    def update_daily_progress(self, speaking_time_sec: float = 0, band_score: float = None, games_played: int = 0, add_turn: bool = True):
        """Update daily progress tracking."""
        try:
            today = date.today().isoformat()
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            turns_inc = 1 if add_turn else 0

            cursor.execute(
                """INSERT INTO daily_progress (date, total_speaking_time_sec, total_turns, games_played)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET
                       total_speaking_time_sec = total_speaking_time_sec + ?,
                       total_turns = total_turns + ?,
                       games_played = games_played + ?""",
                (today, speaking_time_sec, turns_inc, games_played, speaking_time_sec, turns_inc, games_played),
            )

            if band_score is not None:
                cursor.execute(
                    """UPDATE daily_progress SET estimated_band_score = ?
                       WHERE date = ?""",
                    (band_score, today),
                )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to update daily progress: {e}")

    def clear(self):
        """Clear current session memory (doesn't affect database)."""
        self._turns.clear()
