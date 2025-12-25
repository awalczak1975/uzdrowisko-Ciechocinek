import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz
import base64

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
# Odświeżanie co 10 sekund dla sprawnego czatu
st_autorefresh(interval=10000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* POWIADOMIENIA */
    .new-msg-alert { 
        color: #ef4444 !important; 
        font-weight: 900 !important; 
        text-align: center;
        animation: blinker 1.5s linear infinite; 
    }
    @keyframes blinker { 50% { opacity: 0; } }

    /* LOGO */
    .logo-container { text-align: center; margin-top: -30px !important; margin-bottom: 20px !important; }
    .logo-container img { width: 200px; cursor: pointer; transition: 0.3s; }
    .logo-container img:hover { transform: scale(1.03); }

    /* METRYKI WYŚRODKOWANE */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 10px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

    /* ZAKŁADKI GÓRNE */
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; margin-right: 5px !important; padding: 10px 20px !important; border: 1px solid #cbd5e1 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }

    /* CZAT BALONIKI */
    .chat-bubble { padding: 12px; border-radius: 15px; margin-bottom: 8px; font-family: sans-serif; line-height: 1.4; }
    .chat-mine { background-color: #eab308; color: #1e293b; margin-left: auto; text-align: right; border-bottom-right-radius: 2px; }
    .chat-theirs { background-color: #334155; color: white; margin-right: auto; border-left: 5px solid #ef4444; border-bottom-left-radius: 2px; }

    /* KOMPAKTOWA BELKA DOLNA */
    .main-sheet-footer {
        margin-top: 15px;
        padding: 5px 15px;
        background-color: #1e293b;
        border-top: 3px solid #eab308;
        border-radius: 5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    }
    .footer-brand { font-size: 0.8rem; font-weight: 800; color: #eab308; }
    .sidebar-footer { text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #334155; color: #94a3b8; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE TECHNICZNE
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if len(dane) < 1: return pd.DataFrame()
        return pd.DataFrame(dane[1:], columns=dane[0])
    except: return pd.DataFrame()

def wyslij_wiadomosc(nadawca, odbiorca, tresc):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("CZAT")
        czas = datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([czas, nadawca, odbiorca, tresc, "NIEPRZECZYTANE"])
        return True
    except: return False

def play_notification_sound():
    # Krótki dźwięk powiadomienia w formacie base64
    audio_html = """
        <audio autoplay="true" style="display:none;">
            <source src="https://www.soundjay.com/buttons/beep-07a.mp3" type="audio/mpeg">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# ==========================================================
# 3. LOGIKA SIDEBARU
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

# Sprawdzanie wiadomości
df_chat = pobierz_df("CZAT")
has_new = False
if not df_chat.empty and 'ODBIORCA' in df_chat.columns and 'STATUS' in df_chat.columns:
    has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty

with st.sidebar:
    st.markdown(f'<div class="logo-container"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    st.divider()
    
    if has_new:
        st.markdown('<p class="new-msg-alert">🔔 MASZ NOWĄ WIADOMOŚĆ!</p>', unsafe_allow_html=True)
        play_notification_sound() # Odtwórz dźwięk przy wykryciu nowej wiadomości
        
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))
    st.markdown(f'<div class="sidebar-footer">System Zarządzania &copy; {now_pl.year}<br><b>Andrzej Walczak</b></div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
chat_title = "💬 CZAT (NOWY!)" if has_new else "💬 CZAT"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_title])

for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📋 Razem", len(df))
            m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
            st.data_editor(df, use_container_width=True, hide_index=True, height=500)

with tabs[3]:
    st.subheader("Komunikator Służbowy")
    pracownicy = ["Marta", "Sławek", "Andrzej", "Agata", "Rafał"]
    odbiorca = st.selectbox("Wybierz adresata:", [p for p in pracownicy if p != zalogowany])
    
    chat_box = st.container(height=400, border=True)
    if not df_chat.empty and 'TREŚĆ' in df_chat.columns:
        history = df_chat[((df_chat['NADAWCA'] == zalogowany) & (df_chat['ODBIORCA'] == odbiorca)) | 
                         ((df_chat['NADAWCA'] == odbiorca) & (df_chat['ODBIORCA'] == zalogowany))]
        for _, msg in history.tail(15).iterrows():
            cls = "chat-mine" if msg['NADAWCA'] == zalogowany else "chat-theirs"
            chat_box.markdown(f'<div class="chat-bubble {cls}"><b>{msg["NADAWCA"]}</b>: {msg["TREŚĆ"]}</div>', unsafe_allow_html=True)

    t_input = st.chat_input("Napisz wiadomość...")
    if t_input:
        if wyslij_wiadomosc(zalogowany, odbiorca, t_input):
            st.rerun()

# --- ULTRA KOMPAKTOWA BELKA DOLNA ---
st.markdown(f"""
    <div class="main-sheet-footer">
        <div class="footer-brand">UZDROWISKO CIECHOCINEK S.A.</div>
        <div style="font-size:0.75rem; color:#94a3b8;">{now_pl.strftime('%d.%m.%Y | %H:%M:%S')} | Komunikator aktywny</div>
    </div>
""", unsafe_allow_html=True)
