import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (WYŚRODKOWANIE LICZB)
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

    .cal-container { background: white; padding: 6px; border-radius: 8px; border: 2px solid #eab308; width: 100%; margin-bottom: 10px; }
    .cal-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 10px; color: #1e293b; }
    .cal-table td { text-align: center; padding: 3px 1px; font-weight: 700; border-radius: 3px; }
    .day-today { background-color: #eab308 !important; }
    .day-task { color: #ef4444 !important; border: 1px solid #ef4444 !important; }

    .term-box { background: #334155; padding: 12px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 8px; color: white; font-size: 0.72rem; }
    .sidebar-header { color: #eab308; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; margin-top: 8px; }
    
    /* WYŚRODKOWANIE LICZB I ETYKIET W METRYKACH */
    [data-testid="stMetricValue"] > div { 
        display: flex !important; 
        justify-content: center !important; 
        color: #eab308 !important; 
        font-weight: 900 !important; 
        font-size: 1.8rem !important; 
    }
    [data-testid="stMetricLabel"] > div { 
        display: flex !important; 
        justify-content: center !important; 
        color: white !important; 
        font-weight: 600 !important; 
    }
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; 
        border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; 
        text-align: center !important;
    }

    button[data-baseweb="tab"] { 
        font-size: 1.1rem !important; 
        font-weight: 700 !important; 
        color: #1e293b !important; 
        background-color: #e2e8f0 !important; 
        border-radius: 8px 8px 0 0 !important; 
        padding: 10px 25px !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] { 
        color: white !important; 
        background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }
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
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df['TREŚĆ ZADANIA'].str.strip() != ""].copy()
    except: return pd.DataFrame()

# ==========================================================
# 3. SIDEBAR
# ==========================================================
df_biez_full = pobierz_arkusz("Zadania bieżące")
df_zreal_full = pobierz_arkusz("Zadania zrealizowane")
df_chat = pobierz_arkusz("CZAT")
has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty if not df_chat.empty else False

with st.sidebar:
    st.markdown(f'<div class="logo-container"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div class="sidebar-header">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_taskami = set()
    if not df_biez_full.empty:
        df_f = df_biez_full if zalogowany == "Andrzej" else df_biez_full[df_biez_full['OSOBA'].str.contains(zalogowany, na=False)]
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
    if not df_biez_full.empty:
        df_side = df_biez_full if zalogowany == "Andrzej" else df_biez_full[df_biez_full['OSOBA'].str.contains(zalogowany, na=False)]
        for _, r in df_side.head(4).iterrows():
            dni_v = pd.to_numeric(r.get('DNI', 0), errors='coerce')
            st.markdown(f'<div class="term-box">{"🔥" if dni_v >= -2 else "🟢"} <b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:25]}...</div>', unsafe_allow_html=True)
    
    u_name = "ANDRZEJ WALCZAK" if zalogowany == "Andrzej" else zalogowany.upper()
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {u_name}</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (WYŚRODKOWANE LICZNIKI)
# ==========================================================
chat_tab_label = f"💬 CZAT {'🔴' if has_new else ''}"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_tab_label])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

count_zreal = df_zreal_full.iloc[:, 0].replace('', pd.NA).dropna().count() if not df_zreal_full.empty else 0

for i, nazwa in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df_tab = pobierz_arkusz(nazwa)
        m1, m2, m3, m4 = st.columns(4)
        
        if not df_tab.empty:
            count_razem = df_tab.iloc[:, 0].replace('', pd.NA).dropna().count()
            df_tab['DNI_N'] = pd.to_numeric(df_tab['DNI'], errors='coerce').fillna(-999)
            
            m1.metric("📋 Razem", int(count_razem))
            m2.metric("🔥 Pilne (-2+)", len(df_tab[df_tab['DNI_N'] >= -2]))
            m3.metric("✅ Zrealizowane", int(count_zreal))
            m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
            
            df_tab['TREŚĆ ZADANIA'] = df_tab.apply(lambda r: f"{('🔥 ' if r['DNI_N'] >= -2 else '🟢 ')}{r['TREŚĆ ZADANIA']}", axis=1)
            st.data_editor(df_tab.drop(columns=['DNI_N']), use_container_width=True, hide_index=True, height=800)
        else:
            m1.metric("📋 Razem", 0); m2.metric("🔥 Pilne (-2+)", 0)
            st.info("Brak zadań.")

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now_pl.strftime("%d.%m.%Y | %H:%M")}</span></div>', unsafe_allow_html=True)
