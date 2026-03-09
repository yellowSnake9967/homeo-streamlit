import os
import random
import string
import time
from datetime import datetime

import streamlit as st
from ai_engine import run_query

# ==========================================================
# PASSWORD PROTECTION
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.set_page_config(page_title="Restricted Access", layout="centered")
    st.title("🔒 Restricted Access")

    password = st.text_input(
        "Enter password to continue",
        type="password"
    )

    if password:
        if password == os.getenv("ST_PASSWORD"):
            st.session_state.authenticated = True
            st.success("Access granted")
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

# ==========================================================
# CONTEXT WINDOW LIMITS
# ==========================================================
MAX_TOKENS = 400_000
CHARS_PER_TOKEN = 4
PROMPT_TEMPLATE_BUFFER_CHARS = 60_000
MAX_CHARS = (MAX_TOKENS * CHARS_PER_TOKEN) - PROMPT_TEMPLATE_BUFFER_CHARS

# ---------- Helpers ----------
def generate_random_code(length=6):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def linkify_homeoint_lines(text: str) -> str:
    html_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        safe_line = (
            line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

        if stripped.startswith("QUERY:"):
            html_lines.append("<b>QUERY:</b>")
        elif stripped.startswith("RESPONSE:"):
            html_lines.append("<b>RESPONSE:</b>")
        elif stripped.startswith("Time Elapsed:"):
            html_lines.append(f"<b>{safe_line}</b>")
        elif "homeoint.org" in stripped and stripped.startswith("http"):
            html_lines.append(f'<a href="{stripped}" target="_blank">{stripped}</a>')
        else:
            html_lines.append(safe_line)

    return "<br>".join(html_lines)

# ---------- History ----------
HISTORY_DIR = "history data"
os.makedirs(HISTORY_DIR, exist_ok=True)

def auto_save_history(content: str):
    timestamp = datetime.now().strftime("%d-%m-%Y %H-%M-%S-%f")[:-3]
    filename = f"{timestamp} {generate_random_code()}.txt"
    with open(os.path.join(HISTORY_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)

# ---------- Session State ----------
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "elapsed_time" not in st.session_state:
    st.session_state.elapsed_time = 0

# ---------- UI ----------
st.set_page_config(
    page_title="Homeopathy Research Assistant",
    layout="wide"
)

st.title("Homeopathy Research Assistant (09-03-2026)")

query = st.text_area(
    "Clinical Case Description:",
    height=220,
    placeholder="Enter patient symptoms, modalities, mental state..."
)

current_len = len(query)
remaining = MAX_CHARS - current_len

st.caption(f"Characters left: {remaining:,}")

if remaining < 10_000:
    st.warning("⚠️ You are close to the context limit")

run_clicked = st.button("Analyze with Materia Medica")

# ---------- Run AI ----------
if run_clicked:
    if not query.strip():
        st.error("Please enter a case description.")
    else:
        st.session_state.last_query = query
        start_time = time.time()

        with st.spinner("🔍 Searching materia medica and reasoning..."):
            try:
                response = run_query(query)
                st.session_state.last_response = response
            except Exception as e:
                st.error(str(e))
                st.stop()

        elapsed = int(time.time() - start_time)
        st.session_state.elapsed_time = elapsed

        final_text = (
            "QUERY:\n"
            f"{query}\n\n"
            "RESPONSE:\n"
            f"{response}\n\n"
            "------------------------------\n"
            f"Time Elapsed: {elapsed // 3600} hours, "
            f"{(elapsed % 3600) // 60} minutes, "
            f"{elapsed % 60} seconds"
        )

        auto_save_history(final_text)

# ---------- Output ----------
if st.session_state.last_response:
    st.subheader("Results")

    html_output = linkify_homeoint_lines(
        "QUERY:\n"
        f"{st.session_state.last_query}\n\n"
        "RESPONSE:\n"
        f"{st.session_state.last_response}\n\n"
        f"Time Elapsed: {st.session_state.elapsed_time} seconds"
    )

    st.markdown(html_output, unsafe_allow_html=True)

    st.download_button(
        label="💾 Save Output as .txt",
        data=(
            "QUERY:\n"
            f"{st.session_state.last_query}\n\n"
            "RESPONSE:\n"
            f"{st.session_state.last_response}"
        ),
        file_name="homeopathy_analysis.txt",
        mime="text/plain"
    )

