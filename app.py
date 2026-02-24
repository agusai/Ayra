import streamlit as st
import time
from datetime import datetime
from dotenv import load_dotenv
import os

from utils.memory_manager import MemoryManager
from utils.mood_analyzer import MoodAnalyzer
from utils.model_router import ModelRouter
from utils.helpers import get_greeting, get_ui_theme, handle_easter_egg, get_level_from_messages
from utils.prompts import AYRA_SYSTEM_PROMPT

load_dotenv()

# -------------------------------------------------------------------
# Initialise components (singleton in session state)
# -------------------------------------------------------------------
if "memory" not in st.session_state:
    st.session_state.memory = MemoryManager()
if "mood" not in st.session_state:
    st.session_state.mood = MoodAnalyzer()
if "router" not in st.session_state:
    st.session_state.router = ModelRouter()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_activity" not in st.session_state:
    st.session_state.last_activity = []
if "fatigue" not in st.session_state:
    st.session_state.fatigue = False
if "fatigue_until" not in st.session_state:
    st.session_state.fatigue_until = 0
if "mood_score" not in st.session_state:
    st.session_state.mood_score = 0.0
if "comfort_mode" not in st.session_state:
    st.session_state.comfort_mode = False
if "current_story_id" not in st.session_state:
    st.session_state.current_story_id = None

# -------------------------------------------------------------------
# UI Setup
# -------------------------------------------------------------------
st.set_page_config(page_title="AYRA - Soulful Malaysian AI", page_icon="✨")

# Dynamic theme
theme_css = get_ui_theme(st.session_state.mood_score, st.session_state.fatigue)
st.markdown(f"""
<style>
    /* Background Dinamik Abang */
    .stApp {{ 
        background: {theme_css}; 
        transition: background 1.0s ease; 
    }}

    /* Sembunyikan Header & Footer (Bagi nampak macam Real App) */
    header, footer {{visibility: hidden !important;}}
    #MainMenu {{visibility: hidden;}}

    /* Cantikkan Kotak Chat */
    .stChatMessage {{ 
        background-color: rgba(255, 255, 255, 0.15); 
        backdrop-filter: blur(5px); /* Efek kaca */
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; 
        padding: 15px; 
        margin-bottom: 12px;
        box-shadow: 2px 4px 6px rgba(0,0,0,0.05);
    }}

    /* Kotak Input (Bawah) */
    .stChatInputContainer {{
        padding-bottom: 20px;
    }}
    
    /* Font Title bagi nampak premium */
    h1 {{
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
    }}
</style>
""", unsafe_allow_html=True)

st.title("✨ AYRA")
st.caption(get_greeting())

