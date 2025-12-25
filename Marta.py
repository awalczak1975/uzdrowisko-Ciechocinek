import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. STYLIZACJA (PRZYWRÓCENIE PEŁNEJ GRAFIKI)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .logo-container { text-align: center; margin-top: -65px !important; margin-bottom: 20px !important; }
    .logo-container img { width: 190px; }
    
    .user-info-footer {
        background-color: #eab308 !important;
        color: #1e293b !important;
        padding: 10px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 15px;
        border: 2px solid white;
    }

    /* WYŚRODKOWANIE METRYK */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; text-align: center !important; }

    /* ZAKŁADKI */
    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 25px !important; border: none !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }
    
    /* KOMUNIKATOR DYMKI */
    .chat-bubble { padding: 10px 15px; border-radius: 15px; margin-bottom: 5px; max-width: 80%; font-size: 14px; }
    .bubble-me { background: #eab308; align-self: flex-end; color: #1e293b; font-weight: 600; }
    .bubble-other { background: white; align-self: flex-start; border: 1px solid #cbd5e1; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGOWANIE I DANE
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")
if u_p in USERS and USERS[u_p] == k_p: zalogowany = u_p
else: st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=15)
def pobierz_arkusz(nazwa):
    try:
        sh = polacz().open("Marta-Dział Techniczny")
        ws = sh.worksheet(nazwa)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df.iloc[:, 1].str.strip() != ""].copy()
    except: return pd.DataFrame()

# Inicjalizacja czatu w pamięci (ulotny)
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ==========================================================
# 3. SIDEBAR
# ==========================================================
df_biez = pobierz_arkusz("Zadania bieżące")
df_zreal = pobierz_arkusz("Zadania zrealizowane")

with st.sidebar:
    st.markdown(f'<div class="logo-container"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.button("➕ DODAJ", use_container_width=True)
    if c2.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div class="sidebar-header" style="color:#eab308; font-weight:800; margin-top:20px;">📅 KALENDARZ</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {zalogowany.upper()} WALCZAK</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "CZAT 🔴"])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, nazwa in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_arkusz(nazwa)
        m1, m2, m3 = st.columns(3)
        if not df.empty:
            m1.metric("📋 Razem", len(df))
            m3.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
            st.data_editor(df, use_container_width=True, hide_index=True, height=500)

with tabs[3]:
    st.subheader("💬 Komunikator Szybki (Wiadomości sesyjne)")
    st.caption("W tej wersji wiadomości są widoczne do czasu odświeżenia strony.")
    
    # Wyświetlanie dymków
    for msg in st.session_state.chat_history:
        cls = "bubble-me" if msg['user'] == zalogowany else "bubble-other"
        st.markdown(f'<div class="chat-bubble {cls}"><b>{msg["user"]}</b>: {msg["text"]}</div>', unsafe_allow_html=True)
    
    with st.form("chat_form", clear_on_submit=True):
        txt = st.text_input("Napisz coś...")
        if st.form_submit_button("Wyślij") and txt:
            st.session_state.chat_history.append({"user": zalogowany, "text": txt})
            st.rerun()

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now_pl.strftime("%d.%m.%Y")}</span></div>', unsafe_allow_html=True)
