"""
Progress Dashboard Page — Track learning progress over time.
"""

import sqlite3
from datetime import date, timedelta

import streamlit as st

import config


def render_progress_page():
    """Render the progress tracking dashboard."""
    st.markdown("## 📊 Progress Dashboard")
    st.markdown("*Track your IELTS preparation journey.*")
    st.markdown("---")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    progress_data = _get_progress_data()
    vocab_data = _get_vocab_data()

    with col1:
        total_words = len(vocab_data)
        mastered = sum(1 for v in vocab_data if v["is_mastered"])
        st.metric("📘 Words Learned", total_words, delta=f"{mastered} mastered")

    with col2:
        total_turns = sum(p.get("total_turns", 0) for p in progress_data)
        st.metric("💬 Total Turns", total_turns)

    with col3:
        total_time = sum(p.get("total_speaking_time_sec", 0) for p in progress_data)
        st.metric("🎙️ Speaking Time", f"{total_time / 60:.0f} min")

    with col4:
        latest_band = 0
        for p in reversed(progress_data):
            if p.get("estimated_band_score"):
                latest_band = p["estimated_band_score"]
                break
        if latest_band > 0:
            st.metric("🎯 Latest Band", f"{latest_band:.1f}")
        else:
            st.metric("🎯 Latest Band", "—")

    st.markdown("---")

    # Vocabulary mastery breakdown
    st.markdown("### 📘 Vocabulary Mastery")

    if vocab_data:
        mastered_words = [v for v in vocab_data if v["is_mastered"]]
        in_progress = [v for v in vocab_data if not v["is_mastered"] and v["correct_uses"] > 0]
        not_started = [v for v in vocab_data if v["correct_uses"] == 0 and not v["is_mastered"]]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**✅ Mastered ({len(mastered_words)})**")
            for v in mastered_words:
                st.markdown(f"- {v['word']}")
        with col2:
            st.markdown(f"**📈 In Progress ({len(in_progress)})**")
            for v in in_progress:
                st.markdown(f"- {v['word']} ({v['correct_uses']}/5)")
        with col3:
            st.markdown(f"**🔲 Not Started ({len(not_started)})**")
            for v in not_started:
                st.markdown(f"- {v['word']}")
    else:
        st.info("Start practicing to see vocabulary progress!")

    st.markdown("---")

    # Daily activity log
    st.markdown("### 📅 Daily Activity")

    if progress_data:
        for entry in reversed(progress_data[-7:]):
            d = entry.get("date", "Unknown")
            turns = entry.get("total_turns", 0)
            time_sec = entry.get("total_speaking_time_sec", 0)
            band = entry.get("estimated_band_score")
            games = entry.get("games_played", 0)

            band_str = f" · Band: {band:.1f}" if band else ""
            st.markdown(
                f"**{d}** — {turns} turns · {time_sec/60:.0f} min speaking · "
                f"{games} games{band_str}"
            )
    else:
        st.info("No activity recorded yet. Start a conversation to begin!")

    # Streak counter
    st.markdown("---")
    st.markdown("### 🔥 Practice Streak")

    streak = _calculate_streak(progress_data)
    if streak > 0:
        st.markdown(f"## 🔥 {streak} day{'s' if streak != 1 else ''}")
        if streak >= 7:
            st.balloons()
            st.success("Amazing! A whole week of practice! Keep it up! 🎉")
        elif streak >= 3:
            st.success("Great consistency! Keep the streak going! 💪")
    else:
        st.markdown("## 🔥 0 days")
        st.caption("Start practicing today to begin your streak!")


def _get_progress_data() -> list[dict]:
    """Get daily progress data from database."""
    try:
        conn = sqlite3.connect(str(config.DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            """SELECT date, total_speaking_time_sec, total_turns,
                      words_practiced, estimated_band_score, games_played
               FROM daily_progress
               ORDER BY date DESC
               LIMIT 30"""
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "date": row[0],
                "total_speaking_time_sec": row[1] or 0,
                "total_turns": row[2] or 0,
                "words_practiced": row[3] or 0,
                "estimated_band_score": row[4],
                "games_played": row[5] or 0,
            }
            for row in rows
        ]
    except Exception:
        return []


def _get_vocab_data() -> list[dict]:
    """Get vocabulary progress data."""
    try:
        return st.session_state.vocab_system.get_word_progress()
    except Exception:
        return []


def _calculate_streak(progress_data: list[dict]) -> int:
    """Calculate the current daily practice streak."""
    if not progress_data:
        return 0

    dates = sorted(set(p["date"] for p in progress_data if p.get("total_turns", 0) > 0))
    if not dates:
        return 0

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # Streak must include today or yesterday
    if dates[-1] not in (today, yesterday):
        return 0

    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        current = date.fromisoformat(dates[i])
        previous = date.fromisoformat(dates[i - 1])
        if (current - previous).days == 1:
            streak += 1
        else:
            break

    return streak
