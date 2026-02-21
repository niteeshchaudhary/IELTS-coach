"""
IELTS Guidance Page — Comprehensive exam preparation guide.
"""

import streamlit as st

from intelligence.ielts_guidance import IELTSGuidance


def render_guidance_page():
    """Render the IELTS guidance page."""
    st.markdown("## 📖 IELTS Speaking Guide")
    st.markdown("*Everything you need to know about the IELTS Speaking test.*")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Exam Format",
        "📊 Band Criteria",
        "⚠️ Common Mistakes",
        "📅 Daily Plan",
        "🎯 Exam Day Tips",
    ])

    with tab1:
        _render_exam_format()

    with tab2:
        _render_band_criteria()

    with tab3:
        _render_common_mistakes()

    with tab4:
        _render_daily_plan()

    with tab5:
        _render_exam_day_tips()


def _render_exam_format():
    """Display IELTS Speaking exam format."""
    st.markdown("### 📋 IELTS Speaking Exam Format")

    exam = IELTSGuidance.get_exam_format()
    st.markdown(f"**Overview:** {exam['overview']}")

    for part in exam["parts"]:
        with st.expander(f"**{part['name']}** ({part['duration']})", expanded=True):
            st.markdown(part["description"])
            st.markdown("**Tips:**")
            for tip in part["tips"]:
                st.markdown(f"- {tip}")


def _render_band_criteria():
    """Display IELTS band score criteria."""
    st.markdown("### 📊 Band Score Criteria")

    criteria = IELTSGuidance.get_band_criteria()

    for c in criteria:
        with st.expander(f"**{c['criterion']}** ({c['weight']})", expanded=True):
            for band_range, desc in c["bands"].items():
                st.markdown(f"**Band {band_range}:** {desc}")

            st.markdown("**💡 Tips for improvement:**")
            for tip in c["tips"]:
                st.markdown(f"- {tip}")


def _render_common_mistakes():
    """Display common IELTS speaking mistakes."""
    st.markdown("### ⚠️ Common Mistakes to Avoid")

    mistakes = IELTSGuidance.get_common_mistakes()

    for m in mistakes:
        with st.expander(f"❌ {m['mistake']}"):
            st.error(f"**Why it's bad:** {m['why_bad']}")
            st.success(f"**How to fix:** {m['fix']}")


def _render_daily_plan():
    """Display suggested daily preparation plan."""
    st.markdown("### 📅 Suggested Daily Plan")

    plan = IELTSGuidance.get_daily_plan()

    for step in plan:
        st.markdown(f"**{step['time']}** — {step['activity']}")

    st.info(
        "💡 Consistency is key! Even 15 minutes of daily practice "
        "is better than 2 hours once a week."
    )


def _render_exam_day_tips():
    """Display exam day tips."""
    st.markdown("### 🎯 Exam Day Tips")

    tips = IELTSGuidance.get_exam_day_tips()

    for i, tip in enumerate(tips, 1):
        st.markdown(f"**{i}.** {tip}")

    st.success(
        "🌟 Remember: The examiner WANTS you to do well. "
        "Stay calm, be natural, and show your best English!"
    )
