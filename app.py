import re
import streamlit as st

from utils.state import load_data, save_data, create_new_chat, delete_chat
from utils.ocr import extract_text
from utils.llm import get_available_models, query_ollama_stream
from utils.prompts import COVER_LETTER_PROMPT, ATS_MATCH_PROMPT, INTERVIEW_PREP_PROMPT

st.set_page_config(page_title="Resume AI Chat", layout="centered")

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

# Define base styling (fonts, avatars, animations, cool toggle)
base_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Fonts */
html, body, [class*="css"], .stApp, p, span, div, button, input, textarea, select {
    font-family: 'Outfit', 'Inter', sans-serif !important;
}

[data-testid="stChatMessageAvatar"] { display: none; }
[data-testid="stChatMessageContent"] { margin-left: 0; }
.stStatus { margin-bottom: 10px; }

/* Cool Toggle Switch Styling */
.st-key-theme_toggle_widget {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}
.st-key-theme_toggle_widget [data-baseweb="checkbox"] {
    background-color: transparent !important;
}
.st-key-theme_toggle_widget [data-baseweb="checkbox"] > div:first-of-type {
    border-radius: 30px !important;
    border: 1px solid var(--toggle-border) !important;
    background: var(--toggle-bg) !important;
    width: 48px !important;
    height: 26px !important;
    padding: 3px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15) !important;
}
.st-key-theme_toggle_widget [data-baseweb="checkbox"] > div:first-of-type > div {
    border-radius: 50% !important;
    background: var(--toggle-knob) !important;
    width: 18px !important;
    height: 18px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}
