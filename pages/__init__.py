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

    # ── Conversation history ──────
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.conversation_history:
            st.info(
                "👋 Hi! I'm your IELTS Speaking Coach. "
                "Start speaking or type a message below to begin our conversation. "
                "I'll help you practice your English and improve your IELTS score!"
            )

        for turn in st.session_state.conversation_history:
            with st.chat_message(turn["role"], avatar="🎓" if turn["role"] == "assistant" else "🗣️"):
                st.write(turn["content"])
                # Play audio if available
                if turn.get("audio_bytes"):
                    autoplay = turn.pop("autoplay", False)
                    st.audio(turn["audio_bytes"], format="audio/wav", autoplay=autoplay)

    st.markdown("---")

    # ── Input section ────────────
    # Voice input in an expander or columns to keep UI clean
    with st.expander("🎙️ Voice Input Controls", expanded=st.session_state.get("audio_models_loaded", False)):
        try:
            from streamlit_mic_recorder import mic_recorder
            
            st.markdown("**Click to start and stop recording:**")
            audio = mic_recorder(
                start_prompt="Record Audio",
                stop_prompt="Stop Recording",
                just_once=True,
                use_container_width=True,
                format="wav"
            )
            
            if audio:
                with st.spinner("🧠 Processing your speech..."):
                    # Load audio models if needed
                    from audio.stt import SpeechToText
                    if "stt" not in st.session_state:
                         st.session_state.stt = SpeechToText()
                         
                    # The recorder returns a dict: {'bytes': b'...', 'sample_rate': 48000}
                    # Convert raw bytes to the expected format for STT
                    audio_bytes = audio['bytes']
                    import numpy as np
                    
                    # For whisper, it's easier to let it decode the wav bytes directly
                    # Our STT model might need numpy arrays, let's let st.session_state.stt.transcribe handle the raw bytes or convert 
                    
                    # Write to temporary file for Whisper to process
                    import tempfile
                    import os
                    
                    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.wav')
                    with os.fdopen(tmp_fd, 'wb') as f:
                        f.write(audio_bytes)
                        
                    try:
                        result = st.session_state.stt.transcribe(tmp_path)
                        user_text = result["text"].strip()
                        if user_text:
                            _handle_user_input(user_text)
                    finally:
                        try:
                            os.remove(tmp_path)
                        except:
                            pass
                        
        except ImportError:
            st.info("📝 Voice recorder not installed. Run `pip install streamlit-mic-recorder`")

    # Always show chat input at the bottom
    user_input = st.chat_input("Type your message here...")
    if user_input:
        _handle_user_input(user_input)


# Removed _render_text_fallback as it's now integrated via st.chat_input




def _handle_user_input(user_text: str):
    """Process user input (from either voice or text) and generate AI response."""
    # Add user message to conversation
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_text,
    })
    st.session_state.memory.add_turn("user", user_text)

    # Estimate speaking duration for tracking
    estimated_duration = (len(user_text.split()) / 130.0) * 60.0
    st.session_state.memory.update_daily_progress(speaking_time_sec=estimated_duration)


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

            with st.spinner("🧠 Thinking..."):
                ai_response = llm.generate(
                    user_message=user_prompt,
                    context=context[:-1],  # Exclude the last user turn (it's in user_prompt)
                    system_prompt=prompts.SYSTEM_TUTOR + "\nIMPORTANT: You are ONLY the Tutor. Do not write the student's part. Respond with only your next sentence(s) in the conversation.",
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
