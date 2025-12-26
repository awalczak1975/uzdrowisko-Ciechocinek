import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I PEŁNA STYLIZACJA PANELU
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

APP_URL = "https://uzdrowisko-ciechocinek-nex3rfaat9fpxlpug35urd.streamlit.app/?u=Andrzej&k=8800"
LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }}
    
    /* AKTYWNE LOGO */
    .logo-link {{ display: block; text-align: center; margin-top: -65px !important; margin-bottom: 20px !important; cursor: pointer; }}
    .logo-link img {{ width: 190px; transition: transform 0.3s ease; }}
    .logo-link img:hover {{ transform: scale(1.05); }}
    
    /* KALENDARZ - POWRÓT DO CZYTELNOŚCI */
    .cal-container {{ background: white; padding: 10px; border-radius: 8px; border: 2px solid #eab308; width: 100%; margin-bottom: 15px; }}
    .cal-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 11px; color: #1e293b; }}
    .cal-table td {{ text-align: center; padding: 5px 1px; font-weight: 700; border-radius: 3px; }}
    .day-today {{ background-color: #eab308 !important; }}
    .day-task {{ color: #ef4444 !important; border: 1px solid #ef4444 !important; }}

    /* KAFELKI ZADAŃ (+2mm) */
    .term-box {{ background: #334155; padding: 14px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 12px; color: white; font-size: 0.75rem; line-height: 1.4; }}
    .sidebar-header {{ color: #eab308; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; margin-top: 15px; }}
    
    /* ETYKIETA ZALOGOWANEGO */
    .user-info-footer {{ background-color: #eab308 !important; color: #1e293b !important; padding: 10px; border-radius: 8px; font-weight: 900; font-size: 0.8rem; text-align: center; margin-top: 20px; border: 2px solid white; }}

    /* METRYKI WYŚRODKOWANE */
    [data-testid="stMetricValue"] > div {{ display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 1.8rem !important; }}
    [data-testid="stMetricLabel"] > div {{ display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }}
    [data-testid="stMetric"] {{ background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; text-align: center !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGIKA DANYCH
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

# ==========================================================
# 3. NAPRAWIONY LEWY PANEL (SIDEBAR)
# ==========================================================
df_biez = pobierz_arkusz("Zadania bieżące")

with st.sidebar:
    # 1. AKTYWNE LOGO
    st.markdown(f'<a href="{APP_URL}" target="_self" class="logo-link"><img src="{LOGO_URL}"></a>', unsafe_allow_html=True)
    
    # 2. NAWIGACJA
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    # 3. NAPRAWIONY KALENDARZ
    st.markdown('<div class="sidebar-header">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dt = pd.to_datetime(df_biez['DEADLINE'], errors='coerce', dayfirst=True) if not df_biez.empty else pd.Series()
    dni_task = set(dt[(dt.dt.month == now.month) & (dt.dt.year == now.year)].dt.day.dropna().astype(int))

    html = f'<div class="cal-container"><table class="cal-table"><thead><tr><th colspan="7">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html += '<tr>'
        for day in week:
            if day == 0: html += '<td></td>'
            else:
                cls = "day-today" if day == now.day else ""
                if day in dni_task: cls += " day-task"
                html += f'<td class="{cls}">{day}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

    # 4. POWIĘKSZONE NADCHODZĄCE ZADANIA
    st.markdown('<div class="sidebar-header">🕒 NADCHODZĄCE TWOJE</div>', unsafe_allow_html=True)
    if not df_biez.empty:
        df_side = df_biez if zalogowany == "Andrzej" else df_biez[df_biez['OSOBA'].str.contains(zalogowany, na=False)]
        for _, r in df_side.head(4).iterrows():
            st.markdown(f'<div class="term-box"><b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:25]}...</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {zalogowany.upper()} WALCZAK</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (ZACHOWANY)
# ==========================================================
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "CZAT 🔴"])
for i, nazwa in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df_tab = pobierz_arkusz(nazwa)
        if not df_tab.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem", len(df_tab))
            m3.metric("🕒 Aktualizacja", now.strftime("%H:%M"))
            st.data_editor(df_tab, use_container_width=True, hide_index=True, height=700)

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now.strftime("%d.%m.%Y")}</span></div>', unsafe_allow_html=True)
