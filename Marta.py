import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA
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
        padding: 10px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 20px;
        border: 2px solid white;
    }

    .cal-container { background: white; padding: 5px; border-radius: 8px; border: 2px solid #eab308; width: 100%; }
    .cal-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 10px; color: #1e293b; }
    .cal-table td { text-align: center; padding: 1px; font-weight: 700; border-radius: 3px; }
    .day-today { background-color: #eab308 !important; }
    .day-task { color: #ef4444 !important; border: 1px solid #ef4444 !important; }

    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 5px 10px !important; }
    
    .term-box { background: #334155; padding: 6px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 5px; color: white; font-size: 0.7rem; }
    .sidebar-header { color: #eab308; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. DANE I LOGOWANIE
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")
if u_p in USERS and USERS[u_p] == k_p: zalogowany = u_p
else: st.error("BŁĄD LOGOWANIA"); st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=15)
def pobierz_arkusz(nazwa):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(nazwa)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        return pd.DataFrame(dane[1:], columns=dane[0])
    except: return pd.DataFrame()

# ==========================================================
# 3. SIDEBAR
# ==========================================================
df_biez = pobierz_arkusz("Zadania bieżące")
df_zreal = pobierz_arkusz("Zadania zrealizowane")
df_chat = pobierz_arkusz("CZAT")

with st.sidebar:
    st.markdown(f'<div class="logo-container"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header" style="margin-top:-10px;">🧭 Nawigacja</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div class="sidebar-header">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    # Generowanie kalendarza
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_taskami = set()
    if not df_biez.empty:
        df_f = df_biez if zalogowany == "Andrzej" else df_biez[df_biez['OSOBA'].str.contains(zalogowany, na=False)]
        deadlines = pd.to_datetime(df_f['DEADLINE'], errors='coerce', dayfirst=True)
        dni_z_taskami = set(deadlines[(deadlines.dt.month == now.month) & (deadlines.dt.year == now.year)].dt.day.dropna().astype(int))

    html_cal = f'<div class="cal-container"><table class="cal-table"><thead><tr><th colspan="7">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html_cal += '<tr>'
        for day in week:
            if day == 0: html_cal += '<td></td>'
            else:
                cls = "day-today" if day == now.day else ""
                if day in dni_z_taskami: cls += " day-task"
                html_cal += f'<td class="{cls}">{day}</td>'
        html_cal += '</tr>'
    st.markdown(html_cal + '</tbody></table></div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-header">🕒 NADCHODZĄCE TWOJE</div>', unsafe_allow_html=True)
    if not df_biez.empty:
        df_side = df_biez if zalogowany == "Andrzej" else df_biez[df_biez['OSOBA'].str.contains(zalogowany, na=False)]
        for _, r in df_side.head(5).iterrows():
            dni_v = pd.to_numeric(r.get('DNI', 0), errors='coerce')
            st.markdown(f'<div class="term-box">{"🔥" if dni_v >= -2 else "🟢"} <b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:25]}...</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {"ANDRZEJ WALCZAK" if zalogowany == "Andrzej" else zalogowany.upper()}</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (POPRAWNY LICZNIK "RAZEM")
# ==========================================================
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", f"💬 CZAT"])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, nazwa in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df_raw = pobierz_arkusz(nazwa)
        m1, m2, m3, m4 = st.columns(4)
        
        if not df_raw.empty:
            # KLUCZOWA POPRAWKA: Sumowanie wartości z Kolumny A (indeks 0)
            try:
                suma_razem = pd.to_numeric(df_raw.iloc[:, 0], errors='coerce').sum()
                # Jeśli suma jest 0 (np. kolumna A to teksty), pokazujemy liczbę wierszy
                if suma_razem == 0: suma_razem = len(df_raw)
            except: suma_razem = len(df_raw)
            
            df_raw['DNI_N'] = pd.to_numeric(df_raw['DNI'], errors='coerce').fillna(-999)
            m1.metric("📋 Razem", int(suma_razem))
            m2.metric("🔥 Pilne (-2+)", len(df_raw[df_raw['DNI_N'] >= -2]))
            
            df_v = df_raw.copy()
            df_v['TREŚĆ ZADANIA'] = df_v.apply(lambda r: f"{('🔥 ' if r['DNI_N'] >= -2 else '🟢 ')}{r['TREŚĆ ZADANIA']}", axis=1)
            st.data_editor(df_v.drop(columns=['DNI_N']), use_container_width=True, hide_index=True, height=800)
        else:
            m1.metric("📋 Razem", 0); m2.metric("🔥 Pilne (-2+)", 0)
            st.info("Brak zadań.")
        
        m3.metric("✅ Zrealizowane", len(df_zreal))
        m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now_pl.strftime("%d.%m.%Y | %H:%M")}</span></div>', unsafe_allow_html=True)
