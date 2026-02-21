"""
🎙️ IELTS English Speaking Coach — Main Application

Voice-first AI tutor for IELTS speaking practice.
Run with: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import config
from intelligence.vocabulary import VocabularySystem
from intelligence.llm_engine import get_llm
from intelligence.vocab_detector import VocabDetector
from intelligence.ielts_scorer import IELTSScorer
from engine.memory import ConversationMemory
from engine.conversation_state import ConversationStateMachine
from engine.buffer_manager import BufferManager


def init_session_state():
    """Initialize all session state variables on first load."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        
        username = st.session_state.get("username", "default")
        db_path_str = str(config.get_db_path(username))

        # Core systems
        st.session_state.memory = ConversationMemory(db_path=db_path_str)
        st.session_state.state_machine = ConversationStateMachine()
        st.session_state.buffer_manager = BufferManager()
        st.session_state.vocab_system = VocabularySystem(db_path=db_path_str)

        # LLM (lazy — initialized on first use)
        st.session_state.llm = None
        st.session_state.vocab_detector = VocabDetector()
        st.session_state.ielts_scorer = IELTSScorer()

        # Daily vocabulary
        st.session_state.daily_words = st.session_state.vocab_system.get_daily_words()
        st.session_state.memory.set_daily_vocab(
            st.session_state.vocab_system.get_daily_word_names()
        )

        # Conversation UI state
        st.session_state.conversation_history = []
        st.session_state.current_status = "Ready to start"

        # Audio state
        st.session_state.audio_models_loaded = False


def get_llm_instance():
    """Get or create the LLM instance."""
    if st.session_state.llm is None:
        try:
            st.session_state.llm = get_llm()
            st.session_state.vocab_detector.set_llm(st.session_state.llm)
            st.session_state.ielts_scorer.set_llm(st.session_state.llm)
            st.session_state.vocab_system.set_llm(st.session_state.llm)
        except Exception as e:
            st.error(f"Failed to initialize LLM: {e}")
            return None
    return st.session_state.llm


def main():
    """Main application entry point."""
    # Page config
    st.set_page_config(
        page_title=config.APP_TITLE,
        page_icon=config.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
    <style>
        /* Main styling */
        .main-header {
            text-align: center;
            padding: 1rem 0;
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-listening { background: #e8f5e9; color: #2e7d32; }
        .status-thinking { background: #fff3e0; color: #ef6c00; }
        .status-speaking { background: #e3f2fd; color: #1565c0; }
        .status-idle { background: #f5f5f5; color: #616161; }

        /* Vocab card */
        .vocab-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 1rem;
            margin: 0.5rem 0;
        }
        .vocab-card h3 { color: white !important; margin: 0; }
        .vocab-card p { color: rgba(255,255,255,0.9); margin: 0.25rem 0; }

        /* Chat messages */
        .user-message {
            background: #e3f2fd;
            padding: 1rem;
            border-radius: 1rem 1rem 0.25rem 1rem;
            margin: 0.5rem 0;
        }
        .ai-message {
            background: #f3e5f5;
            padding: 1rem;
            border-radius: 1rem 1rem 1rem 0.25rem;
            margin: 0.5rem 0;
        }

        /* Game styling */
        .game-score {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
        }

        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # Login Flow
    if "username" not in st.session_state:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{config.APP_ICON} Welcome to IELTS Coach</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Please login to continue and track your personal progress.</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Login")
            with st.form("login_form"):
                username_input = st.text_input("Username", placeholder="Enter your username")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    if username_input.strip():
                        st.session_state.username = username_input.strip()
                        st.rerun()
                    else:
                        st.error("Please enter a valid username.")
        return

    # Initialize session state (only runs after login)
    init_session_state()

    # Sidebar navigation
    st.sidebar.markdown(f"# {config.APP_ICON} IELTS Coach")
    st.sidebar.markdown(f"**👤 User:** {st.session_state.username}")
    if st.sidebar.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        options=[
            "🎙️ Conversation",
            "📘 Word of the Day",
            "🎮 Games",
            "🧪 IELTS Practice",
            "📊 Progress",
            "📖 IELTS Guide",
        ],
        index=0,
    )

    # Daily vocab in sidebar with pronunciation
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📘 Today's Words")
    for idx, word_data in enumerate(st.session_state.daily_words):
        word_col, speak_col = st.sidebar.columns([4, 1])
        with word_col:
            st.markdown(
                f"**{word_data['word']}** (Band {word_data.get('band_level', '?')})"
            )
        with speak_col:
            if st.button("🔊", key=f"sidebar_pronounce_{idx}", help=f"Hear '{word_data['word']}'"):
                from audio.tts import TextToSpeech
                if "tts" not in st.session_state:
                    st.session_state.tts = TextToSpeech()
                audio, mime = st.session_state.tts.synthesize_to_playable_bytes(
                    f"{word_data['word']}. {word_data['word']}."
                )
                st.session_state[f"sidebar_audio_{idx}"] = audio
                st.session_state[f"sidebar_mime_{idx}"] = mime

        st.sidebar.caption(word_data["meaning"])
        if f"sidebar_audio_{idx}" in st.session_state and st.session_state[f"sidebar_audio_{idx}"]:
            st.sidebar.audio(
                st.session_state[f"sidebar_audio_{idx}"],
                format=st.session_state.get(f"sidebar_mime_{idx}", "audio/mp3"),
            )

    # Route to selected page
    if page == "🎙️ Conversation":
        from pages.conversation import render_conversation_page
        render_conversation_page()
    elif page == "📘 Word of the Day":
        from pages.vocabulary import render_vocabulary_page
        render_vocabulary_page()
    elif page == "🎮 Games":
        from pages.games import render_games_page
        render_games_page()
    elif page == "🧪 IELTS Practice":
        from pages.ielts_practice import render_ielts_practice_page
        render_ielts_practice_page()
    elif page == "📊 Progress":
        from pages.progress import render_progress_page
        render_progress_page()
    elif page == "📖 IELTS Guide":
        from pages.guidance import render_guidance_page
        render_guidance_page()


if __name__ == "__main__":
    main()
