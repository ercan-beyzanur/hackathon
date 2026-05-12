import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import base64
import json
import logging
import os
import re
import tempfile
from datetime import datetime

import google.generativeai as genai
import requests
import streamlit as st
from gtts import gTTS
from streamlit.components.v1 import html
from streamlit_mic_recorder import speech_to_text

from dotenv import load_dotenv
from config import API_URL, GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ProKOBİ Sesli Asistan", layout="wide", page_icon="🎙️")

load_dotenv()
genai.configure(api_key=GEMINI_API_KEY)

# --- LOG AYARI ---
os.makedirs("logs", exist_ok=True)
LOG_FILE = os.path.join("logs", "prokobi.log")

logger = logging.getLogger("prokobi")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logger.propagate = False

# --- SESSION STATE ---
if "last_processed_transcript" not in st.session_state:
    st.session_state.last_processed_transcript = ""
if "tasks" not in st.session_state:
    st.session_state.tasks = []


# --- YARDIMCI FONKSİYONLAR ---
def fetch_tasks():
    try:
        res = requests.get(f"{API_URL}/tasks", timeout=10)
        res.raise_for_status()
        tasks = res.json()
        logger.info("Tasks fetched successfully. Count=%s", len(tasks) if tasks else 0)
        return tasks
    except Exception as e:
        logger.exception("Görevler alınamadı: %s", e)
        return []


def speak(text: str):
    """Metni sese çevirir ve tarayıcıda oynatır."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name

        tts = gTTS(text=text, lang="tr")
        tts.save(tmp_path)

        with open(tmp_path, "rb") as f:
            data = f.read()

        b64 = base64.b64encode(data).decode("utf-8")
        audio_html = f"""
        <audio autoplay="true" controls="controls" style="width: 100%;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3" />
        </audio>
        """
        html(audio_html, height=70)

        logger.info("Speech synthesized: %s", text)

    except Exception as e:
        logger.exception("Seslendirme hatası: %s", e)


def ask_gemini(prompt: str, current_tasks):
    model = genai.GenerativeModel("gemini-2.5-flash")
    su_an = datetime.now().strftime("%Y-%m-%d %H:%M")

    full_prompt = f"""
Sen bir KOBİ iş takip asistanısın.
Şu an: {su_an}
Mevcut işler: {current_tasks}

Kullanıcı komutunu SADECE şu JSON formatında yanıtla:
{{
  "action": "EKLE" veya "GUNCELLE",
  "title": "iş başlığı",
  "task_time": "YYYY-MM-DD HH:MM" veya "NULL",
  "status": "To Do" veya "In Progress" veya "Done"
}}

Kurallar:
- Sadece JSON dön.
- action EKLE ise title ve task_time alanlarını doldur.
- action GUNCELLE ise title ve status alanlarını doldur.
- Başka metin yazma.

Kullanıcı komutu: {prompt}
"""
    response = model.generate_content(full_prompt)
    ai_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    logger.info("Gemini raw response: %s", ai_text)
    return ai_text


def parse_ai_response(ai_text: str):
    """Gemini çıktısını JSON olarak ayrıştırmayı dener; olmazsa fallback yapar."""
    try:
        data = json.loads(ai_text)
        if isinstance(data, dict) and "action" in data:
            return data
    except Exception:
        pass

    cleaned = ai_text.replace("```", "").strip()

    if "EKLE" in cleaned:
        m = re.search(r'"?title"?\s*:\s*"(.*?)".*?"?task_time"?\s*:\s*"(.*?)"', cleaned, re.DOTALL | re.IGNORECASE)
        if m:
            return {"action": "EKLE", "title": m.group(1).strip(), "task_time": m.group(2).strip()}

    if "GUNCELLE" in cleaned:
        m = re.search(r'"?title"?\s*:\s*"(.*?)".*?"?status"?\s*:\s*"(.*?)"', cleaned, re.DOTALL | re.IGNORECASE)
        if m:
            return {"action": "GUNCELLE", "title": m.group(1).strip(), "status": m.group(2).strip()}

    return None


def refresh_tasks():
    st.session_state.tasks = fetch_tasks()


def process_command(command_text: str):
    try:
        logger.info("Incoming command: %s", command_text)

        current_titles = [t.get("title", "") for t in st.session_state.tasks]
        ai_resp = ask_gemini(command_text, current_titles)
        parsed = parse_ai_response(ai_resp)

        if not parsed:
            logger.warning("AI response could not be parsed. Text=%s", ai_resp)
            return

        action = (parsed.get("action") or "").upper().strip()

        if action == "EKLE":
            title = (parsed.get("title") or "").strip()
            time_str = (parsed.get("task_time") or "NULL").strip()

            if not title:
                logger.warning("EKLE action but title is empty. Parsed=%s", parsed)
                return

            res = requests.post(
                f"{API_URL}/tasks",
                json={"title": title, "task_time": time_str},
                timeout=10,
            )

            if res.status_code == 200:
                logger.info("Task added: title=%s, task_time=%s", title, time_str)
                speak(f"{title} görevini ekledim.")
                refresh_tasks()
                st.rerun()
            else:
                logger.error("Backend add error: %s - %s", res.status_code, res.text)

        elif action == "GUNCELLE":
            title = (parsed.get("title") or "").strip()
            status = (parsed.get("status") or "").strip()

            if not title or not status:
                logger.warning("GUNCELLE action but title/status empty. Parsed=%s", parsed)
                return

            res = requests.patch(
                f"{API_URL}/tasks/update",
                params={"title": title, "new_status": status},
                timeout=10,
            )

            if res.status_code == 200:
                logger.info("Task updated: title=%s, status=%s", title, status)
                speak(f"{title} görevini {status} yaptım.")
                refresh_tasks()
                st.rerun()
            else:
                logger.error("Backend update error: %s - %s", res.status_code, res.text)

        else:
            logger.warning("Unknown action: %s | Parsed=%s", action, parsed)

    except Exception as e:
        logger.exception("process_command failed: %s", e)


# --- ARAYÜZ ---
st.title("🎙️ ProKOBİ Sesli İş Takip")

if "tasks" not in st.session_state or not st.session_state.tasks:
    refresh_tasks()

st.subheader("Komut Ver")

voice_input = speech_to_text(
    language="tr",
    start_prompt="🎤 Konuşmaya Başla",
    stop_prompt="🛑 Durdur ve Gönder",
    just_once=True,
    use_container_width=True,
    key="stt"
)

text_input = st.chat_input("Veya buraya yazın...")

final_input = ""
if voice_input:
    final_input = voice_input.strip()
elif text_input:
    final_input = text_input.strip()

if final_input and final_input != st.session_state.last_processed_transcript:
    st.session_state.last_processed_transcript = final_input
    process_command(final_input)

# --- KANBAN GÖRÜNÜMÜ ---
st.divider()
cols = st.columns(3)
states = ["To Do", "In Progress", "Done"]

for i, status in enumerate(states):
    with cols[i]:
        st.subheader(status)
        filtered = [t for t in st.session_state.tasks if t.get("status") == status]
        for t in filtered:
            with st.container(border=True):
                st.write(f"**{t.get('title', 'Başlıksız')}**")
                task_time = t.get("task_time", "NULL")
                st.caption(f"📅 {task_time if task_time != 'NULL' else 'Belirtilmedi'}")