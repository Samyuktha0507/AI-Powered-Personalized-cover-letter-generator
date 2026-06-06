import json
import os
import uuid

DATA_FILE = "chat_data.json"


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"conversations": {}, "current_chat": None}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_new_chat(data):
    chat_id = str(uuid.uuid4())[:8]
    data["conversations"][chat_id] = {
        "title": "New chat",
        "text_input": "",
        "cover_letter": "",
        "ats_result": "",
        "interview_messages": [],
        "extracted_files": {},
    }
    data["current_chat"] = chat_id
    save_data(data)
    return chat_id


def delete_chat(data, chat_id):
    if chat_id in data["conversations"]:
        del data["conversations"][chat_id]
    if not data["conversations"]:
        create_new_chat(data)
    else:
        data["current_chat"] = list(data["conversations"].keys())[0]
    save_data(data)
