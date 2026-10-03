import os
import json
import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM THEMING (UI/UX HARDENING)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FlashMind Pro | Executive AI Learning Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern typography, unified spacing, and card animations
st.markdown("""
<style>
    /* Global Page Styling */
    .stApp {
        background-color: #0b0e14;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* App Title Header */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #818CF8 0%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .brand-subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    /* Flashcard Container styling */
    .flashcard-card {
        background: #151c28;
        border: 1px solid #283447;
        border-radius: 16px;
        padding: 40px 30px;
        min-height: 240px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        transition: all 0.25s ease-in-out;
        margin-bottom: 10px;
    }
    .flashcard-card:hover {
        border-color: #6366F1;
        box-shadow: 0 12px 30px -5px rgba(99, 102, 241, 0.25);
    }
    
    /* Badges */
    .card-badge {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 5px 14px;
        border-radius: 20px;
        margin-bottom: 18px;
    }
    .badge-question { background-color: #1E1B4B; color: #A5B4FC; border: 1px solid #4338CA; }
    .badge-answer { background-color: #064E3B; color: #6EE7B7; border: 1px solid #047857; }

    /* Card Typography */
    .card-text-content {
        font-size: 1.3rem;
        font-weight: 500;
        color: #F8FAFC;
        line-height: 1.6;
    }

    /* Analytics Cards */
    .metric-box {
        background-color: #151c28;
        border: 1px solid #283447;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to prevent Cross-Site Scripting (XSS)
def sanitize_text(input_str: str) -> str:
    return html.escape(str(input_str))

# -----------------------------------------------------------------------------
# 2. SESSION STATE & SECURITY INITIALIZATION
# -----------------------------------------------------------------------------
if "user_api_key" not in st.session_state:
    st.session_state.user_api_key = os.environ.get("GEMINI_API_KEY", "")
if "cards" not in st.session_state:
    st.session_state.cards = []
if "generated_notes" not in st.session_state:
    st.session_state.generated_notes = ""
if "user_notes" not in st.session_state:
    st.session_state.user_notes = {}
if "mastery" not in st.session_state:
    st.session_state.mastery = {}
if "difficulty" not in st.session_state:
    st.session_state.difficulty = {}
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROL PANEL
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ System Control")
    
    # API Key Input
    key_input = st.text_input(
        "Gemini API Key:",
        value=st.session_state.user_api_key,
        type="password",
        help="API Key is stored strictly in temporary session state and never saved on disk."
    )
    if key_input != st.session_state.user_api_key:
        st.session_state.user_api_key = key_input
        st.rerun()

    if st.button("🔒 Reset Session Data", use_container_width=True):
        st.session_state.user_api_key = ""
        st.session_state.cards = []
        st.session_state.generated_notes = ""
        st.rerun()

    st.markdown("---")
    st.markdown("### 🎴 Deck Settings")
    card_count = st.slider("Target Card Count", min_value=3, max_value=10, value=5)
    target_role = st.selectbox("Depth Focus:", [
        "Executive Summary (High-Level)",
        "Technical Deep-Dive",
        "Conceptual Fundamentals",
        "Interview Prep"
    ])

# Guard clause for API Key
if not st.session_state.user_api_key:
    st.markdown('<div class="brand-title">🧠 FlashMind Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Secure AI Active Recall & Study Guide Hub</div>', unsafe_allow_html=True)
    st.warning("⚠️ **Security Action Required:** Please input your Gemini API Key in the left sidebar control panel to unlock the workspace.")
    st.stop()

# Initialize Client
try:
    client = genai.Client(api_key=st.session_state.user_api_key)
except Exception as err:
    st.error(f"Failed to connect to Gemini API: {err}")
    st.stop()

# -----------------------------------------------------------------------------
# 4. STRUCTURED DATA SCHEMAS
# -----------------------------------------------------------------------------
class Flashcard(BaseModel):
    question: str = Field(description="Front card question or concept")
    answer: str = Field(description="Back card concise explanation")

class FlashcardSet(BaseModel):
    topic: str = Field(description="Topic title")
    cards: list[Flashcard] = Field(description="Generated flashcard list")

# -----------------------------------------------------------------------------
# 5. HEADER & INPUT DRAWER
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-title">🧠 FlashMind Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-subtitle">AI-Powered Active Recall Engine & Comprehensive Study Guide Synthesizer</div>', unsafe_allow_html=True)

with st.expander("📥 Generate Flashcard Deck from Topic or File", expanded=not bool(st.session_state.cards)):
    in_tab1, in_tab2 = st.tabs(["✍️ Topic / Raw Text", "📁 Upload File (.txt)"])
    study_input = ""

    with in_tab1:
        text_input = st.text_area(
            "Enter topic or study source text:",
            height=100,
            max_chars=4000,
            placeholder="E.g., System Design Load Balancers, Transformer Neural Networks, Microservice Security..."
        )
        if text_input:
            study_input = text_input

    with in_tab2:
        uploaded_file = st.file_uploader("Upload document (.txt):", type=["txt"])
        if uploaded_file is not None:
            if uploaded_file.size > 1 * 1024 * 1024:
                st.error("File size exceeds 1MB limit.")
            else:
                study_input = uploaded_file.read().decode("utf-8")[:4000]

    if st.button("🚀 Generate Flashcard Deck", type="primary", use_container_width=True):
        if not study_input.strip():
            st.warning("Please provide topic text or upload a file first.")
        else:
            with st.spinner("Synthesizing learning deck..."):
                prompt = f"""
                Synthesize exactly {card_count} flashcards based on the provided material.
                Depth Mode: {target_role}.
                Return high-yield questions and accurate, educational answers.

                Source Content:
                {study_input}
                """

                models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
                response = None
                last_err = None

                for model in models_to_try:
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=FlashcardSet,
                                temperature=0.2,
                            )
                        )
                        if response and response.text:
                            break
                    except Exception as e:
                        last_err = e
                        continue

                if response and response.text:
                    try:
                        data = json.loads(response.text)
                        st.session_state.cards = data.get("cards", [])
                        st.session_state.current_index = 0
                        st.session_state.show_answer = False
                        st.session_state.user_notes = {i: "" for i in range(len(st.session_state.cards))}
                        st.session_state.mastery = {i: "Unread" for i in range(len(st.session_state.cards))}
                        st.session_state.difficulty = {i: "Medium" for i in range(len(st.session_state.cards))}
                        st.success(f"Generated {len(st.session_state.cards)} cards!")
                        st.rerun()
                    except Exception as p_err:
                        st.error(f"Error parsing generated data: {p_err}")
                else:
                    st.error(f"Generation failed: {last_err}")

# -----------------------------------------------------------------------------
# 6. WORKSPACE TABS ARCHITECTURE
# -----------------------------------------------------------------------------
tab_canvas, tab_notes_gen, tab_card_notes, tab_analytics, tab_export = st.tabs([
    "🎴 Active Recall Deck", 
    "📑 Smart Notes Synthesizer",
    "✏️ Card Annotations", 
    "📊 Session Analytics", 
    "💾 Export & Backup"
])

# --- TAB 1: Flashcard Canvas ---
with tab_canvas:
    if st.session_state.cards:
        total_cards = len(st.session_state.cards)
        current_idx = st.session_state.current_index
        card = st.session_state.cards[current_idx]

        st.progress((current_idx + 1) / total_cards)
        st.caption(f"Card {current_idx + 1} of {total_cards}")

        safe_q = sanitize_text(card['question'])
        safe_a = sanitize_text(card['answer'])

        if not st.session_state.show_answer:
            st.markdown(
                f"""
                <div class="flashcard-card">
                    <span class="card-badge badge-question">Question / Concept</span>
                    <div class="card-text-content">{safe_q}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            spoken_text = card['question']
        else:
            st.markdown(
                f"""
                <div class="flashcard-card" style="border-color: #059669;">
                    <span class="card-badge badge-answer">Answer / Explanation</span>
                    <div class="card-text-content">{safe_a}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            spoken_text = card['answer']

        # Browser Text-to-Speech (Audio)
        safe_speech_str = sanitize_text(spoken_text.replace("'", "\\'").replace("\n", " "))
        tts_script = f"""
            <script>
            function speakCard() {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance('{safe_speech_str}');
                msg.rate = 0.95;
                window.speechSynthesis.speak(msg);
            }}
            </script>
            <button onclick="speakCard()" style="background: #1E293B; color: #CBD5E1; border: 1px solid #334155; padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; width: 100%; margin-top: 5px;">
                🔊 Listen to Text
            </button>
        """
        components.html(tts_script, height=45)

        # Deck Navigation Controls
        btn_c1, btn_c2, btn_c3 = st.columns([1, 2, 1])
        with btn_c1:
            if st.button("⬅️ Previous", disabled=(current_idx == 0), use_container_width=True):
                st.session_state.current_index -= 1
                st.session_state.show_answer = False
                st.rerun()

        with btn_c2:
            lbl = "🙈 Hide Answer" if st.session_state.show_answer else "👁 Reveal Answer"
            if st.button(lbl, use_container_width=True, type="secondary"):
                st.session_state.show_answer = not st.session_state.show_answer
                st.rerun()

        with btn_c3:
            if st.button("Next ➡️", disabled=(current_idx == total_cards - 1), use_container_width=True):
                st.session_state.current_index += 1
                st.session_state.show_answer = False
                st.rerun()

        # Mastery Assessment Row
        st.markdown("---")
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            if st.button("✅ Mark Mastered", use_container_width=True):
                st.session_state.mastery[current_idx] = "Mastered"
                st.rerun()
        with m_col2:
            if st.button("⚠️ Needs Review", use_container_width=True):
                st.session_state.mastery[current_idx] = "Review Needed"
                st.rerun()
        with m_col3:
            st.session_state.difficulty[current_idx] = st.selectbox(
                "Difficulty Tag:",
                ["Easy", "Medium", "Hard"],
                index=["Easy", "Medium", "Hard"].index(st.session_state.difficulty.get(current_idx, "Medium")),
                key=f"tag_diff_{current_idx}"
            )
    else:
        st.info("👈 Use the top input box to generate a deck and start reviewing.")

# --- TAB 2: Smart Notes Synthesizer ---
with tab_notes_gen:
    st.subheader("📑 Custom Study Note Generator")
    st.write("Generate structured Markdown study guides for any topic based on your target learning goal.")

    n_col1, n_col2 = st.columns([2, 1])
    with n_col1:
        note_topic_input = st.text_input(
            "Topic Name:",
            placeholder="E.g., Docker Containerization, CAP Theorem, Database Indexing, REST API Best Practices..."
        )
    with n_col2:
        note_goal = st.selectbox(
            "Learning Goal / Depth:",
            [
                "Quick Basics (5-Min Overview)",
                "Deep Comprehensive Notes (Complete Mastery)",
                "Interview Preparation (High-Yield & Q&A)",
                "Exam Cheat Sheet (Definitions & Formulas)"
            ]
        )

    if st.button("✨ Synthesize Topic Notes", type="primary", use_container_width=True):
        if not note_topic_input.strip():
            st.warning("Please specify a topic name.")
        else:
            with st.spinner(f"Writing study notes for '{note_topic_input}'..."):
                note_prompt = f"""
                You are an expert technical educator.
                Generate high-yield, cleanly structured Markdown notes for the topic: "{note_topic_input}".
                Target Goal: {note_goal}.

                Required Structure:
                1. 📌 Executive Summary & Core Concept
                2. 🔑 Key Principles & Terminology
                3. 🚀 Architectural Patterns / Real-World Usage
                4. 🎯 Common Pitfalls & Edge Cases
                5. 💡 Top Interview Questions & Ideal Answers
                """
                note_models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
                res = None
                last_note_err = None

                for model_name in note_models:
                    try:
                        res = client.models.generate_content(
                            model=model_name,
                            contents=note_prompt,
                            config=types.GenerateContentConfig(temperature=0.2)
                        )
                        if res and res.text:
                            break
                    except Exception as e:
                        last_note_err = e
                        continue

                if res and res.text:
                    st.session_state.generated_notes = res.text
                    st.success("Study notes synthesized!")
                else:
                    st.error(f"Service busy. Please click the button again in 5 seconds. ({last_note_err})")

    if st.session_state.generated_notes:
        st.markdown("---")
        st.markdown(st.session_state.generated_notes)
        st.download_button(
            label="📥 Download Study Guide (.md)",
            data=st.session_state.generated_notes.encode("utf-8"),
            file_name=f"study_guide_{note_topic_input.replace(' ', '_').lower()}.md",
            mime="text/markdown",
            use_container_width=True
        )

# --- TAB 3: Card Annotations ---
with tab_card_notes:
    if st.session_state.cards:
        c_idx = st.session_state.current_index
        active_card = st.session_state.cards[c_idx]

        st.subheader(f"✏️ Notes for Card #{c_idx + 1}")
        st.info(f"**Question:** {active_card['question']}")

        existing_note = st.session_state.user_notes.get(c_idx, "")
        user_note_entry = st.text_area(
            "Add personal memory hooks, code snippets, or hints:",
            value=existing_note,
            height=160,
            max_chars=1000,
            key=f"area_note_{c_idx}"
        )
        st.session_state.user_notes[c_idx] = user_note_entry
    else:
        st.info("No active flashcard deck loaded.")

# --- TAB 4: Session Analytics ---
with tab_analytics:
    if st.session_state.cards:
        st.subheader("📊 Session Performance & Mastery Tracking")
        tot = len(st.session_state.cards)
        m_cnt = sum(1 for s in st.session_state.mastery.values() if s == "Mastered")
        r_cnt = sum(1 for s in st.session_state.mastery.values() if s == "Review Needed")
        p_cnt = tot - (m_cnt + r_cnt)

        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#34D399">{m_cnt}</div><div class="metric-label">Mastered</div></div>', unsafe_allow_html=True)
        with col_a2:
            st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#F87171">{r_cnt}</div><div class="metric-label">Needs Review</div></div>', unsafe_allow_html=True)
        with col_a3:
            st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#FBBF24">{p_cnt}</div><div class="metric-label">Pending Review</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        summary_rows = []
        for idx, c in enumerate(st.session_state.cards):
            summary_rows.append({
                "Card": f"#{idx + 1}",
                "Question": c["question"],
                "Mastery": st.session_state.mastery.get(idx, "Unread"),
                "Difficulty": st.session_state.difficulty.get(idx, "Medium")
            })
        st.dataframe(pd.DataFrame(summary_rows))
    else:
        st.info("No analytics to report yet.")

# --- TAB 5: Export & Backup ---
with tab_export:
    if st.session_state.cards:
        st.subheader("💾 Export & Integration Hub")
        st.write("Export your flashcards, user notes, and review tags to standard tabular data files.")

        data_export = []
        for idx, c in enumerate(st.session_state.cards):
            data_export.append({
                "Index": idx + 1,
                "Question": c["question"],
                "Answer": c["answer"],
                "Difficulty": st.session_state.difficulty.get(idx, "Medium"),
                "Mastery State": st.session_state.mastery.get(idx, "Unread"),
                "User Notes": st.session_state.user_notes.get(idx, "")
            })

        df_out = pd.DataFrame(data_export)
        csv_bytes = df_out.to_csv(index=False).encode('utf-8')
        json_bytes = json.dumps(data_export, indent=2).encode('utf-8')

        ex_c1, ex_c2 = st.columns(2)
        with ex_c1:
            st.download_button(
                label="📥 Download CSV Deck",
                data=csv_bytes,
                file_name="flashmind_deck.csv",
                mime="text/csv",
                use_container_width=True
            )
        with ex_c2:
            st.download_button(
                label="📥 Download JSON Deck",
                data=json_bytes,
                file_name="flashmind_deck.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("No active deck available for export.")