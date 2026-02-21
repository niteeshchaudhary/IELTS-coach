"""
Game Modules for IELTS vocabulary practice.

- Word Matching: match words to definitions
- Sentence Completion: fill in blanks with vocabulary words
- Typing Speed: type words/sentences accurately and quickly
- Error Correction: find and fix grammar/vocabulary errors
"""

import random
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class GameResult:
    """Result of a completed game round."""
    game_type: str
    score: int
    total: int
    time_seconds: float
    details: list[dict] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return (self.score / self.total * 100) if self.total > 0 else 0


class WordMatchingGame:
    """Match vocabulary words to their definitions."""

    def __init__(self, words: list[dict]):
        self.words = words
        self._current_round: list[dict] = []
        self._start_time: Optional[float] = None

    def new_round(self, count: int = 5) -> list[dict]:
        """Generate a new round of word-definition pairs."""
        available = self.words.copy()
        random.shuffle(available)
        selected = available[:min(count, len(available))]

        self._current_round = selected
        self._start_time = time.time()

        # Return words and shuffled definitions separately
        definitions = [w["meaning"] for w in selected]
        random.shuffle(definitions)

        return [
            {
                "word": w["word"],
                "correct_meaning": w["meaning"],
                "options": definitions,
            }
            for w in selected
        ]

    def check_answers(self, answers: dict[str, str]) -> GameResult:
        """
        Check user answers.
        answers: {word: selected_definition}
        """
        elapsed = time.time() - self._start_time if self._start_time else 0
        correct = 0
        details = []

        for word_data in self._current_round:
            word = word_data["word"]
            user_answer = answers.get(word, "")
            is_correct = user_answer.strip().lower() == word_data["meaning"].strip().lower()
            if is_correct:
                correct += 1
            details.append({
                "word": word,
                "correct_answer": word_data["meaning"],
                "user_answer": user_answer,
                "is_correct": is_correct,
            })

        return GameResult(
            game_type="word_matching",
            score=correct,
            total=len(self._current_round),
            time_seconds=elapsed,
            details=details,
        )


