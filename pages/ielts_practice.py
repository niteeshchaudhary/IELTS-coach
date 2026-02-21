"""
IELTS Practice Page — Speaking, Listening, Reading test modules.
"""

import time
import streamlit as st

from intelligence.ielts_guidance import IELTSGuidance
from intelligence import prompts


def render_ielts_practice_page():
    """Render the IELTS practice page."""
    st.markdown("## 🧪 IELTS Practice")
    st.markdown("*Practice for your IELTS exam with simulated test sections.*")
    st.markdown("---")

    section = st.selectbox(
        "Choose a section:",
        ["🗣️ Speaking Practice", "👂 Listening Practice", "📖 Reading Practice"],
    )

    if section == "🗣️ Speaking Practice":
        _render_speaking_practice()
    elif section == "👂 Listening Practice":
        _render_listening_practice()
    elif section == "📖 Reading Practice":
        _render_reading_practice()


def _render_speaking_practice():
    """IELTS Speaking practice with Part 1, 2, and 3."""
    st.markdown("### 🗣️ Speaking Practice")

    part = st.radio("Select Part:", ["Part 1", "Part 2", "Part 3"], horizontal=True)
    topics = IELTSGuidance.get_speaking_topics()

    if part == "Part 1":
        st.markdown("#### Part 1 — Introduction & Interview")
        st.info("The examiner asks general questions about familiar topics. Practice giving extended answers.")

        topic = st.selectbox("Choose a topic:", topics["part1"])

        if st.button("Start Practice", key="sp1_start"):
            st.session_state.sp_active = True
            st.session_state.sp_part = 1
            st.session_state.sp_topic = topic

        if st.session_state.get("sp_active") and st.session_state.get("sp_part") == 1:
            st.markdown(f"**Topic: {st.session_state.sp_topic}**")
            st.markdown("---")

            # Generate questions using LLM or use static ones
            part1_questions = _get_part1_questions(st.session_state.sp_topic)

            for i, question in enumerate(part1_questions):
                st.markdown(f"**Q{i+1}:** {question}")
                answer = st.text_area(
                    f"Your answer to Q{i+1}:",
                    key=f"sp1_a{i}",
                    height=80,
                    placeholder="Speak your answer or type it here...",
                )

            if st.button("📊 Get Score", key="sp1_score"):
                all_answers = []
                for i in range(len(part1_questions)):
                    a = st.session_state.get(f"sp1_a{i}", "")
                    if a:
                        all_answers.append(a)

                if all_answers:
                    _show_score(
                        " ".join(all_answers),
                        topic=st.session_state.sp_topic,
                    )

    elif part == "Part 2":
        st.markdown("#### Part 2 — Individual Long Turn (Cue Card)")
        st.info("You have 1 minute to prepare, then speak for 1–2 minutes on the topic.")

        part2_topics = topics["part2"]
        topic_names = [t["topic"] for t in part2_topics]
        selected_idx = st.selectbox("Choose a cue card:", range(len(topic_names)), format_func=lambda x: topic_names[x])
        selected_topic = part2_topics[selected_idx]

        st.markdown(f"### 📋 {selected_topic['topic']}")
        st.markdown("You should say:")
        for point in selected_topic["points"]:
            st.markdown(f"- {point}")

        st.markdown("---")

        if st.button("⏱️ Start 1-Minute Prep", key="sp2_prep"):
            st.session_state.sp2_prep_start = time.time()
            st.info("⏱️ Preparation time started! Make notes below.")

        notes = st.text_area(
            "Your preparation notes:",
            key="sp2_notes",
            height=80,
            placeholder="Jot down key points...",
        )

        st.markdown("**Your response (1–2 minutes):**")
        response = st.text_area(
            "Speak about the topic:",
            key="sp2_response",
            height=200,
            placeholder="Type or dictate your 1-2 minute response...",
        )

        if st.button("📊 Get Score", key="sp2_score") and response:
            _show_score(
                response,
                topic=selected_topic["topic"],
                duration=120,
            )

    elif part == "Part 3":
        st.markdown("#### Part 3 — Two-way Discussion")
        st.info("The examiner asks deeper, more abstract questions. Express opinions and compare perspectives.")

        theme = st.selectbox("Choose a theme:", topics["part3_themes"])

        part3_questions = _get_part3_questions(theme)

        for i, question in enumerate(part3_questions):
            st.markdown(f"**Q{i+1}:** {question}")
            answer = st.text_area(
                f"Your answer to Q{i+1}:",
                key=f"sp3_a{i}",
                height=100,
                placeholder="Give a detailed, analytical response...",
            )

        if st.button("📊 Get Score", key="sp3_score"):
            all_answers = []
            for i in range(len(part3_questions)):
                a = st.session_state.get(f"sp3_a{i}", "")
                if a:
                    all_answers.append(a)

            if all_answers:
                _show_score(
                    " ".join(all_answers),
                    topic=theme,
                )


@st.cache_data(show_spinner="Synthesizing audio...")
def _generate_audio(text: str) -> tuple[bytes, str]:
    from audio.tts import TextToSpeech
    tts = TextToSpeech()
    return tts.synthesize_to_playable_bytes(text)


