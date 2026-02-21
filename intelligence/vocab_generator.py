"""
Vocabulary Generator — LLM-powered vocabulary expansion.
"""

import json
import logging
from typing import Optional, List

from intelligence.llm_engine import LLMProvider
from intelligence import prompts

logger = logging.getLogger(__name__)

class VocabularyGenerator:
    """
    Generates high-impact IELTS vocabulary using an LLM.
    """

    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def generate_words(
        self, 
        topic: str = "general", 
        band_level: int = 7, 
        count: int = 5
    ) -> List[dict]:
        """
        Generate N new vocabulary words for a topic/band level.
        """
        prompt = prompts.SYSTEM_VOCAB_GENERATE.format(
            count=count,
            topic=topic,
            band_level=band_level
        )

        try:
            response = self._llm.generate(
                user_message=prompt,
                context=[],
                system_prompt="You are a meticulous IELTS professional. Output JSON only.",
                temperature=0.8, # Higher temperature for variety
                max_tokens=1500
            )

            # Parse JSON
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            
            words = json.loads(text)
            
            # Basic validation
            if not isinstance(words, list):
                logger.error(f"LLM returned non-list for vocabulary: {type(words)}")
                return []
            
            return words

        except Exception as e:
            logger.error(f"Failed to generate vocabulary: {e}")
            return []

    def expand_word_bank(
        self, 
        existing_bank: List[dict], 
        topic: str = "general", 
        count: int = 5
    ) -> List[dict]:
        """
        Generate words that are NOT already in the existing bank.
        """
        # Collect existing words to avoid duplicates
        existing_words = {w['word'].lower() for w in existing_bank}
        
        new_words = self.generate_words(topic=topic, count=count)
        
        # Filter duplicates
        filtered = [
            w for w in new_words 
            if w['word'].lower() not in existing_words
        ]
        
        return filtered
