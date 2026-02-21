"""
Interview Page — Continuous Voice Interview.

Simulates human-to-human interview interaction. Requires no start/stop button.
Automatically proceeds if the user is silent for 15s.
Considers an answer finished if the user pauses for 10s.
"""

import time
import streamlit as st

import config
import base64
import uuid
import streamlit.components.v1 as components
from intelligence import prompts
from engine.turn_manager import TurnManager

# We will need the audio capture and WebRTC setup
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
except ImportError:
    st.error("streamlit-webrtc is required for continuous interview. Please install it.")

def _init_interview_audio():
    """Initialize continuous audio capture and turn manager."""
    from audio.audio_capture import AudioCapture
    from audio.pause_detector import PauseDetector
    from audio.vad import VoiceActivityDetector
    from audio.stt import SpeechToText
    from audio.tts import TextToSpeech
    
    if "interview_audio_capture" not in st.session_state:
        # Custom pause detector: 10 seconds of silence to complete turn
        pause_detector = PauseDetector(pause_threshold_ms=10000)
        vad = VoiceActivityDetector()
        
        capture = AudioCapture(vad=vad, pause_detector=pause_detector)
        st.session_state.interview_audio_capture = capture

    if "interview_stt" not in st.session_state:
        st.session_state.interview_stt = SpeechToText()
        
    if "interview_tts" not in st.session_state:
        st.session_state.interview_tts = TextToSpeech()

    if "interview_turn_manager" not in st.session_state:
        st.session_state.interview_turn_manager = TurnManager(
            audio_capture=st.session_state.interview_audio_capture,
            stt=st.session_state.interview_stt,
            tts=st.session_state.interview_tts,
            state_machine=st.session_state.state_machine,
            buffer_manager=st.session_state.buffer_manager,
            memory=st.session_state.memory,
            llm_generate=_generate_interview_response,
            on_transcription=_on_transcription,
            on_ai_response=_on_ai_response,
            on_state_change=_on_state_change
        )
        
def _generate_interview_response(user_text: str, context: list) -> str:
    """Generate the AI's response as an interviewer."""
    from app import get_llm_instance
    llm = get_llm_instance()
    if not llm:
        return "I'm sorry, I cannot connect to my brain right now."
        
    system_prompt = (
        "You are an expert IELTS examiner conducting a speaking test interview. "
        "Ask questions one by one. If the user answers, follow up naturally or move to the next question. "
        "Keep your responses concise and conversational. Do not write the user's part."
    )
    
    # If the user text is just a placeholder indicating 15s silence
    if user_text.startswith("[SILENCE_TIMEOUT]"):
        user_prompt = "The candidate has been silent for a while. Please ask a follow up question or move to the next topic to encourage them to speak."
    else:
        user_prompt = user_text
        
    response = llm.generate(
        user_message=user_prompt,
        context=context,
        system_prompt=system_prompt
    )
    
    return response

def _on_transcription(text: str, details: dict):
    st.session_state.conversation_history.append({
        "role": "user",
        "content": text,
    })
    
def _on_ai_response(text: str):
    st.session_state.conversation_history.append({
        "role": "assistant",
        "content": text,
    })

def _on_state_change(state_info: dict):
    st.session_state.current_status = state_info.get("status_text", "Ready to start")