# Sidebar
with st.sidebar:
    st.header("AYRA")

    # Level and stats
    msg_count = st.session_state.memory.get_stat("total_messages")
    level, level_name = get_level_from_messages(msg_count)
    st.metric("Friendship Level", f"{level} · {level_name}")
    st.metric("Total Messages", msg_count)

    # Mood indicator
    mood_val = st.session_state.mood_score
    if mood_val > 0.2:
        mood_text = "😊 Ceria"
    elif mood_val < -0.2:
        mood_text = "😔 Comfort Mode"
    else:
        mood_text = "😐 Neutral"
    st.metric("Mood AYRA", mood_text)

    if st.button("🔄 New Chat"):
        st.session_state.chat_history = []
        st.rerun()

    st.divider()
    st.subheader("Easter Eggs")
    st.write("`/ais-krim` · `/penat` · `/cerita` · `/sambung` · `/mood` · `/level` · `/badges` · `/dream` · `/food` · `/trending`")
    st.divider()
    st.caption("Made with ❤️ in Malaysia")

    st.divider()
    with st.expander("📁 Upload File untuk Analisis"):
        file_type = st.radio("Jenis fail:", ["📸 Imej", "📄 PDF", "📊 Excel", "📝 Word", "📃 Teks"], horizontal=True)
        uploaded_file = st.file_uploader("Pilih fail", type=['png','jpg','jpeg','pdf','xlsx','xls','docx','doc','txt','md'])
    
        if uploaded_file is not None:
            # Tunjukkan preview
            if file_type.startswith("📸"):
                st.image(uploaded_file, caption="Preview", width=200)
            elif file_type.startswith("📄"):
                st.info(f"PDF: {uploaded_file.name}")
            elif file_type.startswith("📊"):
                st.info(f"Excel: {uploaded_file.name}")
            elif file_type.startswith("📝"):
                st.info(f"Word: {uploaded_file.name}")
            else:
                st.info(f"Teks: {uploaded_file.name}")
        
            analysis_option = st.selectbox("Apa nak AYRA buat?", [
            "Ringkaskan", "Cari poin penting", "Analisis bisnes", "Soalan custom..."
            ])
            custom_q = st.text_input("Soalan spesifik (optional)")
        
            if st.button("🔍 Analisis Sekarang"):
                st.session_state.uploaded_file = uploaded_file
                st.session_state.file_type = file_type
                st.session_state.analysis_option = analysis_option
                st.session_state.custom_q = custom_q
                st.session_state.analyze_file = True

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -------------------------------------------------------------------
# Handle user input
# -------------------------------------------------------------------
# Handle file analysis
if st.session_state.get('analyze_file', False):
    uploaded_file = st.session_state.uploaded_file
    file_type = st.session_state.file_type
    analysis_option = st.session_state.analysis_option
    custom_q = st.session_state.custom_q
    
    # Reset flag
    st.session_state.analyze_file = False
    
    # Tampilkan mesej user
    with st.chat_message("user"):
        st.write(f"[Uploaded file: {uploaded_file.name}]")
    
    # Proses ikut jenis fail
    file_content = ""
    if file_type.startswith("📸"):
        # Guna Gemini vision
        import PIL.Image
        image = PIL.Image.open(uploaded_file)
        # ... (panggil model vision)
    elif file_type.startswith("📄"):
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages[:5]:
            file_content += page.extract_text()
    elif file_type.startswith("📊"):
        import pandas as pd
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        file_content = f"Data shape: {df.shape}\nColumns: {list(df.columns)}\nPreview:\n{df.head().to_string()}"
    elif file_type.startswith("📝"):
        from docx import Document
        doc = Document(uploaded_file)
        for para in doc.paragraphs[:20]:
            file_content += para.text + "\n"
    else:
        file_content = uploaded_file.read().decode()
    
    # Potong panjang
    if len(file_content) > 3000:
        file_content = file_content[:3000] + "...[truncated]"
    
    # Hantar ke model (guna router atau terus Gemini)
    with st.spinner("AYRA sedang baca fail..."):
        prompt_text = f"Analisis fail ini: {analysis_option}\n\nKandungan:\n{file_content}\n\nSoalan tambahan: {custom_q if custom_q else 'Tiada'}"
        response, model_used = st.session_state.router.route(prompt_text, [])
        # Simpan dan papar
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
        st.session_state.memory.save_interaction(f"[Upload] {uploaded_file.name}", response, st.session_state.mood_score, model_used)
        st.rerun()