.st-key-theme_toggle_widget [data-baseweb="checkbox"]:has(input:checked) > div:first-of-type {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 8px rgba(139, 92, 246, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}
.st-key-theme_toggle_widget [data-baseweb="checkbox"]:has(input:checked) > div:first-of-type > div {
    background: #ffffff !important;
    transform: translateX(22px) !important;
}

/* Fix chat input container to the bottom of the viewport */
.stChatInputContainer {
    position: fixed !important;
    bottom: 20px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: calc(100% - 40px) !important;
    max-width: 730px !important;
    z-index: 9999 !important;
    padding: 0 !important;
}

/* Custom empty state card */
.clean-empty-state {
    padding: 2.5rem 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}
.clean-empty-state h3 {
    margin-top: 0 !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.6rem !important;
}
.clean-empty-state p {
    font-size: 0.95rem !important;
    margin-bottom: 0 !important;
    line-height: 1.6 !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}

</style>
"""
st.markdown(base_css, unsafe_allow_html=True)

if st.session_state["theme"] == "dark":
    dark_css = """
    <style>
    :root {
        --toggle-border: rgba(255, 255, 255, 0.15);
        --toggle-bg: #1e293b;
        --toggle-knob: #f8fafc;
    }
    
    /* Dark Mode Core */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
        padding-bottom: 110px !important;
    }
    [data-testid="stHeader"] {
        background-color: rgba(11, 15, 25, 0.8) !important;
        backdrop-filter: blur(12px) !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #94a3b8 !important;
    }
    
    /* Inputs & Textareas */
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    [data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
    
    /* Buttons */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #3b82f6 !important;
        border-color: #3b82f6 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Chat bubbles */
    [data-testid="stChatMessage"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
        color: #f8fafc !important;
    }
    
    /* Bottom Chat Input box */
    .stChatInputContainer {
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #f8fafc !important;
    }
    
    /* Tabs selector */
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        border-bottom: 2px solid transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    /* Empty State Card */
    .clean-empty-state {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
        backdrop-filter: blur(8px) !important;
    }
    .clean-empty-state h3 {
        color: #3b82f6 !important;
    }
    .clean-empty-state p {
        color: #94a3b8 !important;
    }
    
    /* File Uploader styling */
    [data-testid="stFileUploader"] {
        background-color: rgba(30, 41, 59, 0.3) !important;
        border: 1px dashed #334155 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    </style>
    """
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    light_css = """
    <style>
    :root {
        --toggle-border: #cbd5e1;
        --toggle-bg: #e2e8f0;
        --toggle-knob: #ffffff;
    }
    
    /* Light Mode Core (Harsh Black removed, replaced with slate-600/700) */
    .stApp {
        background-color: #f8fafc !important;
        color: #334155 !important;
        padding-bottom: 110px !important;
    }
    [data-testid="stHeader"] {
        background-color: rgba(248, 250, 252, 0.8) !important;
        backdrop-filter: blur(12px) !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #475569 !important;
    }
    
    /* Inputs & Textareas */
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }
    [data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 1px #2563eb !important;
    }
    
    /* Buttons */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }
    
    /* Chat bubbles */
    [data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
        color: #334155 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02) !important;
    }
    
    /* Bottom Chat Input box */
    .stChatInputContainer {
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #334155 !important;
    }
    
    /* Tabs selector */
    button[data-baseweb="tab"] {
        color: #64748b !important;
        border-bottom: 2px solid transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 2px solid #2563eb !important;
    }
    
    /* Empty State Card */
    .clean-empty-state {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05) !important;
    }
    .clean-empty-state h3 {
        color: #2563eb !important;
    }
    .clean-empty-state p {
        color: #64748b !important;
    }
    
    /* File Uploader styling */
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1px dashed #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    </style>
    """
    st.markdown(light_css, unsafe_allow_html=True)

data = load_data()
if data["current_chat"] is None or data["current_chat"] not in data["conversations"]:
    create_new_chat(data)
    data = load_data()

current_chat_id = data["current_chat"]
current_chat = data["conversations"][current_chat_id]


def extract_score(text):
    match = re.search(r"(?:Match Score|Score)[:\s]*(\d+)", text, re.IGNORECASE)
    if match:
        return min(int(match.group(1)), 100)
    match2 = re.search(r"(\d+)\s*/\s*100", text)
    if match2:
        return min(int(match2.group(1)), 100)
    return None


def build_context(chat, uploaded_files):
    parts = []
    chat.setdefault("extracted_files", {})

    for file in uploaded_files or []:
        file_key = f"doc_{file.name}_{file.size}"
        if file_key not in chat["extracted_files"]:
            with st.spinner(f"Reading {file.name}..."):
                chat["extracted_files"][file_key] = extract_text(file)
                save_data(data)
        parts.append(f"FILE: {file.name}\nCONTENT: {chat['extracted_files'][file_key]}")

    for file_key, text in chat["extracted_files"].items():
        if not any(f"doc_{f.name}_{f.size}" == file_key for f in (uploaded_files or [])):
            name = file_key.replace("doc_", "", 1)
            parts.append(f"FILE: {name}\nCONTENT: {text}")

    if chat.get("text_input", "").strip():
        parts.append(f"USER TEXT:\n{chat['text_input'].strip()}")

    return "\n\n".join(parts)


with st.sidebar:
    st.title("Chats")
    if st.button("New Chat", use_container_width=True):
        create_new_chat(data)
        st.session_state.pop("menu_open", None)
        st.session_state.pop("renaming", None)
        st.rerun()

    st.divider()

    available_models = get_available_models()
    if len(available_models) > 1:
        selected_model = st.selectbox("Model", available_models, index=0)
        st.divider()
    else:
        selected_model = available_models[0]

    # Theme Toggle
    current_theme = st.session_state.get("theme", "dark")
    theme_toggle = st.toggle("🌙 Dark Mode", value=(current_theme == "dark"), key="theme_toggle_widget")
    new_theme = "dark" if theme_toggle else "light"
    if new_theme != current_theme:
        st.session_state["theme"] = new_theme
        st.rerun()
    st.divider()

    for chat_id, chat in list(data["conversations"].items()):
        cols = st.columns([8, 1])
        if st.session_state.get("renaming") == chat_id:
            new_name = cols[0].text_input("", value=chat["title"], key=f"rename_{chat_id}", label_visibility="collapsed")
            if new_name.strip() and new_name.strip() != chat["title"]:
                chat["title"] = new_name.strip()
                save_data(data)
        else:
            if cols[0].button(chat["title"], key=f"open_{chat_id}", use_container_width=True):
                data["current_chat"] = chat_id
                save_data(data)
                st.session_state.pop("menu_open", None)
                st.rerun()

        if cols[1].button("\u22ee", key=f"menu_{chat_id}", help="Options"):
            st.session_state["menu_open"] = None if st.session_state.get("menu_open") == chat_id else chat_id
            st.rerun()

        if st.session_state.get("menu_open") == chat_id:
            if st.button("Rename", key=f"rename_btn_{chat_id}", use_container_width=True):
                st.session_state["renaming"] = chat_id
                st.session_state["menu_open"] = None
                st.rerun()
            if st.button("Delete", key=f"delete_btn_{chat_id}", use_container_width=True):
                delete_chat(data, chat_id)
                st.session_state.pop("menu_open", None)
                st.session_state.pop("renaming", None)
                st.rerun()

st.title(current_chat["title"])

st.subheader("Documents")
uploaded_files = st.file_uploader(
    "Upload files (resume, job posting, etc. as PDF, image, or text)",
    accept_multiple_files=True,
    type=["pdf", "png", "jpg", "jpeg", "txt"],
    key=f"docs_{current_chat_id}",
)

if "job_description" in current_chat:
    current_chat.setdefault("text_input", current_chat.pop("job_description"))

current_chat.setdefault("text_input", "")
text_key = f"text_input_{current_chat_id}"
if text_key not in st.session_state:
    st.session_state[text_key] = current_chat["text_input"]

st.caption("Upload files above, or type and edit text below.")
text_input = st.text_area(
    "Text input",
    height=160,
    placeholder="Type or paste text here if you prefer not to upload a file.",
    key=text_key,
    label_visibility="visible",
)
if st.session_state[text_key] != current_chat["text_input"]:
    current_chat["text_input"] = st.session_state[text_key]
    save_data(data)

full_context = build_context(current_chat, uploaded_files)

tab1, tab2, tab3 = st.tabs(["Cover Letter", "ATS Match & Resume Feedback", "Interview Prep (Viva)"])

with tab1:
    cover_letter_text = current_chat.get("cover_letter", "")
    if cover_letter_text:
        edited_letter = st.text_area("Edit Cover Letter", value=cover_letter_text, height=350, key=f"edit_cl_{current_chat_id}")
        if edited_letter != cover_letter_text:
            current_chat["cover_letter"] = edited_letter
            save_data(data)

        col1, col2 = st.columns(2)
        col1.download_button("Download as Text", data=edited_letter, file_name="cover_letter.txt", mime="text/plain", use_container_width=True)
        col2.info("You can copy the code block below:")
        st.code(edited_letter, language="markdown")

        if st.button("Regenerate Cover Letter", key=f"regen_cl_{current_chat_id}"):
            current_chat["cover_letter"] = ""
            save_data(data)
            st.rerun()
    else:
        if st.button("Generate Cover Letter", use_container_width=True):
            api_messages = [{"role": "system", "content": f"{COVER_LETTER_PROMPT}\n\nDOCUMENTS:\n{full_context}"}]
            with st.spinner("Generating..."):
                reply = st.write_stream(query_ollama_stream(api_messages, model=selected_model))
            current_chat["cover_letter"] = reply
            save_data(data)
            st.rerun()

with tab2:
    ats_text = current_chat.get("ats_result", "")
    if ats_text:
        score = extract_score(ats_text)
        if score is not None:
            st.subheader("ATS Match Metrics")
            col1, col2 = st.columns([1, 3])
            col1.metric("Match Score", f"{score}%")
            col2.progress(score / 100.0)

        st.markdown(ats_text)

        if st.button("Re-run ATS Analysis", key=f"regen_ats_{current_chat_id}"):
            current_chat["ats_result"] = ""
            save_data(data)
            st.rerun()
    else:
        if st.button("Run ATS Analysis & Get Feedback", use_container_width=True):
            api_messages = [{"role": "system", "content": f"{ATS_MATCH_PROMPT}\n\nDOCUMENTS:\n{full_context}"}]
            with st.spinner("Analyzing..."):
                reply = st.write_stream(query_ollama_stream(api_messages, model=selected_model))
            current_chat["ats_result"] = reply
            save_data(data)
            st.rerun()

with tab3:
    interview_messages = current_chat.setdefault("interview_messages", [])

    if interview_messages:
        if st.button("Reset Interview Session", key=f"reset_interview_{current_chat_id}"):
            current_chat["interview_messages"] = []
            save_data(data)
            st.rerun()

    for msg in interview_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_answer = st.chat_input("Type your response here...", key=f"interview_input_{current_chat_id}")

    if not interview_messages:
        if st.button("Start Mock Interview", use_container_width=True):
            api_messages = [
                {"role": "system", "content": f"{INTERVIEW_PREP_PROMPT}\n\nDOCUMENTS:\n{full_context}"},
                {"role": "user", "content": "Start interview"},
            ]
            interview_messages.append({"role": "user", "content": "Start interview"})
            save_data(data)

            with st.chat_message("assistant"):
                with st.spinner("Preparing question..."):
                    reply = st.write_stream(query_ollama_stream(api_messages, model=selected_model))
            interview_messages.append({"role": "assistant", "content": reply})
            save_data(data)
            st.rerun()

    elif user_answer:
        interview_messages.append({"role": "user", "content": user_answer})
        save_data(data)

        with st.chat_message("user"):
            st.markdown(user_answer)

        api_messages = [{"role": "system", "content": f"{INTERVIEW_PREP_PROMPT}\n\nDOCUMENTS:\n{full_context}"}]
        api_messages.extend(interview_messages)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing answer and preparing next question..."):
                reply = st.write_stream(query_ollama_stream(api_messages, model=selected_model))
        interview_messages.append({"role": "assistant", "content": reply})
        save_data(data)
        st.rerun()