def _render_listening_practice():
    """IELTS Listening practice section."""
    st.markdown("### 👂 Listening Practice")
    
    content = IELTSGuidance.get_listening_practice_content()
    st.markdown(f"#### {content['title']}")
    
    st.info("Listen to the audio recording and answer the questions below.")
    
    audio_bytes, mime_type = _generate_audio(content["audio_text"])
    if audio_bytes:
        st.audio(audio_bytes, format=mime_type)
    else:
        st.error("Audio synthesis failed.")

    with st.expander("Show Transcript (for review)", expanded=False):
        st.write(content["audio_text"])
        
    st.markdown("---")
    st.markdown("#### Questions")
    
    answers = {}
    for i, q in enumerate(content["questions"]):
        st.markdown(f"**Q{i+1}:** {q['question']}")
        
        if q["type"] in ["multiple_choice", "true_false_not_given"]:
            answers[q["id"]] = st.radio(
                "Select your answer:",
                options=q["options"],
                key=f"listening_q_{q['id']}",
                index=None
            )
        st.markdown("")
        
    if st.button("📊 Submit Answers", key="listening_submit"):
        st.markdown("---")
        st.markdown("### 📝 Results")
        
        score = 0
        total = len(content["questions"])
        
        for i, q in enumerate(content["questions"]):
            user_ans = answers.get(q["id"])
            correct_ans = q["answer"]
            
            if user_ans == correct_ans:
                st.success(f"**Q{i+1}: Correct!**")
                score += 1
            else:
                st.error(f"**Q{i+1}: Incorrect.** Correct Answer: {correct_ans}")
                
            st.info(f"**Explanation:** {q['explanation']}")
            st.markdown(" ")
            
        st.metric("Total Score", f"{score} / {total}")



def _render_reading_practice():
    """IELTS Reading practice section."""
    st.markdown("### 📖 Reading Practice")
    
    content = IELTSGuidance.get_reading_practice_content()
    
    st.markdown(f"#### {content['title']}")
    
    with st.expander("Read Passage", expanded=True):
        st.write(content["passage"])
        
    st.markdown("---")
    st.markdown("#### Questions")
    
    answers = {}
    for i, q in enumerate(content["questions"]):
        st.markdown(f"**Q{i+1}:** {q['question']}")
        
        if q["type"] in ["multiple_choice", "true_false_not_given"]:
            answers[q["id"]] = st.radio(
                "Select your answer:",
                options=q["options"],
                key=f"reading_q_{q['id']}",
                index=None
            )
        st.markdown("")
        
    if st.button("📊 Submit Answers", key="reading_submit"):
        st.markdown("---")
        st.markdown("### 📝 Results")
        
        score = 0
        total = len(content["questions"])
        
        for i, q in enumerate(content["questions"]):
            user_ans = answers.get(q["id"])
            correct_ans = q["answer"]
            
            if user_ans == correct_ans:
                st.success(f"**Q{i+1}: Correct!**")
                score += 1
            else:
                st.error(f"**Q{i+1}: Incorrect.** Correct Answer: {correct_ans}")
                
            st.info(f"**Explanation:** {q['explanation']}")
            st.markdown(" ")
            
        st.metric("Total Score", f"{score} / {total}")


def _get_part1_questions(topic: str) -> list[str]:
    """Get Part 1 questions for a topic."""
    default_questions = {
        "Hometown": [
            "Where is your hometown?",
            "What do you like most about your hometown?",
            "Has your hometown changed much in recent years?",
            "Would you recommend your hometown to visitors?",
        ],
        "Work or Studies": [
            "Do you work or are you a student?",
            "What do you like about your work/studies?",
            "What are the challenges?",
            "What would you like to change about your work/studies?",
        ],
    }
    return default_questions.get(topic, [
        f"Can you tell me about your experience with {topic.lower()}?",
        f"How often do you engage with {topic.lower()}?",
        f"What do you enjoy most about {topic.lower()}?",
        f"Has your interest in {topic.lower()} changed over time?",
    ])


def _get_part3_questions(theme: str) -> list[str]:
    """Get Part 3 discussion questions for a theme."""
    default_questions = [
        f"What are the main issues related to {theme.lower()} in your country?",
        f"How has {theme.lower()} changed compared to the past?",
        f"What role should governments play in addressing {theme.lower()}?",
        f"How do you think {theme.lower()} will change in the future?",
    ]
    return default_questions


def _show_score(text: str, topic: str = "", duration: float = 0):
    """Display IELTS band score evaluation."""
    st.markdown("---")
    st.markdown("### 📊 Band Score Estimate")

    scorer = st.session_state.get("ielts_scorer")
    if scorer:
        with st.spinner("Evaluating your response..."):
            result = scorer.evaluate(text, duration, topic)

        if result and result.get("overall_band", 0) > 0:
            st.markdown(f"## Overall Band: **{result['overall_band']:.1f}**")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                fc = result.get("fluency_coherence", {})
                st.metric("Fluency & Coherence", f"{fc.get('score', 0):.1f}")
                st.caption(fc.get("feedback", ""))
            with col2:
                lr = result.get("lexical_resource", {})
                st.metric("Lexical Resource", f"{lr.get('score', 0):.1f}")
                st.caption(lr.get("feedback", ""))
            with col3:
                gr = result.get("grammatical_range", {})
                st.metric("Grammar", f"{gr.get('score', 0):.1f}")
                st.caption(gr.get("feedback", ""))
            with col4:
                p = result.get("pronunciation", {})
                st.metric("Pronunciation", f"{p.get('score', 0):.1f}")
                st.caption(p.get("feedback", ""))

            if result.get("strengths"):
                st.success("**Strengths:** " + ", ".join(result["strengths"]))
            if result.get("improvements"):
                st.warning("**Areas to improve:** " + ", ".join(result["improvements"]))
        else:
            st.info("Please provide more text for a meaningful evaluation.")
    else:
        st.warning("IELTS scorer not available. Configure your LLM provider.")
