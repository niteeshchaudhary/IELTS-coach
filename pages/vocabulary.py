"""
Word of the Day Page — Daily vocabulary display and practice.
"""

import streamlit as st

from audio.tts import TextToSpeech


def _get_tts() -> TextToSpeech:
    """Get or create a shared TTS instance for pronunciation."""
    if "tts" not in st.session_state:
        st.session_state.tts = TextToSpeech()
    return st.session_state.tts


def _pronounce(text: str) -> tuple[bytes, str]:
    """Generate pronunciation audio. Returns (audio_bytes, mime_type)."""
    tts = _get_tts()
    return tts.synthesize_to_playable_bytes(text)


def render_vocabulary_page():
    """Render the Word of the Day page."""
    st.markdown("## 📘 Word of the Day")
    st.markdown("*Learn and practice today's IELTS vocabulary. Press 🔊 to hear pronunciation.*")
    st.markdown("---")

    daily_words = st.session_state.daily_words

    if not daily_words:
        st.info("No vocabulary words available. Check your vocabulary data file.")
        return

    # Display each word in a styled card
    for i, word_data in enumerate(daily_words):
        with st.container():
            # ── Word header with pronunciation button ──
            header_col, btn_col = st.columns([5, 1])

            with header_col:
                st.markdown(
                    f"""
                    <div class="vocab-card">
                        <h3>📖 {word_data['word']}</h3>
                        <p><em>Band {word_data.get('band_level', '?')} · {word_data.get('topic', 'general')}</em></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with btn_col:
                if st.button("🔊", key=f"pronounce_{i}", help=f"Hear '{word_data['word']}' pronounced"):
                    with st.spinner("🔊"):
                        audio_bytes, mime = _pronounce(
                            f"{word_data['word']}. {word_data['word']}. {word_data['meaning']}."
                        )
                        st.session_state[f"pron_audio_{i}"] = audio_bytes
                        st.session_state[f"pron_mime_{i}"] = mime
                        st.session_state[f"pron_autoplay_{i}"] = True

            # Play pronunciation audio if generated
            if f"pron_audio_{i}" in st.session_state and st.session_state[f"pron_audio_{i}"]:
                autoplay = st.session_state.pop(f"pron_autoplay_{i}", False)
                st.audio(
                    st.session_state[f"pron_audio_{i}"],
                    format=st.session_state.get(f"pron_mime_{i}", "audio/mp3"),
                    autoplay=autoplay,
                )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Meaning:** {word_data['meaning']}")

                if word_data.get("examples"):
                    st.markdown("**Example Sentences:**")
                    for j, ex in enumerate(word_data["examples"]):
                        ex_col, ex_btn = st.columns([6, 1])
                        with ex_col:
                            st.markdown(f"- *\"{ex}\"*")
                        with ex_btn:
                            if st.button("🔊", key=f"pron_ex_{i}_{j}", help="Hear this example"):
                                with st.spinner("🔊"):
                                    audio, mime = _pronounce(ex)
                                    st.session_state[f"ex_audio_{i}_{j}"] = audio
                                    st.session_state[f"ex_mime_{i}_{j}"] = mime
                                    st.session_state[f"ex_autoplay_{i}_{j}"] = True

                        if f"ex_audio_{i}_{j}" in st.session_state and st.session_state[f"ex_audio_{i}_{j}"]:
                            autoplay = st.session_state.pop(f"ex_autoplay_{i}_{j}", False)
                            st.audio(
                                st.session_state[f"ex_audio_{i}_{j}"],
                                format=st.session_state.get(f"ex_mime_{i}_{j}", "audio/mp3"),
                                autoplay=autoplay,
                            )

            with col2:
                if word_data.get("usage_notes"):
                    st.info(f"💡 **Usage Tip:** {word_data['usage_notes']}")

                if word_data.get("common_mistakes"):
                    st.warning(f"⚠️ **Common Mistake:** {word_data['common_mistakes']}")

            # Practice input
            st.markdown(f"**✍️ Try using '{word_data['word']}' in a sentence:**")
            user_sentence = st.text_input(
                f"Your sentence with '{word_data['word']}':",
                key=f"vocab_practice_{i}",
                placeholder=f"Write a sentence using the word '{word_data['word']}'...",
            )

            if user_sentence:
                # Ensure LLM is available for detection
                if not st.session_state.get("llm"):
                    from intelligence.llm_engine import get_llm
                    try:
                        st.session_state.llm = get_llm()
                        st.session_state.vocab_detector.set_llm(st.session_state.llm)
                    except Exception:
                        pass
                
                # Check usage using the detector
                with st.spinner("Analyzing sentence..."):
                    results = st.session_state.vocab_detector.detect(
                        user_sentence, [word_data["word"]]
                    )
                    usage = results.get(word_data["word"], {})
                    status = usage.get("status", "NOT_USED")
                    feedback = usage.get("feedback", "")

                if status == "CORRECT":
                    default_msg = f"You used '{word_data['word']}' perfectly!"
                    st.success(f"✅ **Great!** {feedback or default_msg}")
                    st.session_state.vocab_system.record_usage(word_data["word"], True)
                elif status == "INCORRECT":
                    st.error(f"❌ **Grammar/Usage Note:** {feedback}")
                    st.session_state.vocab_system.record_usage(word_data["word"], False)
                elif status == "PARTIAL":
                    st.warning(f"⚠️ **Almost there!** {feedback}")
                    st.session_state.vocab_system.record_usage(word_data["word"], False)
                else:
                    st.warning(f"Hmm, I don't see '{word_data['word']}' in your sentence correctly. Try again!")

            st.markdown("---")

    # Vocabulary progress section
    st.markdown("### 📊 Vocabulary Progress")

    progress = st.session_state.vocab_system.get_word_progress()
    if progress:
        for wp in progress[-10:]:
            mastery = "✅ Mastered" if wp["is_mastered"] else f"📈 {wp['correct_uses']}/5 correct uses"
            st.markdown(
                f"**{wp['word']}** — {mastery} "
                f"(Seen: {wp['times_seen']}x, Correct: {wp['correct_uses']}x, "
                f"Incorrect: {wp['incorrect_uses']}x)"
            )
    else:
        st.caption("Start practicing to see your progress here!")