def render_interview_page():
    """Render the interview page UI."""
    st.markdown("## 🤝 Continuous Interview")
    st.markdown("*I will ask a question. I will wait for you to answer. If you pause for 10 seconds, I'll assume you have finished answering. If you stay silent for 15 seconds, I'll prompt you.*")

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
    
    # Init audio pipeline
    _init_interview_audio()
    
    capture = st.session_state.interview_audio_capture
    
    # Debug metrics
    if st.session_state.get("interview_started", False):
        stats = capture.get_status()
        st.caption(f"Mic Status: {stats['state']} | Voice Confidence: {stats['vad_confidence']:.2f} | Buffer: {stats['buffer_duration_ms']:.0f}ms")
    
    if not st.session_state.get("interview_started", False):
        st.info("🎙️ **Click 'START' below** to grant microphone access and begin your interview!")

    webrtc_ctx = webrtc_streamer(
        key="interview_mic",
        mode=WebRtcMode.SENDONLY,
        audio_frame_callback=capture.process_audio_frame,
        media_stream_constraints={"audio": True, "video": False},
        desired_playing_state=None,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        async_processing=True,
    )
    
    # Start the interview automatically if history is empty and mic is started
    if not st.session_state.get("interview_started", False) and webrtc_ctx.state.playing:
        st.session_state.interview_started = True
        
        # Ask the first question immediately
        with st.spinner("🧠 Preparing first question..."):
            system_prompt = (
                "You are an expert IELTS examiner conducting a speaking test interview. "
                "Introduce yourself briefly and ask the first question to the candidate. "
                "Keep your responses concise and conversational."
            )
            from app import get_llm_instance
            llm = get_llm_instance()
            if llm:
                response_text = llm.generate(
                    user_message="Hello, I am ready to start the interview.",
                    context=[],
                    system_prompt=system_prompt
                )
                _on_ai_response(response_text)
                
                # Generate audio
                audio_bytes = st.session_state.interview_tts.synthesize_to_wav_bytes(response_text)
                st.session_state.conversation_history[-1]["audio_bytes"] = audio_bytes
                st.session_state.conversation_history[-1]["turn_id"] = str(uuid.uuid4())
                
                estimated_duration = len(audio_bytes) / 32000.0
                st.session_state.ai_speaking_until = time.time() + estimated_duration
                st.session_state.last_activity_time = st.session_state.ai_speaking_until
                
        st.rerun()
    
    if st.session_state.get("interview_started", False):
        
        # Poll turn manager
        turn_manager = st.session_state.interview_turn_manager
        
        # Manage timeouts
        current_time = time.time()
        
        # When does AI finish speaking?
        ai_until = st.session_state.get("ai_speaking_until", 0)
        last_activity = st.session_state.get("last_activity_time", current_time)
        
        # If user is actively speaking, reset the timeout
        if capture.pause_detector.is_user_speaking:
            st.session_state.last_activity_time = current_time
            time_since_activity = 0.0
        elif current_time > ai_until:
            # AI has finished speaking, calculate how long it's been silent
            time_since_activity = current_time - max(last_activity, ai_until)
        else:
            time_since_activity = 0.0
        
        # Check if turn is complete
        turn_result = turn_manager.process_turn()
        
        if turn_result:
            # Turn was processed
            
            # If audio was generated, queue it for autoplay
            if turn_result.get("ai_audio_bytes"):
                audio_bytes = turn_result["ai_audio_bytes"]
                st.session_state.conversation_history[-1]["audio_bytes"] = audio_bytes
                st.session_state.conversation_history[-1]["turn_id"] = str(uuid.uuid4())
                
                estimated_duration = len(audio_bytes) / 32000.0
                st.session_state.ai_speaking_until = time.time() + estimated_duration
                st.session_state.last_activity_time = st.session_state.ai_speaking_until
            else:
                st.session_state.last_activity_time = time.time()
                
            st.rerun()
        elif time_since_activity >= 5.0 and webrtc_ctx.state.playing:
            # 5 seconds of silence timeout
            # Force an AI turn to prompt the user
            st.session_state.last_activity_time = time.time()
            
            with st.spinner("🧠 Generating follow-up..."):
                response_text = _generate_interview_response("[SILENCE_TIMEOUT]", st.session_state.memory.get_context())
                _on_ai_response(response_text)
                
                # generate audio
                audio_bytes = st.session_state.interview_tts.synthesize_to_wav_bytes(response_text)
                st.session_state.conversation_history[-1]["audio_bytes"] = audio_bytes
                st.session_state.conversation_history[-1]["turn_id"] = str(uuid.uuid4())
                
                estimated_duration = len(audio_bytes) / 32000.0
                st.session_state.ai_speaking_until = time.time() + estimated_duration
                st.session_state.last_activity_time = st.session_state.ai_speaking_until
            
            st.rerun()

    # ── Conversation history ──────
    chat_container = st.container()
    
    with chat_container:
        for turn in st.session_state.conversation_history:
            if turn["content"].startswith("[SILENCE_TIMEOUT]"):
                continue # don't show internal marker
                
            with st.chat_message(turn["role"], avatar="🎓" if turn["role"] == "assistant" else "🗣️"):
                st.write(turn["content"])
                # Play audio if available
                if turn.get("audio_bytes"):
                    # Standard viewer
                    st.audio(turn["audio_bytes"], format="audio/wav")
                    
                    # Persistent JS Autoplay
                    turn_id = turn.get("turn_id", "unknown")
                    b64_audio = base64.b64encode(turn["audio_bytes"]).decode("utf-8")
                    js_code = f"""
                    <script>
                        if (!window.parent.playedAudio) window.parent.playedAudio = {{}};
                        if (!window.parent.playedAudio['{turn_id}']) {{
                            var snd = new Audio("data:audio/wav;base64,{b64_audio}");
                            snd.play();
                            window.parent.playedAudio['{turn_id}'] = true;
                        }}
                    </script>
                    """
                    components.html(js_code, height=0, width=0)

    # Auto-refresh loop to check WebRTC frames / timeout
    if st.session_state.get("interview_started", False) and webrtc_ctx.state.playing:
        time.sleep(0.5)
        st.rerun()
