import streamlit as st
import json
import os
import uuid
import requests
import numpy as np
from PIL import Image
import fitz  # PyMuPDF (already in your pip list)
from paddleocr import PaddleOCR

# ---------- OCR INITIALIZATION ----------
# We initialize this at the top so it loads once. 
# lang='en' is standard for resumes; use_angle_cls handles rotated documents.
@st.cache_resource
def load_ocr_model():
    return PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

ocr = load_ocr_model()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Resume AI Chat", page_icon="📄", layout="centered")

# ---------- CSS ----------
st.markdown("""
<style>
[data-testid="stChatMessageAvatar"] { display: none; }
[data-testid="stChatMessageContent"] { margin-left: 0; }
.stStatus { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "chat_data.json"

# ---------- HELPERS ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"conversations": {}, "current_chat": None}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def create_new_chat(data):
    chat_id = str(uuid.uuid4())[:8]
    data["conversations"][chat_id] = {
        "title": "New chat",
        "messages": []
    }
    data["current_chat"] = chat_id
    save_data(data)

def delete_chat(data, chat_id):
    del data["conversations"][chat_id]
    if not data["conversations"]:
        create_new_chat(data)
    else:
        data["current_chat"] = list(data["conversations"].keys())[0]
    save_data(data)

def extract_text_from_file(uploaded_file):
    """Processes PDF or Image and returns extracted text."""
    text_results = []
    
    try:
        if uploaded_file.type == "application/pdf":
            # Read PDF from memory
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                pix = page.get_pixmap()
                # Convert to PIL Image then to Numpy array for Paddle
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                result = ocr.ocr(np.array(img), cls=True)
                if result[0]:
                    for line in result[0]:
                        text_results.append(line[1][0])
        else:
            # Handle Images (JPG, PNG)
            img = Image.open(uploaded_file).convert("RGB")
            result = ocr.ocr(np.array(img), cls=True)
            if result[0]:
                for line in result[0]:
                    text_results.append(line[1][0])
    except Exception as e:
        return f"Error during OCR: {str(e)}"
            
    return " ".join(text_results)

def query_ollama(messages, model="gemma3:4b"):
    url = "http://localhost:11434/api/chat"
    payload = {"model": model, "messages": messages, "stream": True} # Set stream to True
    
    try:
        response = requests.post(url, json=payload, timeout=None, stream=True)
        response.raise_for_status()
        
        full_response = ""
        # Create a placeholder for the streaming text
        placeholder = st.empty()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk:
                    content = chunk["message"].get("content", "")
                    full_response += content
                    placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response) # Final clean render
        return full_response
        
    except Exception as e:
        return f"❌ Connection Error: {e}"# ---------- DATA LOADING ----------
data = load_data()
if data["current_chat"] is None:
    create_new_chat(data)
    data = load_data()

current_chat_id = data["current_chat"]
current_chat = data["conversations"][current_chat_id]

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("💬 Chats")
    if st.button("➕ New Chat", use_container_width=True):
        create_new_chat(data)
        st.rerun()

    st.divider()

    for chat_id, chat in data["conversations"].items():
        cols = st.columns([8, 1])
        if st.session_state.get("renaming") == chat_id:
            new_name = cols[0].text_input("", value=chat["title"], key=f"rename_{chat_id}", label_visibility="collapsed")
            if new_name.strip():
                chat["title"] = new_name.strip()
                save_data(data)
        else:
            if cols[0].button(chat["title"], key=f"open_{chat_id}", use_container_width=True):
                data["current_chat"] = chat_id
                save_data(data)
                st.rerun()

        if cols[1].button("⋮", key=f"menu_{chat_id}"):
            st.session_state["menu_open"] = None if st.session_state.get("menu_open") == chat_id else chat_id
            st.rerun()

        if st.session_state.get("menu_open") == chat_id:
            action_col = st.columns([1])[0]
            if action_col.button("Rename", key=f"rename_btn_{chat_id}"):
                st.session_state["renaming"] = chat_id
                st.session_state["menu_open"] = None
                st.rerun()
            if action_col.button("Delete", key=f"delete_btn_{chat_id}"):
                delete_chat(data, chat_id)
                st.session_state["menu_open"] = None
                st.rerun()

# ---------- MAIN UI ----------
st.title(current_chat["title"])

# Display history
for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# File Upload Section
st.markdown("### 📎 Upload Resume (PDF or Image)")
uploaded_files = st.file_uploader(
    "Upload files for analysis", 
    accept_multiple_files=True, 
    type=['pdf', 'png', 'jpg', 'jpeg'],
    label_visibility="collapsed"
)

# Chat Input
user_input = st.chat_input("Ask a question about the uploaded resume...")

if user_input:
    # 1. Show user message immediately
    current_chat["messages"].append({"role": "user", "content": user_input})
    
    # 2. Update title if needed
    if current_chat["title"] == "New chat":
        current_chat["title"] = user_input[:30]

    # 3. Process OCR if files are present
    full_context = ""
    if uploaded_files:
        for file in uploaded_files:
            with st.spinner(f"OCR: Reading {file.name}..."):
                text = extract_text_from_file(file)
                full_context += f"\nFILE: {file.name}\nCONTENT: {text}\n"

    # 4. Generate AI Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            # Prepare API Payload: We send the OCR text as context to the AI
            api_messages = []
            if full_context:
                system_prompt = f"The following is text extracted from a resume via OCR. Use it to answer questions:\n{full_context}"
                api_messages.append({"role": "system", "content": system_prompt})
            
            # Add the rest of the conversation history
            api_messages.extend(current_chat["messages"])
            
            bot_reply = query_ollama(api_messages)
            st.markdown(bot_reply)

    # 5. Save and refresh
    current_chat["messages"].append({"role": "assistant", "content": bot_reply})
    save_data(data)
    st.rerun()