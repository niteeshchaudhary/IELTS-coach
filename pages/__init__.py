"""
Voice Conversation Page — The core voice-first interaction page.

Features:
- WebRTC microphone capture
- Live transcription display
- Conversation history
- Status indicators
- TTS audio playback
"""

import time
import streamlit as st
import numpy as np

import config
from intelligence import prompts
from engine.conversation_state import ConversationState


def render_conversation_page():
    """Render the voice conversation page."""
    st.markdown("## 🎙️ Voice Conversation")
    st.markdown("*Speak naturally — I'll wait for you to finish before responding.*")

    # Status indicator
    status = st.session_state.get("current_status", "Ready to start")
    status_map = {
        "Ready to start": ("status-idle", "🟢 Ready"),
        "🎙️ Listening...": ("status-listening", "🎙️ Listening"),
        "🧠 Thinking...": ("status-thinking", "🧠 Thinking"),
        "🔊 Speaking...": ("status-speaking", "🔊 Speaking"),
    }
    css_class, display = status_map.get(status, ("status-idle", status))
    st.markdown(
        f'<div class="status-badge {css_class}">{display}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Voice input section ──
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🎙️ Voice Input")

        try:
            from streamlit_webrtc import webrtc_streamer, WebRtcMode

            # Check if audio models are loaded
            if not st.session_state.get("audio_models_loaded"):
                with st.spinner("Loading audio models (first time may take a minute)..."):
                    try:
                        from audio.audio_capture import AudioCapture
                        st.session_state.audio_capture = AudioCapture()
                        st.session_state.audio_models_loaded = True
                    except Exception as e:
                        st.warning(f"Audio models not available: {e}")
                        st.info("Using text input mode instead.")
                        st.session_state.audio_models_loaded = False

            if st.session_state.get("audio_models_loaded"):
                # WebRTC audio streamer
                webrtc_ctx = webrtc_streamer(
                    key="ielts-mic",
                    mode=WebRtcMode.SENDONLY,
                    audio_receiver_size=1024,
                    media_stream_constraints={
                        "audio": {
                            "sampleRate": config.AUDIO_SAMPLE_RATE,
                            "channelCount": 1,
                            "echoCancellation": True,
                            "noiseSuppression": True,
                        },
                        "video": False,
                    },
                    rtc_configuration={
                        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                    },
                )

                # Process audio frames
                if webrtc_ctx.audio_receiver:
                    _process_webrtc_audio(webrtc_ctx)

            else:
                _render_text_fallback()

        except ImportError:
            st.info("📝 WebRTC not available. Using text input mode.")
            _render_text_fallback()

    with col2:
        # Today's vocabulary sidebar
        st.markdown("### 📘 Today's Words")
        for word_data in st.session_state.daily_words:
            with st.expander(f"**{word_data['word']}** — Band {word_data.get('band_level', '?')}"):
                st.write(f"**Meaning:** {word_data['meaning']}")
                if word_data.get("examples"):
                    st.write(f"**Example:** {word_data['examples'][0]}")
                if word_data.get("common_mistakes"):
                    st.warning(f"⚠️ {word_data['common_mistakes']}")

    st.markdown("---")

    # ── Conversation history ──
    st.markdown("### 💬 Conversation")

    if not st.session_state.conversation_history:
        st.info(
            "👋 Hi! I'm your IELTS Speaking Coach. "
            "Start speaking or type a message to begin our conversation. "
            "I'll help you practice your English and improve your IELTS score!"
        )

    for turn in st.session_state.conversation_history:
        if turn["role"] == "user":
            st.markdown(
                f'<div class="user-message">🗣️ <strong>You:</strong> {turn["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="ai-message">🎓 <strong>Coach:</strong> {turn["content"]}</div>',
                unsafe_allow_html=True,
            )
            # Play audio if available
            if turn.get("audio_bytes"):
                autoplay = turn.pop("autoplay", False)
                st.audio(turn["audio_bytes"], format="audio/wav", autoplay=autoplay)


def _render_text_fallback():
    """Render text input fallback when WebRTC is not available."""
    st.markdown(
        "*💡 Tip: For the full voice experience, run locally with a microphone.*"
    )

    user_input = st.text_input(
        "Type your message:",
        key="text_input",
        placeholder="e.g., I want to practice talking about my hometown...",
    )

    if st.button("Send", key="send_btn") and user_input:
        _handle_user_input(user_input)


def _process_webrtc_audio(webrtc_ctx):
    """Process audio from WebRTC streamer."""
    capture = st.session_state.get("audio_capture")
    if not capture:
        return

    try:
        # Get audio frames from receiver
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=0.05)
        for frame in audio_frames:
            capture.process_audio_frame(frame)

        # Check for completed turns
        if capture.has_completed_turn():
            audio_data = capture.get_turn_audio()
            if audio_data is not None and len(audio_data) > 0:
                # Transcribe
                from audio.stt import SpeechToText
                if "stt" not in st.session_state:
                    st.session_state.stt = SpeechToText()

                with st.spinner("🧠 Processing your speech..."):
                    result = st.session_state.stt.transcribe(audio_data)
                    user_text = result["text"].strip()

                if user_text:
                    _handle_user_input(user_text)

        # Update status display
        status = capture.get_status()
        state = status.get("state", "SILENCE")
        state_labels = {
            "SILENCE": "Ready to start",
            "SPEECH_STARTED": "🎙️ Listening...",
            "SPEAKING": "🎙️ Listening...",
            "MAYBE_DONE": "🎙️ Listening...",
            "TURN_COMPLETE": "🧠 Thinking...",
        }
        st.session_state.current_status = state_labels.get(state, "Ready")

    except Exception as e:
        if "timeout" not in str(e).lower():
            st.warning(f"Audio processing error: {e}")


