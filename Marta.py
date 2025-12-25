import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (NAPRAWA ETYKIETY)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* LOGO */
    .logo-container { text-align: center; margin-top: -65px !important; margin-bottom: 25px !important; }
    .logo-container img { width: 200px; }
    
    /* --- NOWA, STABILNA ETYKIETA ZALOGOWANEGO --- */
    .user-info-footer {
        background-color: #eab308 !important;
        color: #1e293b !important;
        padding: 12px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 0.85rem;
        text-align: center;
        margin-top: 30px; /* Odstęp od ostatniego zadania */
        border: 2px solid white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* METRYKI */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 5px 10px !important; }
    
    /* ZAKŁADKI */
    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 25px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }
    
    .term-box { background: #334155; padding: 6px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 5px; color: white; font-size: 0.72rem; }
    .sidebar-header { color: #eab308; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGOWANIE I DANE
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")
if u_p in USERS and USERS[u_p] == k_p: zalogowany = u_p
else: st.error("BŁĄD LOGOWANIA"); st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=20)
def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df.iloc[:, 0].astype(str).str.strip() != ""].copy()
    except: return pd.DataFrame()

# ==========================================================
# 3. SIDEBAR (WIDOCZNY KOMPLET ELEMENTÓW)
# ==========================================================
df_biez = pobierz_df("Zadania bieżące")
df_chat = pobierz_df("CZAT")
has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty if not df_chat.empty else False

with st.sidebar:
    st.markdown(f'<div class="logo-container"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header" style="margin-top:-10px;">🧭 Nawigacja</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div style="border-top:1px solid #334155; margin:10px 0;"></div>', unsafe_allow_html=True)
    
    # SEKCJA TERMINÓW
    st.markdown('<div class="sidebar-header" style="margin-top:-5px;">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    # Prosty kalendarz HTML
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    cal_html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308;"><table style="width:100%; border-collapse:collapse; font-size:11px; font-family:sans-serif;">'
    for week in cal:
        cal_html += '<tr style="height:20px;">'
        for day in week:
            if day == 0: cal_html += "<td></td>"
            else:
                bg = "#eab308" if day == now.day else "transparent"
                cal_html += f'<td style="text-align:center; font-weight:700; background-color:{bg}; border-radius:4px;">{day}</td>'
        cal_html += "</tr>"
    cal_html += "</table></div>"
    st.markdown(cal_html, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header" style="margin-top:10px;">🕒 NADCHODZĄCE TWOJE</div>', unsafe_allow_html=True)
    if not df_biez.empty:
        df_side = df_biez if zalogowany == "Andrzej" else df_biez[df_biez['OSOBA'].str.contains(zalogowany, na=False)]
        for _, r in df_side.head(5).iterrows():
            dni = pd.to_numeric(r.get('DNI', 0), errors='coerce')
            st.markdown(f'<div class="term-box">{"🔥" if dni >= -2 else "🟢"} <b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:30]}...</div>', unsafe_allow_html=True)
    
    # --- ETYKIETA ZALOGOWANEGO (ZAINSTALOWANA NA SZTYWNO) ---
    u_name = "ANDRZEJ WALCZAK" if zalogowany == "Andrzej" else zalogowany.upper()
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {u_name}</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", f"💬 CZAT {'🔴' if has_new else ''}"])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df(kat)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📋 Razem", len(df))
        if not df.empty and 'DNI' in df.columns:
            df['D_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            m2.metric("🔥 Pilne (-2+)", len(df[df['D_N'] >= -2]))
            df_v = df.copy()
            df_v['TREŚĆ ZADANIA'] = df_v.apply(lambda r: f"{('🔥 ' if pd.to_numeric(r['DNI'], errors='coerce') >= -2 else '🟢 ')}{r['TREŚĆ ZADANIA']}", axis=1)
            st.data_editor(df_v.drop(columns=['D_N']), use_container_width=True, hide_index=True, height=800)
        m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))

with tabs[3]:
    st.subheader("💬 Messenger Firmowy")
    if not df_chat.empty:
        hist = df_chat[(df_chat['NADAWCA'] == zalogowany) | (df_chat['ODBIORCA'] == zalogowany)].tail(15)
        st.write("Wiadomości zostaną wyświetlone tutaj...") # Miejsce na dymki

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now_pl.strftime("%d.%m.%Y | %H:%M")}</span></div>', unsafe_allow_html=True)
