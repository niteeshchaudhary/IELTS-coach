"""
Central configuration for IELTS English Speaking Coach.
All tunable parameters live here — no magic numbers elsewhere.
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "user_progress.db"
VOCAB_JSON_PATH = DATA_DIR / "ielts_vocabulary.json"
TOPICS_JSON_PATH = DATA_DIR / "ielts_topics.json"

# ──────────────────────────────────────────────
# Audio Pipeline
# ──────────────────────────────────────────────
AUDIO_SAMPLE_RATE = 16000          # 16kHz — required by Whisper
AUDIO_CHANNELS = 1                 # Mono
AUDIO_CHUNK_MS = 32                # 32ms chunks for VAD (512 samples at 16kHz)
# NOTE: Silero VAD v4+ requires chunk sizes of 512, 1024, or 1536 samples for 16kHz.
# 480 samples (30ms) is too short and triggers "Input audio chunk is too short".
AUDIO_CHUNK_SAMPLES = 512

# ──────────────────────────────────────────────
# Voice Activity Detection (Silero VAD)
# ──────────────────────────────────────────────
VAD_THRESHOLD = 0.5                # Speech probability threshold (0.0–1.0)
VAD_MIN_SPEECH_MS = 300            # Minimum continuous speech to count as real speech
VAD_MIN_SPEECH_CHUNKS = int(VAD_MIN_SPEECH_MS / AUDIO_CHUNK_MS)  # ~10 chunks

# ──────────────────────────────────────────────
# Pause Detection
# ──────────────────────────────────────────────
PAUSE_THRESHOLD_MS = 2000          # Silence duration to end user turn (1500–2500ms)
PAUSE_THRESHOLD_CHUNKS = int(PAUSE_THRESHOLD_MS / AUDIO_CHUNK_MS)  # ~67 chunks

# ──────────────────────────────────────────────
# Speech-to-Text (Faster-Whisper)
# ──────────────────────────────────────────────
WHISPER_MODEL_SIZE = "base"        # Options: tiny, base, small, medium, large-v3
WHISPER_DEVICE = "cpu"             # "cpu" or "cuda"
WHISPER_COMPUTE_TYPE = "int8"      # int8 for CPU, float16 for GPU
WHISPER_LANGUAGE = "en"
WHISPER_BEAM_SIZE = 5
WHISPER_VAD_FILTER = True          # Enable built-in VAD filtering

# ──────────────────────────────────────────────
# Text-to-Speech (Piper TTS)
# ──────────────────────────────────────────────
PIPER_MODEL_NAME = "en_US-lessac-medium"
PIPER_SPEAKER_ID = 0
PIPER_LENGTH_SCALE = 1.0           # Speech speed (lower = faster)
PIPER_NOISE_SCALE = 0.667          # Variation in speech
PIPER_NOISE_W = 0.8                # Phoneme width noise

# ──────────────────────────────────────────────
# LLM Configuration
# ──────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")   # openai / gemini / ollama / groq
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 300               # Keep responses conversational, not essay-length
LLM_STREAMING = True               # Stream responses for lower perceived latency
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))  # Default 5 minutes for local LLMs

# API Keys (from environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ──────────────────────────────────────────────
# Smart Response Buffering
# ──────────────────────────────────────────────
BUFFER_RELEVANCE_THRESHOLD = 0.6   # Drop buffered response if relevance < this
BUFFER_MAX_AGE_MS = 10000          # Drop buffer if older than 10 seconds
BUFFER_MERGE_ENABLED = True        # Allow merging buffer with new context

# ──────────────────────────────────────────────
# Conversation
# ──────────────────────────────────────────────
CONVERSATION_HISTORY_MAX_TURNS = 20  # Rolling context window
AI_RESPONSE_DELAY_MS = 400          # Small pause before AI speaks (feels natural)

# ──────────────────────────────────────────────
# Vocabulary System
# ──────────────────────────────────────────────
WORDS_PER_DAY = 3                  # Number of daily vocabulary words
REINFORCEMENT_INTERVAL_TURNS = 5   # Reinforce vocab every N conversation turns
VOCAB_MASTERY_THRESHOLD = 5        # Correct uses needed to consider word "mastered"

# ──────────────────────────────────────────────
# IELTS
# ──────────────────────────────────────────────
IELTS_SPEAKING_PART2_TIME_SEC = 120  # 2 minutes for Part 2
IELTS_SPEAKING_PART2_PREP_SEC = 60   # 1 minute preparation
IELTS_MIN_BAND = 1.0
IELTS_MAX_BAND = 9.0

# ──────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────
APP_TITLE = "🎙️ IELTS English Speaking Coach"
APP_ICON = "🎙️"
SIDEBAR_DEFAULT_PAGE = "Conversation"