class SentenceCompletionGame:
    """Fill in blanks in sentences with the correct vocabulary word."""

    def __init__(self, words: list[dict]):
        self.words = words
        self._current_round: list[dict] = []
        self._start_time: Optional[float] = None

    def new_round(self, count: int = 5) -> list[dict]:
        """Generate sentences with blanks."""
        available = [w for w in self.words if w.get("examples")]
        random.shuffle(available)
        selected = available[:min(count, len(available))]

        self._current_round = []
        self._start_time = time.time()

        questions = []
        all_words = [w["word"] for w in selected]

        for w in selected:
            example = random.choice(w["examples"])
            # Create blank by replacing the word
            blanked = example.lower().replace(w["word"].lower(), "______")
            # Handle morphological variants
            for suffix in ["s", "es", "ed", "d", "ing", "ly", "tion"]:
                blanked = blanked.replace(w["word"].lower() + suffix, "______")

            self._current_round.append({
                "word": w["word"],
                "sentence": blanked,
                "original": example,
            })

            questions.append({
                "sentence": blanked,
                "hint": w["meaning"],
                "options": all_words,
            })

        return questions

    def check_answers(self, answers: list[str]) -> GameResult:
        """Check user answers (list of words in order)."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        correct = 0
        details = []

        for i, round_data in enumerate(self._current_round):
            user_answer = answers[i] if i < len(answers) else ""
            is_correct = user_answer.strip().lower() == round_data["word"].lower()
            if is_correct:
                correct += 1
            details.append({
                "correct_word": round_data["word"],
                "user_answer": user_answer,
                "original_sentence": round_data["original"],
                "is_correct": is_correct,
            })

        return GameResult(
            game_type="sentence_completion",
            score=correct,
            total=len(self._current_round),
            time_seconds=elapsed,
            details=details,
        )


class TypingSpeedGame:
    """Test typing accuracy and speed with IELTS sentences."""

    SENTENCES = [
        "The ubiquitous use of technology has transformed modern education.",
        "Governments should allocate more resources to sustainable development.",
        "The prevalence of obesity has become a significant health concern.",
        "Innovative approaches are needed to mitigate climate change.",
        "Social media can exacerbate feelings of isolation among young people.",
        "A paradigm shift in education is essential for future generations.",
        "Autonomous vehicles will facilitate more efficient transportation.",
        "The disparity between rich and poor nations continues to grow.",
        "Pragmatic solutions are needed to address environmental challenges.",
        "Building resilient communities requires substantial investment.",
    ]

    def __init__(self):
        self._current_sentence = ""
        self._start_time: Optional[float] = None

    def new_round(self) -> str:
        """Get a random sentence to type."""
        self._current_sentence = random.choice(self.SENTENCES)
        self._start_time = time.time()
        return self._current_sentence

    def check_answer(self, typed_text: str) -> GameResult:
        """Check typed text against the target sentence."""
        elapsed = time.time() - self._start_time if self._start_time else 0

        target = self._current_sentence
        typed = typed_text.strip()

        # Calculate accuracy (character-level)
        correct_chars = sum(
            1 for a, b in zip(target, typed) if a == b
        )
        total_chars = max(len(target), len(typed))
        accuracy = (correct_chars / total_chars * 100) if total_chars > 0 else 0

        # Calculate WPM (words per minute)
        word_count = len(typed.split())
        wpm = (word_count / elapsed * 60) if elapsed > 0 else 0

        return GameResult(
            game_type="typing_speed",
            score=int(accuracy),
            total=100,
            time_seconds=elapsed,
            details=[{
                "target": target,
                "typed": typed,
                "accuracy_percent": round(accuracy, 1),
                "wpm": round(wpm, 1),
                "correct_chars": correct_chars,
                "total_chars": total_chars,
            }],
        )


class ErrorCorrectionGame:
    """Find and correct grammar/vocabulary errors in sentences."""

    QUESTIONS = [
        {
            "incorrect": "The government should allocate more funds for education.",
            "correct": "The government should allocate more funds to education.",
            "error_type": "preposition",
            "explanation": "We say 'allocate TO' not 'allocate for'.",
        },
        {
            "incorrect": "This problem is very prevalent among for young people.",
            "correct": "This problem is very prevalent among young people.",
            "error_type": "extra word",
            "explanation": "Remove the extra 'for' — 'prevalent among' is correct.",
        },
        {
            "incorrect": "The new policy detrimental for local businesses.",
            "correct": "The new policy is detrimental to local businesses.",
            "error_type": "missing verb + wrong preposition",
            "explanation": "Needs 'is' and the preposition should be 'to' not 'for'.",
        },
        {
            "incorrect": "We need to take a more pragmatical approach.",
            "correct": "We need to take a more pragmatic approach.",
            "error_type": "word form",
            "explanation": "The adjective form is 'pragmatic', not 'pragmatical'.",
        },
        {
            "incorrect": "Technology has facilitated to learn new skills.",
            "correct": "Technology has facilitated learning new skills.",
            "error_type": "grammar",
            "explanation": "Facilitate takes a direct object (gerund), not 'to + infinitive'.",
        },
        {
            "incorrect": "The situation was exasperated by heavy rainfall.",
            "correct": "The situation was exacerbated by heavy rainfall.",
            "error_type": "word confusion",
            "explanation": "Exacerbate means 'make worse'. Exasperate means 'annoy'.",
        },
        {
            "incorrect": "There has been an unprecedented growth in the last decade.",
            "correct": "There has been unprecedented growth in the last decade.",
            "error_type": "article",
            "explanation": "Uncountable noun 'growth' doesn't need the article 'an'.",
        },
        {
            "incorrect": "Children are more resilient that adults think.",
            "correct": "Children are more resilient than adults think.",
            "error_type": "comparative",
            "explanation": "Comparatives use 'than', not 'that'.",
        },
    ]

    def __init__(self):
        self._current_round: list[dict] = []
        self._start_time: Optional[float] = None

    def new_round(self, count: int = 4) -> list[dict]:
        """Generate error correction questions."""
        available = self.QUESTIONS.copy()
        random.shuffle(available)
        self._current_round = available[:min(count, len(available))]
        self._start_time = time.time()

        return [
            {
                "sentence": q["incorrect"],
                "hint": f"Error type: {q['error_type']}",
            }
            for q in self._current_round
        ]

    def check_answers(self, corrections: list[str]) -> GameResult:
        """Check user corrections."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        correct = 0
        details = []

        for i, q in enumerate(self._current_round):
            user_answer = corrections[i].strip() if i < len(corrections) else ""
            # Flexible matching — check if key correction was made
            is_correct = (
                user_answer.lower() == q["correct"].lower()
                or self._fuzzy_match(user_answer, q["correct"])
            )
            if is_correct:
                correct += 1
            details.append({
                "incorrect": q["incorrect"],
                "correct_answer": q["correct"],
                "user_answer": user_answer,
                "is_correct": is_correct,
                "explanation": q["explanation"],
            })

        return GameResult(
            game_type="error_correction",
            score=correct,
            total=len(self._current_round),
            time_seconds=elapsed,
            details=details,
        )

    def _fuzzy_match(self, user: str, correct: str) -> bool:
        """Check if the user's answer is close enough (ignoring punctuation/case)."""
        import re
        clean = lambda s: re.sub(r'[^\w\s]', '', s.lower().strip())
        return clean(user) == clean(correct)
