🎙️ IELTS English Speaking Coach (AI Tutor)
📌 PURPOSE OF THIS README (IMPORTANT)

This README exists to lock product vision, constraints, and design intent so that any agentic AI (or future contributor) does not drift, simplify, or misunderstand the goals.

This is NOT a demo app.
This is a human-like, voice-first IELTS English tutor.

🎯 PRODUCT VISION

Build an AI-powered English Speaking Coach focused on IELTS that feels like:

“I am talking to a real, patient English tutor who listens, waits, thinks, and responds naturally.”

The app must:

Improve spoken English

Improve IELTS band score

Encourage daily practice

Feel non-robotic and interruption-aware

🧱 NON-NEGOTIABLE CONSTRAINTS
Technology

Language: Python only

Frontend: Streamlit

Backend: Streamlit (same codebase)

Runs locally

LLM-driven logic

UX Rules

❌ No “Stop Speaking” button
❌ No push-to-talk UX
❌ No text-only chatbot experience

✅ Auto pause detection
✅ Natural waiting
✅ Voice-first interaction

🧠 CORE INTELLIGENCE REQUIREMENTS
1️⃣ Daily IELTS Vocabulary System

Every day the app must:

Select IELTS-relevant vocabulary

Provide:

Meaning

Example sentences

Usage notes

Common mistakes

Actively initiate conversation to force usage

Detect:

Correct usage

Incorrect usage

Partial usage

Provide gentle corrections, never harsh feedback

2️⃣ Real Human-Like Conversation

The system must support:

Voice input

Voice output

Natural turn-taking

Context memory

The user should feel:

The AI listens fully

The AI waits if the user pauses

The AI does not interrupt

The AI responds intelligently

3️⃣ Automatic Pause Detection (CRITICAL FEATURE)

The app must:

Detect long pauses (≈1.5–2.5 seconds)

Automatically treat silence as:

End of user turn

Never require the user to say “I’m done”

4️⃣ Smart Response Buffering (VERY IMPORTANT)

While the user is speaking:

AI may prepare a response

AI must NOT speak immediately

After user stops:

Decide whether to:

Continue buffered response

Drop buffered response

Merge buffer + user reply

Decision must be based on:

Relevance

Conversation flow

Importance of buffered content

This logic must be explicitly coded, not assumed.

🗣️ VOICE PIPELINE REQUIREMENTS
Speech-to-Text (STT)

Streaming capable

Accurate for non-native accents

Supports pause detection

Examples:

Whisper / Faster-Whisper

Vosk

Text-to-Speech (TTS)

Free or open-source

Natural sounding

ElevenLabs-like quality preferred

Examples:

Coqui TTS

Piper

Bark (if feasible)

🖥️ UI REQUIREMENTS (Streamlit)

The UI must include:

🎙️ Live microphone capture

📝 Live transcription

🔊 Audio playback

📘 Word of the Day

🎮 Games section

🧪 IELTS tests section

📊 Progress tracking

🎮 LEARNING FEATURES
Vocabulary & Typing Games

Word matching

Sentence completion

Typing accuracy & speed

Error correction tasks

IELTS Practice Modules

Listening test

Reading test

Speaking test

(Optional) Writing prompts

⏰ Vocabulary Reinforcement

Same Word of the Day repeated:

During conversations

In reminders

In games

Reinforcement throughout the day

📘 IELTS GUIDANCE MODULE

The app must include structured guidance for:

IELTS exam format

Band score criteria

Common mistakes

Daily preparation plan

Mock test strategies

Exam-day tips

🧩 ARCHITECTURE EXPECTATIONS

The system must clearly define:

Conversation state machine

Audio pipeline

Buffering logic

LLM prompt layers

Memory handling

Modular components

The agent must not collapse everything into one script.

🛠️ EXPECTED OUTPUT FROM AGENTIC AI

The agent must deliver:

Architecture explanation

Component-level design

Exact Python libraries used

Streamlit app structure

Pause detection logic

Buffer decision pseudocode

LLM system + user prompts

Working end-to-end code

Local run instructions

Scalability notes

🚫 ANTI-GOALS (DO NOT DO THIS)

❌ Simple chatbot

❌ Text-only IELTS app

❌ Button-driven conversation

❌ Ignoring pause/buffer logic

❌ “Demo-level” shortcuts

✅ SUCCESS CRITERIA

This project is successful only if:

User can speak naturally

User can pause freely

AI responds like a human tutor

IELTS vocabulary improves measurably

App feels conversational, not transactional

🚀 HOW TO RUN

Prerequisites

- Python 3.10+
- ~4 GB RAM (for audio models: Silero VAD, Faster-Whisper, Piper TTS)
- A working microphone (for voice mode; text fallback available)

1. Install Dependencies

```bash
cd eng_prep
pip install -r requirements.txt
```

2. Configure LLM Provider

Choose ONE of the following:

Option A — OpenAI (default):
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Option B — Google Gemini:
```bash
export LLM_PROVIDER="gemini"
export GEMINI_API_KEY="your-gemini-key"
```

Option C — Ollama (fully local, no API key needed):
```bash
export LLM_PROVIDER="ollama"
export LLM_MODEL="deepseek-r1:latest"
# Make sure Ollama is running: ollama serve
```

3. Run the App

```bash
streamlit run app.py
```

The app will open at http://localhost:8501.

Pages

- 🎙️ Conversation — Voice or text chat with your AI tutor
- 📘 Word of the Day — Daily IELTS vocabulary cards + practice
- 🎮 Games — Word matching, sentence completion, typing speed, error correction
- 🧪 IELTS Practice — Speaking Part 1, 2, 3 with band score evaluation
- 📊 Progress — Dashboard with streaks, vocabulary mastery, daily activity
- 📖 IELTS Guide — Exam format, band criteria, common mistakes, tips

Notes

- First launch downloads audio models (~500 MB). Subsequent launches are faster.
- If WebRTC microphone is unavailable, the app falls back to text input automatically.
- All progress is stored locally in `data/user_progress.db` (SQLite).
- Configuration parameters are in `config.py` — no magic numbers elsewhere.

🧠 FINAL NOTE TO AGENTIC AI

Preserve this context at all times.
If any design decision conflicts with this README, this README wins.