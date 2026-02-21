"""
IELTS Band Score Estimator.

Evaluates speaking performance against official IELTS band descriptors
using LLM analysis.
"""

import json
from typing import Optional

from intelligence.llm_engine import LLMProvider
from intelligence import prompts


class IELTSScorer:
    """
    Estimates IELTS speaking band scores.

    Evaluates on 4 criteria:
    1. Fluency & Coherence
    2. Lexical Resource
    3. Grammatical Range & Accuracy
    4. Pronunciation (estimated from transcription)

    Returns per-criterion scores, overall band, and actionable feedback.
    """

    def __init__(self, llm: Optional[LLMProvider] = None):
        self._llm = llm

    def set_llm(self, llm: LLMProvider):
        """Set the LLM provider."""
        self._llm = llm

    def evaluate(
        self,
        student_text: str,
        duration_seconds: float = 0,
        topic: str = "general conversation",
    ) -> dict:
        """
        Evaluate student speech for IELTS band score.

        Args:
            student_text: Transcribed student speech
            duration_seconds: Speaking duration
            topic: The conversation/test topic

        Returns:
            dict with per-criterion scores, overall band, strengths, improvements
        """
        if not self._llm or not student_text.strip():
            return self._empty_result()

        prompt = prompts.SYSTEM_BAND_SCORE.format(
            student_text=student_text,
            duration_seconds=f"{duration_seconds:.1f}",
            topic=topic,
        )

        try:
            response = self._llm.generate(
                user_message=prompt,
                context=[],
                system_prompt="You are an IELTS speaking examiner. Respond with JSON only.",
                temperature=0.2,
                max_tokens=500,
            )

            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]

            result = json.loads(response_text)

            # Validate and clamp scores
            for key in ["fluency_coherence", "lexical_resource",
                        "grammatical_range", "pronunciation"]:
                if key in result:
                    score = result[key].get("score", 5.0)
                    result[key]["score"] = max(1.0, min(9.0, float(score)))

            if "overall_band" in result:
                result["overall_band"] = max(1.0, min(9.0, float(result["overall_band"])))

            return result

        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: IELTS scoring failed: {e}")
            return self._empty_result()

    def _empty_result(self) -> dict:
        """Return empty/default result."""
        return {
            "fluency_coherence": {"score": 0, "feedback": "Not enough speech to evaluate"},
            "lexical_resource": {"score": 0, "feedback": "Not enough speech to evaluate"},
            "grammatical_range": {"score": 0, "feedback": "Not enough speech to evaluate"},
            "pronunciation": {"score": 0, "feedback": "Cannot evaluate from text alone"},
            "overall_band": 0,
            "strengths": [],
            "improvements": ["Try speaking more to get a proper evaluation"],
        }

    def get_band_description(self, band: float) -> str:
        """Get a human-readable description for a band score."""
        descriptions = {
            9: "Expert — Full operational command of English",
            8: "Very Good — Fully operational with occasional inaccuracies",
            7: "Good — Operational command with occasional inaccuracies",
            6: "Competent — Generally effective command despite some inaccuracies",
            5: "Modest — Partial command, coping with overall meaning",
            4: "Limited — Basic competence in familiar situations",
            3: "Extremely Limited — Conveys only general meaning",
            2: "Intermittent — Great difficulty understanding",
            1: "Non-User — No ability to use language",
        }
        rounded = round(band)
        return descriptions.get(rounded, f"Band {band:.1f}")
