"""
Vocabulary Usage Detector.

Detects whether the user used today's vocabulary words in their speech,
classifying usage as CORRECT, INCORRECT, PARTIAL, or NOT_USED.
"""

import json
from typing import Optional
from enum import Enum, auto

from intelligence.llm_engine import LLMProvider
from intelligence import prompts


class VocabUsageStatus(Enum):
    """Classification of vocabulary usage."""
    CORRECT = auto()
    INCORRECT = auto()
    PARTIAL = auto()
    NOT_USED = auto()


class VocabDetector:
    """
    Detects and classifies vocabulary usage in transcribed speech.

    Uses a two-stage approach:
    1. Quick string matching for exact/fuzzy word presence
    2. LLM classification for usage correctness and context
    """

    def __init__(self, llm: Optional[LLMProvider] = None):
        self._llm = llm

    def set_llm(self, llm: LLMProvider):
        """Set the LLM provider (can be called after init)."""
        self._llm = llm

    def detect(
        self,
        student_text: str,
        target_words: list[str],
    ) -> dict[str, dict]:
        """
        Detect vocabulary usage in student speech.

        Args:
            student_text: Transcribed student speech
            target_words: List of target vocabulary words

        Returns:
            Dict mapping each word to {status, feedback, found_in_text}
        """
        results = {}

        # Stage 1: Quick string matching
        text_lower = student_text.lower()
        for word in target_words:
            word_lower = word.lower()
            found = self._fuzzy_search(word_lower, text_lower)
            results[word] = {
                "status": VocabUsageStatus.NOT_USED.name,
                "feedback": "",
                "found_in_text": found,
            }

        # Stage 2: LLM classification for words that were found
        words_found = [w for w in target_words if results[w]["found_in_text"]]
        if words_found and self._llm:
            llm_results = self._llm_classify(student_text, words_found)
            for word, classification in llm_results.items():
                if word in results:
                    results[word]["status"] = classification.get("status", "NOT_USED")
                    results[word]["feedback"] = classification.get("feedback", "")

        return results

    def _fuzzy_search(self, word: str, text: str) -> bool:
        """
        Check if a word (or close variant) appears in the text.

        Handles:
        - Exact match
        - Plural forms (-s, -es)
        - Past tense (-ed, -d)
        - Gerund (-ing)
        - Adverb form (-ly)
        """
        # Exact match
        if word in text:
            return True

        # Common morphological variants
        variants = [
            word + "s",
            word + "es",
            word + "ed",
            word + "d",
            word + "ing",
            word + "ly",
            word + "tion",
            word + "ment",
        ]

        # Handle words ending in 'e' (e.g., 'mitigate' → 'mitigating')
        if word.endswith("e"):
            variants.extend([
                word[:-1] + "ing",
                word[:-1] + "ed",
                word + "d",
            ])

        # Handle words ending in consonant (e.g., 'occur' → 'occurring')
        if len(word) > 2 and word[-1] not in "aeiou" and word[-2] in "aeiou":
            variants.extend([
                word + word[-1] + "ing",
                word + word[-1] + "ed",
            ])

        return any(v in text for v in variants)

    def _llm_classify(
        self,
        student_text: str,
        target_words: list[str],
    ) -> dict:
        """Use LLM to classify vocabulary usage."""
        if not self._llm:
            return {}

        prompt = prompts.SYSTEM_VOCAB_DETECT.format(
            target_words=", ".join(target_words),
            student_text=student_text,
        )

        try:
            response = self._llm.generate(
                user_message=prompt,
                context=[],
                system_prompt="You are a vocabulary usage analyzer. Respond with JSON only.",
                temperature=0.1,
                max_tokens=300,
            )

            # Parse JSON response
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]

            return json.loads(response_text)

        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: LLM vocab classification failed: {e}")
            # Fall back to simple matching
            return {
                word: {"status": "PARTIAL", "feedback": "Word was used (auto-detected)"}
                for word in target_words
            }