if prompt := st.chat_input("Type your message..."):
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # ---- 0. CRISIS DETECTION (SAFETY FIRST!) ----
    from utils.crisis_detector import detect_crisis, format_crisis_response, contains_crisis_keywords
    
    # Get user's name from memory if available
    user_name = st.session_state.memory.get_profile("name") or "awak"
    
    # Check for crisis
    is_crisis, keyword = detect_crisis(prompt)
    if is_crisis:
        # Log crisis event
        st.session_state.memory.log_crisis_event(prompt, keyword)
        
        # Format and send crisis response
        crisis_response = format_crisis_response(user_name)
        
        # Add to chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": crisis_response})
        
        # Save interaction
        st.session_state.memory.save_interaction(prompt, crisis_response, st.session_state.mood_score, "Crisis Alert")
        
        # Display and stop further processing
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            st.write(crisis_response)
        st.rerun()

    # ---- 1. Check for Easter eggs ----
    egg_response = handle_easter_egg(prompt, memory=st.session_state.memory)
    if egg_response:
        response = egg_response
        model_used = "Easter Egg"
    else:
        # ---- 2. Fatigue simulation ----
        now = time.time()
        st.session_state.last_activity.append(now)
        st.session_state.last_activity = st.session_state.last_activity[-10:]

        if st.session_state.fatigue:
            if now > st.session_state.fatigue_until:
                st.session_state.fatigue = False
            else:
                response = "AYRA: Kejap eh awak, Ayra nak 'recharge' jap. awak pun pergilah rehat, asyik tengok skrin jer!"
                model_used = "Fatigue"
                # Log but skip model
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.session_state.memory.save_interaction(prompt, response, st.session_state.mood_score, model_used)
                with st.chat_message("assistant"):
                    st.write(response)
                st.rerun()

        if not st.session_state.fatigue and len(st.session_state.last_activity) >= 5:
            time_window = st.session_state.last_activity[-1] - st.session_state.last_activity[-5]
            if time_window < 120:  # 5 messages in 2 minutes
                st.session_state.fatigue = True
                st.session_state.fatigue_until = now + 300
                response = "AYRA: Kejap eh awak, Ayra nak 'recharge' jap. awak pun pergilah rehat, asyik tengok skrin jer!"
                model_used = "Fatigue"
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.session_state.memory.save_interaction(prompt, response, st.session_state.mood_score, model_used)
                with st.chat_message("assistant"):
                    st.write(response)
                st.rerun()

        # ---- 3. Normal processing ----
        if not st.session_state.fatigue:
            # Get context from memory
            context = st.session_state.memory.get_recent_conversations(limit=5)
            # Build profile dict for router
            profile = {
                "name": st.session_state.memory.get_profile("name"),
                "birthday": st.session_state.memory.get_profile("birthday")
            }
            # Call router
            response, model_used = st.session_state.router.route(prompt, context, memory_profile=profile)

            # Update mood
            new_mood = st.session_state.mood.update(prompt)
            st.session_state.mood_score = new_mood

            # Comfort mode flag (for UI)
            if new_mood < -0.1:
                st.session_state.comfort_mode = True
            else:
                st.session_state.comfort_mode = False

            # Save interaction
            st.session_state.memory.save_interaction(prompt, response, new_mood, model_used)
            st.session_state.memory.save_to_vault(prompt, response, new_mood, model_used)
            
            # Selepas dapat response dan sebelum save ke SQLite
            # Simpan ke ChromaVault untuk long-term memory
            is_important = any(word in prompt.lower() for word in ['suka', 'minat', 'nama', 'birthday', 'janji', 'teh tarik'])
            st.session_state.memory.save_to_vault(
                prompt, 
                response, 
                st.session_state.mood_score, 
                model_used,
                is_important=is_important
            )

            # Increment message count
            st.session_state.memory.increment_stat("total_messages")

            # Handle story continuation if needed
            if prompt.lower().startswith("/sambung"):
                # Special case: continue story
                story = st.session_state.memory.get_latest_story()
                if story:
                    # Append new part to story (we'll just use the response as continuation)
                    st.session_state.memory.update_story(story["id"], "\n\n" + response)
                    st.session_state.current_story_id = story["id"]

            elif prompt.lower().startswith("/cerita"):
                # New story started – save it
                story_id = st.session_state.memory.save_story("User Story", response)
                st.session_state.current_story_id = story_id

    # Append and display Ayra's response
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
        if model_used != "Easter Egg" and model_used != "Fatigue":
            st.caption(f"*via {model_used}*")

    # Rerun to update UI (theme might change)
    st.rerun()