import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I PEŁNA STYLIZACJA (NAPRAWA PANELU)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=10000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0px !important; }
    
    /* PANEL BOCZNY - POWRÓT DO SPRAWDZONEGO STYLU */
    [data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 5px solid #eab308 !important; 
    }
    
    /* LOGO JAKO PRZYCISK HOME */
    .logo-container { text-align: center; margin-top: -35px !important; margin-bottom: 15px !important; }
    .logo-container img { width: 190px; cursor: pointer; transition: 0.3s; }
    .logo-container img:hover { transform: scale(1.02); }

    /* POWIADOMIENIA CZATU */
    .new-msg-alert { color: #ef4444 !important; font-weight: 900 !important; text-align: center; animation: blinker 1.5s linear infinite; margin-top: 10px; }
    @keyframes blinker { 50% { opacity: 0; } }

    /* PRZYCISKI W SIDEBARZE */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
        height: 44px !important; margin-bottom: 5px !important;
    }

    /* KALENDARZ I NADCHODZĄCE TERMINY */
    .sidebar-section-title { color: white; font-weight: bold; margin-bottom: 5px; font-size: 0.9rem; margin-top: 10px; }

    /* METRYKI GŁÓWNE */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 10px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

    /* ZAKŁADKI GÓRNE */
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; margin-right: 5px !important; padding: 10px 20px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }

    /* BELKA DOLNA */
    .main-sheet-footer { margin-top: 15px; padding: 5px 15px; background-color: #1e293b; border-top: 3px solid #eab308; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; color: white; }
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
        ws.append_row([datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%Y-%m-%d %H:%M:%S"), nadawca, odbiorca, tresc, "NIEPRZECZYTANE"])
        return True
    except: return False

def play_sound():
    st.markdown('<audio autoplay="true" style="display:none;"><source src="https://www.soundjay.com/buttons/beep-07a.mp3" type="audio/mpeg"></audio>', unsafe_allow_html=True)

def generuj_kalendarz_html(df_zadania):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    rok, miesiac = now.year, now.month
    cal = calendar.monthcalendar(rok, miesiac)
    pilne_daty = []
    if not df_zadania.empty and 'DEADLINE' in df_zadania.columns:
        df_zadania['DT'] = pd.to_datetime(df_zadania['DEADLINE'], dayfirst=True, errors='coerce')
        pilne_daty = df_zadania[(df_zadania['DT'].dt.month == miesiac)]['DT'].dt.day.unique().tolist()
    
    html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; font-size:12px; border-bottom:1px solid #eee;">{calendar.month_name[miesiac].upper()} {rok}</th></tr><tr style="color:#64748b; font-size:8px; text-align:center;"><th>PN</th><th>WT</th><th>ŚR</th><th>CZ</th><th>PT</th><th>SO</th><th>ND</th></tr></thead><tbody style="color:#1e293b;">'
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                bg = "#eab308" if day == now.day else "transparent"
                html += f'<td style="text-align:center; padding:3px 1px; font-size:10px; font-weight:700; background-color:{bg}; border-radius:4px;">{day}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 3. LOGIKA I SIDEBAR (PRZYWRÓCONY PORZĄDEK)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_chat = pobierz_df("CZAT")
has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty if not df_chat.empty and 'ODBIORCA' in df_chat.columns else False

with st.sidebar:
    # LOGO HOME
    st.markdown(f'<div class="logo-container"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    
    st.markdown('<div style="border-bottom:1px solid #334155; margin:0 0 10px 0;"></div>', unsafe_allow_html=True)
    
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    # KALENDARZ
    st.components.v1.html(generuj_kalendarz_html(pobierz_df("Zadania bieżące")), height=160)
    
    # TERMINY
    st.markdown('<div class="sidebar-section-title">📅 Terminy:</div>', unsafe_allow_html=True)
    df_term = pobierz_df("Zadania bieżące")
    if not df_term.empty:
        for _, r in df_term.head(2).iterrows():
            st.markdown(f"<div style='background:#334155; padding:6px; border-radius:6px; border-left:3px solid #ef4444; margin-bottom:4px; color:white; font-size:0.75rem;'><b>{r['DEADLINE']}</b>: {r['TREŚĆ ZADANIA'][:30]}...</div>", unsafe_allow_html=True)
    
    # POWIADOMIENIE
    if has_new:
        st.markdown('<p class="new-msg-alert">🔔 NOWA WIADOMOŚĆ!</p>', unsafe_allow_html=True)
        play_sound()

    now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))
    st.markdown(f'<div class="sidebar-footer">System &copy; {now_pl.year}<br><b>{zalogowany}</b></div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
c_title = "💬 CZAT (NOWY!)" if has_new else "💬 CZAT"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", c_title])

for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📋 Razem", len(df))
            m4.metric("🕒 Czas", now_pl.strftime("%H:%M"))
            st.data_editor(df, use_container_width=True, hide_index=True, height=550)

with tabs[3]:
    pracownicy = ["Marta", "Sławek", "Andrzej", "Agata", "Rafał"]
    odbiorca = st.selectbox("Adresat:", [p for p in pracownicy if p != zalogowany])
    chat_box = st.container(height=380, border=True)
    if not df_chat.empty and 'TREŚĆ' in df_chat.columns:
        history = df_chat[((df_chat['NADAWCA'] == zalogowany) & (df_chat['ODBIORCA'] == odbiorca)) | ((df_chat['NADAWCA'] == odbiorca) & (df_chat['ODBIORCA'] == zalogowany))]
        for _, msg in history.tail(10).iterrows():
            cls = "chat-mine" if msg['NADAWCA'] == zalogowany else "chat-theirs"
            chat_box.markdown(f'<div class="chat-bubble {cls}"><b>{msg["NADAWCA"]}</b>: {msg["TREŚĆ"]}</div>', unsafe_allow_html=True)
    t_input = st.chat_input("Napisz...")
    if t_input and wyslij_wiadomosc(zalogowany, odbiorca, t_input): st.rerun()

# BELKA DOLNA
st.markdown(f'<div class="main-sheet-footer"><div style="color:#eab308; font-weight:800; font-size:0.8rem;">UZDROWISKO CIECHOCINEK S.A.</div><div style="font-size:0.7rem; color:#94a3b8;">{now_pl.strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)
