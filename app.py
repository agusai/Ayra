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

st.markdown(f"""
<style>
    /* ===== MIDNIGHT GOLD & COSMIC SOUL ===== */
    
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* ===== BACKGROUND COSMIC ===== */
    .stApp {{
        background-color: #0F1A24 !important;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(255, 215, 0, 0.08) 0%, transparent 30%),
            radial-gradient(circle at 80% 70%, rgba(255, 215, 0, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 40% 80%, rgba(255, 215, 0, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 90% 20%, rgba(255, 215, 0, 0.05) 0%, transparent 35%) !important;
    }}

    /* ===== GLOBAL TEXT ===== */
    * {{
        font-family: 'Inter', sans-serif !important;
        color: #FFFFFF !important;
    }}

    /* ===== BANNER AYRA ===== */
    .banner-ayra {{
        text-align: center;
        margin: 20px auto 5px auto;
    }}

    .banner-ayra h1 {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        background: linear-gradient(135deg, #FFD700, #FFFFFF) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.3) !important;
        letter-spacing: 1px !important;
        margin-bottom: 5px !important;
    }}

    /* ===== GREETING MESSAGE ===== */
    .greeting-box {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 15px !important;
        padding: 12px 20px !important;
        margin: 10px auto 25px auto !important;
        max-width: 800px !important;
        text-align: center !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important;
    }}

    /* ===== SIDEBAR COSMIC ===== */
    [data-testid="stSidebar"] {{
        background-color: rgba(10, 15, 20, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 215, 0, 0.2) !important;
    }}

    [data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}

    /* Stats cards */
    .stMetric {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 215, 0, 0.2) !important;
        border-radius: 15px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
        backdrop-filter: blur(5px);
    }}

    .stMetric label {{
        color: #FFD700 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-weight: 600 !important;
    }}

    .stMetric [data-testid="stMetricValue"] {{
        color: #FFFFFF !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
    }}

    /* ===== CHAT MESSAGES - GLASSMORPHISM ===== */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 20px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
    }}

    .stChatMessage * {{
        color: #FFFFFF !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
    }}

    /* User vs assistant indicator */
    .stChatMessage[data-testid="user"] {{
        border-left: 4px solid #FFD700 !important;
    }}

    .stChatMessage[data-testid="assistant"] {{
        border-right: 4px solid #FFD700 !important;
    }}

    /* ===== INPUT BOX ===== */
    .stChatInputContainer {{
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: rgba(15, 26, 36, 0.95) !important;
        backdrop-filter: blur(10px);
        padding: 12px 15px !important;
        border-top: 1px solid rgba(255, 215, 0, 0.2) !important;
        z-index: 999 !important;
    }}

    .stChatInputContainer input {{
        background: rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        border-radius: 30px !important;
        padding: 12px 20px !important;
        font-size: 1rem !important;
        backdrop-filter: blur(5px);
    }}

    .stChatInputContainer input:focus {{
        border-color: #FFD700 !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.3) !important;
    }}

    /* ===== BUTTONS ===== */
    .stButton button {{
        background: linear-gradient(135deg, #FFD700, #FFA500) !important;
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
        transition: all 0.3s ease !important;
    }}

    .stButton button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.5) !important;
    }}

    /* ===== BOTTOM BAR (optional) ===== */
    .bottom-bar {{
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(15, 26, 36, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 40px;
        padding: 8px 20px;
        display: flex;
        gap: 20px;
        font-size: 1.8rem;
        z-index: 998;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}

    .bottom-bar span {{
        cursor: pointer;
        transition: transform 0.2s;
    }}

    .bottom-bar span:hover {{
        transform: scale(1.2);
    }}

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {{
        width: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05);
    }}

    ::-webkit-scrollbar-thumb {{
        background: rgba(255, 215, 0, 0.3);
        border-radius: 3px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(255, 215, 0, 0.5);
    }}
</style>
""", unsafe_allow_html=True)


# BANNER AYRA - SIMPLE TENGAH
st.markdown("""
<div class="banner-ayra">
    <h1>AYRA</h1>
</div>
""", unsafe_allow_html=True)

# GREETING
greeting_msg = get_greeting()
st.markdown(f"""
<div class="greeting-box">
    {greeting_msg}
</div>
""", unsafe_allow_html=True)

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
    st.subheader("👨‍💻 Uncle Jiji's Something...")
    st.write("Cuba taip ni kalau nak 'surprise':")
    st.code("/ais-krim 🍦 /penat 😮‍💨 /cerita 📖 /sambung 🔄 /mood 😊 /level 📊 /badges 🏅 /dream 🌙 /food 🍜 /trending 📈")
    st.caption("Jangan tanya apa, just try! 😉")

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

    st.divider()
    st.markdown("📝 **Bagi feedback?**")
    st.markdown("[Klik sini](https://forms.gle/jfzyLqPx94oWs1du6) — tolong kami improve AYRA! 🙏")

    st.divider()
    with st.expander("🔬 Public Testing Notice"):
        st.markdown("""
        - AYRA masih dalam **fasa ujian awam**
        - Respons mungkin tidak 100% tepat
        - Jangan kongsi maklumat peribadi sensitif
        - Jika dalam krisis, hubungi:
            - Befrienders KL: **03-7627 2929** (24 jam)
            - Talian Kasih: **15999** (24 jam)
        - Maklum balas amat dialu-alukan! 🌸
        """)

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