import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (NAPRAWA ZAZNACZANIA DAT)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .logo-container { text-align: center; margin-top: -65px !important; margin-bottom: 25px !important; }
    .logo-container img { width: 200px; }
    
    .user-info-footer {
        background-color: #eab308 !important;
        color: #1e293b !important;
        padding: 12px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 0.85rem;
        text-align: center;
        margin-top: 25px;
        border: 2px solid white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* KOMPAKTOWY KALENDARZ */
    .cal-container { 
        background: white; 
        padding: 5px; 
        border-radius: 8px; 
        border: 2px solid #eab308;
        max-width: 260px;
        margin: 0 auto;
    }
    .cal-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 10px; color: #1e293b; }
    .cal-table th { color: #1e293b; text-align: center; font-weight: 800; border-bottom: 1px solid #eee; padding-bottom: 2px; }
    .cal-table td { text-align: center; padding: 2px; font-weight: 700; border-radius: 3px; width: 14.28%; }
    
    /* STYLE DNI */
    .day-today { background-color: #eab308 !important; color: #1e293b !important; }
    .day-task { color: #ef4444 !important; border: 1px solid #ef4444 !important; background-color: #fff5f5; }
    
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
# 3. FUNKCJA KALENDARZA (POPRAWIONE WYKRYWANIE DAT)
# ==========================================================
def generuj_kalendarz_html(df_zadania, user):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_terminami = set()
    
    if not df_zadania.empty and 'DEADLINE' in df_zadania.columns:
        # Filtracja zadań dla użytkownika
        df_f = df_zadania if user == "Andrzej" else df_zadania[df_zadania['OSOBA'].str.contains(user, na=False)]
        
        # Konwersja kolumny DEADLINE na obiekty daty dla porównania
        deadlines = pd.to_datetime(df_f['DEADLINE'], errors='coerce', dayfirst=True)
        
        # Wybieramy tylko dni z bieżącego miesiąca i roku
        mask = (deadlines.dt.month == now.month) & (deadlines.dt.year == now.year)
        dni_z_terminami = set(deadlines[mask].dt.day.dropna().astype(int).tolist())

    html = f'<div class="cal-container">'
    html += f'<table class="cal-table"><thead><tr><th colspan="7">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    
    for week in cal:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td></td>'
            else:
                classes = []
                if day == now.day: classes.append("day-today")
                if day in dni_z_terminami: classes.append("day-task")
                html += f'<td class="{" ".join(classes)}">{day}</td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    return html

# ==========================================================
# 4. SIDEBAR
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
    
    st.markdown('<div class="sidebar-header" style="margin-top:-5px;">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    st.markdown(generuj_kalendarz_html(df_biez, zalogowany), unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header" style="margin-top:15px;">🕒 NADCHODZĄCE TWOJE</div>', unsafe_allow_html=True)
    if not df_biez.empty:
        df_side = df_biez if zalogowany == "Andrzej" else df_biez[df_biez['OSOBA'].str.contains(zalogowany, na=False)]
        for _, r in df_side.head(5).iterrows():
            dni = pd.to_numeric(r.get('DNI', 0), errors='coerce')
            st.markdown(f'<div class="term-box">{"🔥" if dni >= -2 else "🟢"} <b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:30]}...</div>', unsafe_allow_html=True)
    
    u_name = "ANDRZEJ WALCZAK" if zalogowany == "Andrzej" else zalogowany.upper()
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {u_name}</div>', unsafe_allow_html=True)

# Widok główny pozostaje bez zmian (kod z poprzednich wersji)
# ... (Zadania bieżące, zrealizowane, czat)
