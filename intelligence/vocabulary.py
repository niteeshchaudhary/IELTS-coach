"""
IELTS Vocabulary System.

Manages daily word selection, tracking, reinforcement scheduling,
and mastery progression.
"""

import json
import random
import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

import config


class VocabularySystem:
    """
    Daily IELTS vocabulary manager.

    Features:
    - Loads from curated word bank (ielts_vocabulary.json)
    - Selects N words daily (weighted by difficulty + user weakness)
    - Tracks exposure, correct uses, incorrect uses, mastery
    - Schedules reinforcement in conversations
    - Auto-generates more words using LLM if the bank is low
    """

    def __init__(self, db_path: str = str(config.DB_PATH), llm=None):
        self._db_path = db_path
        self._word_bank: list[dict] = []
        self._today_words: list[dict] = []
        self._llm = llm
        self._load_word_bank()

    def set_llm(self, llm):
        """Set LLM for dynamic generation."""
        self._llm = llm

    def _load_word_bank(self):
        """Load vocabulary from JSON file."""
        try:
            with open(config.VOCAB_JSON_PATH, "r") as f:
                self._word_bank = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Vocabulary file not found at {config.VOCAB_JSON_PATH}")
            self._word_bank = self._get_default_words()

    def _get_default_words(self) -> list[dict]:
        """Fallback vocabulary if JSON file is missing."""
        return [
            {
                "word": "ubiquitous",
                "band_level": 7,
                "topic": "technology",
                "meaning": "present, appearing, or found everywhere",
                "examples": [
                    "Smartphones have become ubiquitous in modern society.",
                    "The ubiquitous influence of social media affects all age groups.",
                ],
                "usage_notes": "Often used in IELTS essays about technology and society",
                "common_mistakes": "Don't confuse with 'unique'. Ubiquitous means everywhere, not one-of-a-kind.",
            },
            {
                "word": "prevalent",
                "band_level": 7,
                "topic": "health",
                "meaning": "widespread in a particular area or at a particular time",
                "examples": [
                    "Obesity is increasingly prevalent among young people.",
                    "This disease is most prevalent in tropical regions.",
                ],
                "usage_notes": "Good for discussing health, social issues, or trends",
                "common_mistakes": "Prevalent means widespread, not 'important'. It describes frequency, not significance.",
            },
            {
                "word": "advocate",
                "band_level": 6,
                "topic": "society",
                "meaning": "to publicly support or recommend (verb); a person who supports (noun)",
                "examples": [
                    "Many experts advocate for stricter environmental regulations.",
                    "She is a strong advocate of children's rights.",
                ],
                "usage_notes": "Can be used as verb ('advocate for') or noun ('an advocate of/for')",
                "common_mistakes": "As a verb, say 'advocate FOR something', not 'advocate something' in most cases.",
            },
            {
                "word": "mitigate",
                "band_level": 7,
                "topic": "environment",
                "meaning": "to make something less severe, serious, or painful",
                "examples": [
                    "Governments must take action to mitigate the effects of climate change.",
                    "The new policy aims to mitigate unemployment in rural areas.",
                ],
                "usage_notes": "High-band word perfect for discussing solutions to problems",
                "common_mistakes": "Mitigate means reduce severity, not eliminate entirely. Don't confuse with 'militate'.",
            },
            {
                "word": "exacerbate",
                "band_level": 8,
                "topic": "society",
                "meaning": "to make a problem, bad situation, or negative feeling worse",
                "examples": [
                    "The drought has exacerbated food shortages in the region.",
                    "Social media can exacerbate feelings of loneliness among teenagers.",
                ],
                "usage_notes": "The opposite of 'mitigate'. Great for discussing problems getting worse",
                "common_mistakes": "Pronounce: ig-ZAS-er-bate. Don't say 'exasperate' (which means to annoy).",
            },
            {
                "word": "paradigm",
                "band_level": 8,
                "topic": "education",
                "meaning": "a typical example or pattern of something; a model",
                "examples": [
                    "The internet has created a new paradigm for how we access information.",
                    "We need a paradigm shift in education to prepare students for the future.",
                ],
                "usage_notes": "'Paradigm shift' is a powerful IELTS phrase for discussing major changes",
                "common_mistakes": "Pronounce: PAR-a-dime, not PAR-a-dig-em.",
            },
            {
                "word": "facilitate",
                "band_level": 7,
                "topic": "education",
                "meaning": "to make an action or process easy or easier",
                "examples": [
                    "Technology has facilitated communication across borders.",
                    "The teacher's role is to facilitate learning, not just lecture.",
                ],
                "usage_notes": "Great alternative to 'make easier' or 'help'",
                "common_mistakes": "Facilitate takes a direct object: 'facilitate learning' not 'facilitate to learn'.",
            },
            {
                "word": "detrimental",
                "band_level": 7,
                "topic": "health",
                "meaning": "tending to cause harm; damaging",
                "examples": [
                    "Excessive screen time can be detrimental to children's development.",
                    "The policy change had a detrimental effect on small businesses.",
                ],
                "usage_notes": "Use 'detrimental to' — stronger than 'bad for'",
                "common_mistakes": "It's 'detrimental TO something', not 'detrimental FOR something'.",
            },
            {
                "word": "unprecedented",
                "band_level": 7,
                "topic": "society",
                "meaning": "never done or known before",
                "examples": [
                    "The pandemic caused unprecedented disruption to global economies.",
                    "We are living in an era of unprecedented technological change.",
                ],
                "usage_notes": "Powerful word for emphasizing how new/extreme something is",
                "common_mistakes": "Don't overuse. Reserve for truly unique situations.",
            },
            {
                "word": "resilient",
                "band_level": 7,
                "topic": "society",
                "meaning": "able to recover quickly from difficult conditions",
                "examples": [
                    "Children are often more resilient than adults give them credit for.",
                    "Building resilient communities is essential for disaster preparedness.",
                ],
                "usage_notes": "Can describe people, systems, economies, or communities",
                "common_mistakes": "Resilient means bouncing back, not just 'strong'. A brick wall is strong but not resilient.",
            },
            {
                "word": "substantial",
                "band_level": 6,
                "topic": "general",
                "meaning": "of considerable importance, size, or worth",
                "examples": [
                    "There has been a substantial increase in online shopping.",
                    "The government allocated substantial funds to healthcare.",
                ],
                "usage_notes": "Better than 'big' or 'a lot of' in academic contexts",
                "common_mistakes": "Substantial implies significance, not just physical size.",
            },
            {
                "word": "incentive",
                "band_level": 6,
                "topic": "economics",
                "meaning": "a thing that motivates or encourages someone to do something",
                "examples": [
                    "Tax breaks provide an incentive for businesses to invest in green energy.",
                    "There is little incentive for students to study if jobs are scarce.",
                ],
                "usage_notes": "Very useful for discussing policies, economics, and motivation",
                "common_mistakes": "Incentive is usually external motivation. Don't confuse with 'motive' (internal reason).",
            },
        ]

    def get_daily_words(self, count: int = config.WORDS_PER_DAY) -> list[dict]:
        """
        Get today's vocabulary words.

        Returns the same words for the same day (deterministic based on date).
        Selects words that the user hasn't mastered yet, weighted by band level.
        """
        if self._today_words:
            return self._today_words

        today = date.today()
        mastered_words = self._get_mastered_words()

        # Filter out mastered words
        available = [w for w in self._word_bank if w["word"] not in mastered_words]
        if not available:
            # All mastered — cycle back
            available = self._word_bank.copy()

        # Deterministic selection based on date
        seed = int(today.strftime("%Y%m%d"))
        rng = random.Random(seed)

        # Weight by band level (higher band = more useful to practice)
        weights = [w.get("band_level", 6) for w in available]
        selected = []
        for _ in range(min(count, len(available))):
            if not available:
                break
            idx = rng.choices(range(len(available)), weights=weights, k=1)[0]
            selected.append(available[idx])
            available.pop(idx)
            weights.pop(idx)

        self._today_words = selected
        self._record_words_introduced(selected)
        return selected

    def _get_mastered_words(self) -> set:
        """Get set of mastered word strings from database."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT word FROM vocabulary_progress WHERE is_mastered = 1"
            )
            mastered = {row[0] for row in cursor.fetchall()}
            conn.close()
            return mastered
        except Exception:
            return set()

    def _record_words_introduced(self, words: list[dict]):
        """Record that words were introduced today."""
        try:
            today = date.today().isoformat()
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            for w in words:
                cursor.execute(
                    """INSERT OR IGNORE INTO vocabulary_progress
                       (word, date_introduced, times_seen)
                       VALUES (?, ?, 1)""",
                    (w["word"], today),
                )
                cursor.execute(
                    """UPDATE vocabulary_progress
                       SET times_seen = times_seen + 1, last_seen_at = ?
                       WHERE word = ? AND date_introduced = ?""",
                    (datetime.now().isoformat(), w["word"], today),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to record vocabulary: {e}")

    def record_usage(self, word: str, correct: bool):
        """Record that a word was used (correctly or incorrectly)."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            if correct:
                cursor.execute(
                    """UPDATE vocabulary_progress
                       SET times_used_correctly = times_used_correctly + 1,
                           last_seen_at = ?
                       WHERE word = ?""",
                    (datetime.now().isoformat(), word),
                )
                # Check if mastered
                cursor.execute(
                    """UPDATE vocabulary_progress
                       SET is_mastered = 1
                       WHERE word = ? AND times_used_correctly >= ?""",
                    (word, config.VOCAB_MASTERY_THRESHOLD),
                )
            else:
                cursor.execute(
                    """UPDATE vocabulary_progress
                       SET times_used_incorrectly = times_used_incorrectly + 1,
                           last_seen_at = ?
                       WHERE word = ?""",
                    (datetime.now().isoformat(), word),
                )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to record usage: {e}")

    def get_word_progress(self) -> list[dict]:
        """Get progress data for all tracked words."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT word, date_introduced, times_seen,
                          times_used_correctly, times_used_incorrectly,
                          is_mastered, last_seen_at
                   FROM vocabulary_progress
                   ORDER BY date_introduced DESC, word"""
            )
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "word": row[0],
                    "date_introduced": row[1],
                    "times_seen": row[2],
                    "correct_uses": row[3],
                    "incorrect_uses": row[4],
                    "is_mastered": bool(row[5]),
                    "last_seen": row[6],
                }
                for row in rows
            ]
        except Exception:
            return []

    def get_daily_word_names(self) -> list[str]:
        """Get just the word strings for today."""
        return [w["word"] for w in self.get_daily_words()]

    def auto_expand_bank(self, topic: str = "general", count: int = 5):
        """Use LLM to generate new words and add to the persistent JSON file."""
        if not self._llm:
            return
        
        from intelligence.vocab_generator import VocabularyGenerator
        generator = VocabularyGenerator(self._llm)
        
        new_words = generator.expand_word_bank(self._word_bank, topic=topic, count=count)
        
        if new_words:
            self._word_bank.extend(new_words)
            try:
                with open(config.VOCAB_JSON_PATH, "w") as f:
                    json.dump(self._word_bank, f, indent=2)
            except Exception as e:
                print(f"Warning: Failed to save expanded vocabulary: {e}")
