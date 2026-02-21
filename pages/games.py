"""
Games Page — Vocabulary and typing practice games.
"""

import streamlit as st

from games import (
    WordMatchingGame,
    SentenceCompletionGame,
    TypingSpeedGame,
    ErrorCorrectionGame,
)


def render_games_page():
    """Render the games page."""
    st.markdown("## 🎮 Vocabulary & Typing Games")
    st.markdown("*Practice makes perfect! Play games to reinforce your vocabulary.*")
    st.markdown("---")

    # Game selection
    game_type = st.selectbox(
        "Choose a game:",
        ["🔤 Word Matching", "📝 Sentence Completion", "⌨️ Typing Speed", "🔍 Error Correction"],
    )

    st.markdown("---")

    if game_type == "🔤 Word Matching":
        _render_word_matching()
    elif game_type == "📝 Sentence Completion":
        _render_sentence_completion()
    elif game_type == "⌨️ Typing Speed":
        _render_typing_speed()
    elif game_type == "🔍 Error Correction":
        _render_error_correction()


def _render_word_matching():
    """Word matching game: match words to definitions."""
    st.markdown("### 🔤 Word Matching")
    st.markdown("*Match each vocabulary word with its correct definition.*")

    words = st.session_state.daily_words
    if not words:
        st.warning("No vocabulary words available.")
        return

    if "wm_game" not in st.session_state:
        st.session_state.wm_game = WordMatchingGame(words)
    game = st.session_state.wm_game
    game.words = words

    if st.button("🎲 New Round", key="wm_new"):
        st.session_state.wm_round = game.new_round(count=min(5, len(words)))
        st.session_state.wm_answers = {}
        st.session_state.wm_submitted = False

    if "wm_round" in st.session_state and not st.session_state.get("wm_submitted"):
        questions = st.session_state.wm_round
        answers = {}

        for q in questions:
            selected = st.selectbox(
                f"**{q['word']}** means:",
                options=["-- Select --"] + q["options"],
                key=f"wm_{q['word']}",
            )
            if selected != "-- Select --":
                answers[q["word"]] = selected

        if st.button("✅ Check Answers", key="wm_check"):
            st.session_state.wm_answers = answers
            result = game.check_answers(answers)
            st.session_state.wm_submitted = True
            st.session_state.memory.update_daily_progress(games_played=1, add_turn=False)

            st.markdown(f'<div class="game-score">{result.score}/{result.total}</div>', unsafe_allow_html=True)
            st.markdown(f"⏱️ Time: {result.time_seconds:.1f}s")

            for detail in result.details:
                if detail["is_correct"]:
                    st.success(f"✅ {detail['word']} — Correct!")
                else:
                    st.error(f"❌ {detail['word']} — Correct answer: {detail['correct_answer']}")


def _render_sentence_completion():
    """Sentence completion game: fill in blanks."""
    st.markdown("### 📝 Sentence Completion")
    st.markdown("*Fill in the blank with the correct vocabulary word.*")

    words = st.session_state.daily_words
    if not words:
        st.warning("No vocabulary words available.")
        return

    if "sc_game" not in st.session_state:
        st.session_state.sc_game = SentenceCompletionGame(words)
    game = st.session_state.sc_game
    game.words = words

    if st.button("🎲 New Round", key="sc_new"):
        st.session_state.sc_round = game.new_round(count=min(5, len(words)))
        st.session_state.sc_submitted = False

    if "sc_round" in st.session_state and not st.session_state.get("sc_submitted"):
        questions = st.session_state.sc_round
        answers = []

        for i, q in enumerate(questions):
            st.markdown(f"**{i+1}.** {q['sentence']}")
            st.caption(f"Hint: {q['hint']}")
            answer = st.selectbox(
                f"Word for blank {i+1}:",
                options=["-- Select --"] + q["options"],
                key=f"sc_{i}",
            )
            answers.append(answer if answer != "-- Select --" else "")

        if st.button("✅ Check Answers", key="sc_check"):
            result = game.check_answers(answers)
            st.session_state.sc_submitted = True
            st.session_state.memory.update_daily_progress(games_played=1, add_turn=False)

            st.markdown(f'<div class="game-score">{result.score}/{result.total}</div>', unsafe_allow_html=True)

            for detail in result.details:
                if detail["is_correct"]:
                    st.success(f"✅ Correct! {detail['original_sentence']}")
                else:
                    st.error(f"❌ Correct word: **{detail['correct_word']}**")
                    st.caption(f"Full sentence: {detail['original_sentence']}")


def _render_typing_speed():
    """Typing speed and accuracy game."""
    st.markdown("### ⌨️ Typing Speed Challenge")
    st.markdown("*Type the sentence as fast and accurately as you can!*")

    if "ts_game" not in st.session_state:
        st.session_state.ts_game = TypingSpeedGame()
    game = st.session_state.ts_game

    if st.button("🎲 New Sentence", key="ts_new"):
        st.session_state.ts_sentence = game.new_round()
        st.session_state.ts_submitted = False

    if "ts_sentence" in st.session_state and not st.session_state.get("ts_submitted"):
        st.markdown(f"**Type this sentence:**")
        st.info(st.session_state.ts_sentence)

        typed = st.text_area(
            "Your typing:",
            key="ts_input",
            height=100,
            placeholder="Start typing the sentence above...",
        )

        if st.button("✅ Submit", key="ts_submit") and typed:
            result = game.check_answer(typed)
            st.session_state.ts_submitted = True
            st.session_state.memory.update_daily_progress(games_played=1, add_turn=False)

            detail = result.details[0]
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Accuracy", f"{detail['accuracy_percent']}%")
            with col2:
                st.metric("Speed", f"{detail['wpm']} WPM")

            if detail["accuracy_percent"] >= 95:
                st.success("🎉 Excellent accuracy!")
            elif detail["accuracy_percent"] >= 80:
                st.info("👍 Good job! Keep practicing for higher accuracy.")
            else:
                st.warning("📝 Keep practicing — focus on accuracy first, then speed.")


def _render_error_correction():
    """Error correction game."""
    st.markdown("### 🔍 Error Correction")
    st.markdown("*Find and fix the error in each sentence.*")

    if "ec_game" not in st.session_state:
        st.session_state.ec_game = ErrorCorrectionGame()
    game = st.session_state.ec_game

    if st.button("🎲 New Round", key="ec_new"):
        st.session_state.ec_round = game.new_round(count=4)
        st.session_state.ec_submitted = False

    if "ec_round" in st.session_state and not st.session_state.get("ec_submitted"):
        questions = st.session_state.ec_round
        corrections = []

        for i, q in enumerate(questions):
            st.markdown(f"**{i+1}.** Fix this sentence:")
            st.error(f"❌ {q['sentence']}")
            st.caption(q["hint"])
            correction = st.text_input(
                f"Corrected sentence {i+1}:",
                key=f"ec_{i}",
                placeholder="Type the corrected sentence...",
            )
            corrections.append(correction)

        if st.button("✅ Check Answers", key="ec_check"):
            result = game.check_answers(corrections)
            st.session_state.ec_submitted = True
            st.session_state.memory.update_daily_progress(games_played=1, add_turn=False)

            st.markdown(f'<div class="game-score">{result.score}/{result.total}</div>', unsafe_allow_html=True)

            for detail in result.details:
                if detail["is_correct"]:
                    st.success(f"✅ Correct!")
                else:
                    st.error(f"❌ Correct: {detail['correct_answer']}")
                st.caption(f"📖 {detail['explanation']}")
