import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (POWIADOMIENIA CZATU)
# ==========================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=10000, key="chat_refresh") # Częstsze odświeżanie dla czatu

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* POWIADOMIENIE CZATU - PULSOWANIE */
    @keyframes pulse-red {
        0% { background-color: #ef4444; }
        50% { background-color: #7f1d1d; }
        100% { background-color: #ef4444; }
    }
    .chat-notify {
        animation: pulse-red 1.5s infinite;
        color: white !important;
        font-weight: bold;
    }

    /* KAFELKI METRYK */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 10px !important; }

    /* ZAKŁADKI */
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; margin-right: 5px !important; padding: 10px 20px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }

    /* WIADOMOŚCI CZATU */
    .chat-bubble { padding: 10px; border-radius: 15px; margin-bottom: 10px; max-width: 80%; }
    .chat-mine { background-color: #eab308; color: #1e293b; margin-left: auto; border-bottom-right-radius: 2px; }
    .chat-theirs { background-color: #334155; color: white; margin-right: auto; border-bottom-left-radius: 2px; }

    /* BELKA DOLNA */
    .main-sheet-footer { margin-top: 15px; padding: 5px 15px; background-color: #1e293b; border-top: 3px solid #eab308; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; color: white; }
    .footer-brand { font-size: 0.8rem; font-weight: 800; color: #eab308; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE TECHNICZNE (GSPREAD)
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if not dane: return pd.DataFrame()
        return pd.DataFrame(dane[1:], columns=dane[0])
    except: return pd.DataFrame()

def wyslij_wiadomosc(nadawca, odbiorca, tresc):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("CZAT")
        czas = datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([czas, nadawca, odbiorca, tresc, "NIEPRZECZYTANE"])
        return True
    except: return False

# ==========================================================
# 3. LOGIKA I SIDEBAR
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_chat = pobierz_df("CZAT")
nowe_wiadomosci = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty

with st.sidebar:
    st.markdown(f'<div style="text-align:center; margin-top:-30px;"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}" width="200"></a></div>', unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown(f'<div style="text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:20px;">System Zarządzania &copy; 2025<br><b>Andrzej Walczak</b></div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
# Zakładka czatu pulsuje, jeśli są nowe wiadomości
chat_label = "🔴 CZAT (NOWY!)" if nowe_wiadomosci else "🔴 CZAT"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_label])

# Widoki zadań (uproszczone dla czytelności kodu)
for i in range(3):
    with tabs[i]:
        kat = ["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"][i]
        df = pobierz_df(kat)
        if not df.empty:
            st.metric("📋 Razem w " + kat, len(df))
            st.data_editor(df, use_container_width=True, hide_index=True, height=500)

# --- MODUŁ CZATU ---
with tabs[3]:
    st.subheader("💬 Komunikator Służbowy")
    
    pracownicy = ["Marta", "Sławek", "Andrzej", "Agata", "Rafał"]
    col1, col2 = st.columns([1, 3])
    
    with col1:
        odbiorca = st.selectbox("Wybierz adresata:", [p for p in pracownicy if p != zalogowany])
        st.write("---")
        if nowe_wiadomosci:
            st.warning("Masz nowe wiadomości!")

    with col2:
        # Wyświetlanie historii rozmowy z wybranym odbiorcą
        history = df_chat[((df_chat['NADAWCA'] == zalogowany) & (df_chat['ODBIORCA'] == odbiorca)) | 
                         ((df_chat['NADAWCA'] == odbiorca) & (df_chat['ODBIORCA'] == zalogowany))]
        
        chat_container = st.container(height=400)
        for _, msg in history.iterrows():
            style = "chat-mine" if msg['NADAWCA'] == zalogowany else "chat-theirs"
            chat_container.markdown(f'<div class="chat-bubble {style}"><b>{msg["NADAWCA"]}</b><br>{msg["TREŚĆ"]}</div>', unsafe_allow_html=True)
        
        # Wysyłanie wiadomości
        with st.container():
            t_msg = st.text_input("Napisz wiadomość...", key="chat_input")
            if st.button("Wyślij ➔"):
                if t_msg:
                    if wyslij_wiadomosc(zalogowany, odbiorca, t_msg):
                        st.cache_data.clear(); st.rerun()

# --- ULTRA KOMPAKTOWA BELKA DOLNA ---
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))
st.markdown(f"""
    <div class="main-sheet-footer">
        <div class="footer-brand">UZDROWISKO CIECHOCINEK S.A.</div>
        <div class="footer-info">{now_pl.strftime('%d.%m.%Y | %H:%M:%S')} | Komunikator aktywny</div>
    </div>
""", unsafe_allow_html=True)