def _handle_user_input(user_text: str):
    """Process user input (from either voice or text) and generate AI response."""
    # Add user message to conversation
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_text,
    })
    st.session_state.memory.add_turn("user", user_text)

    st.session_state.current_status = "🧠 Thinking..."

    # Check vocabulary usage
    daily_word_names = st.session_state.vocab_system.get_daily_word_names()
    vocab_status = ""
    if daily_word_names:
        vocab_results = st.session_state.vocab_detector.detect(user_text, daily_word_names)
        vocab_parts = []
        for word, result in vocab_results.items():
            if result["status"] != "NOT_USED":
                vocab_parts.append(f"{word}: {result['status']}")
                # Record usage
                is_correct = result["status"] == "CORRECT"
                st.session_state.vocab_system.record_usage(word, is_correct)
        vocab_status = "; ".join(vocab_parts) if vocab_parts else "none used yet"

    # Generate AI response
    from app import get_llm_instance
    llm = get_llm_instance()

    if llm:
        try:
            # Build prompt with vocabulary context
            user_prompt = prompts.format_user_turn(
                user_text=user_text,
                vocab_words=daily_word_names,
                vocab_status=vocab_status,
            )

            context = st.session_state.memory.get_context_with_vocab()

            ai_response = llm.generate(
                user_message=user_prompt,
                context=context[:-1],  # Exclude the last user turn (it's in user_prompt)
                system_prompt=prompts.SYSTEM_TUTOR,
            )

            # Add AI response to conversation
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": ai_response,
            })
            st.session_state.memory.add_turn("assistant", ai_response)

            # Generate audio
            audio_bytes = None
            try:
                if "tts" not in st.session_state:
                    from audio.tts import TextToSpeech
                    st.session_state.tts = TextToSpeech()
                audio_bytes = st.session_state.tts.synthesize_to_wav_bytes(ai_response)
                st.session_state.conversation_history[-1]["audio_bytes"] = audio_bytes
                st.session_state.conversation_history[-1]["autoplay"] = True
            except Exception as e:
                st.caption(f"(Audio not available: {e})")

            st.session_state.current_status = "Ready to start"

        except Exception as e:
            st.error(f"Error generating response: {e}")
            st.session_state.current_status = "Ready to start"
    else:
        st.warning("LLM not configured. Set OPENAI_API_KEY or LLM_PROVIDER in environment.")
        st.session_state.current_status = "Ready to start"

    st.rerun()
