import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz
import streamlit.components.v1 as components

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

# URL do restartu widoku głównego dla Andrzeja
APP_URL = "https://uzdrowisko-ciechocinek-nex3rfaat9fpxlpug35urd.streamlit.app/?u=Andrzej&k=8800"
LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }}
    
    .user-info-footer {{
        background-color: #eab308 !important;
        color: #1e293b !important;
        padding: 10px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 15px;
        border: 2px solid white;
    }}

    [data-testid="stMetricValue"] > div {{ display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 1.8rem !important; }}
    [data-testid="stMetricLabel"] > div {{ display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }}
    [data-testid="stMetric"] {{ background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; text-align: center !important; }}

    button[data-baseweb="tab"] {{ font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 25px !important; border: none !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }}

    .cal-container {{ background: white; padding: 8px; border-radius: 8px; border: 2px solid #eab308; width: 100%; margin-bottom: 10px; }}
    .cal-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 10px; color: #1e293b; }}
    .cal-table td {{ text-align: center; padding: 4px 1px; font-weight: 700; border-radius: 3px; }}
    .day-today {{ background-color: #eab308 !important; }}
    .day-task {{ color: #ef4444 !important; border: 1px solid #ef4444 !important; }}
    .term-box {{ background: #334155; padding: 14px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 10px; color: white; font-size: 0.75rem; }}
    .sidebar-header {{ color: #eab308; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; margin-top: 10px; }}
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
        if 'TREŚĆ ZADANIA' in df.columns:
            df = df[df['TREŚĆ ZADANIA'].str.strip() != ""].copy()
        return df
    except: return pd.DataFrame()

# ==========================================================
# 3. SIDEBAR (PANCERNE LOGO)
# ==========================================================
with st.sidebar:
    # KOMPONENT HTML WYMUSZAJĄCY KLIKALNOŚĆ LOGO
    logo_html = f"""
    <div style="text-align: center; cursor: pointer; margin-top: -30px;">
        <a href="{APP_URL}" target="_top" style="text-decoration: none;">
            <img src="{LOGO_URL}" style="width: 190px; transition: transform 0.3s;" 
                 onmouseover="this.style.transform='scale(1.05)'" 
                 onmouseout="this.style.transform='scale(1)'">
        </a>
    </div>
    """
    components.html(logo_html, height=120)
    
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div class="sidebar-header">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    # Kalendarz i reszta panelu...
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    html = f'<div class="cal-container"><table class="cal-table"><thead><tr><th colspan="7">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html += '<tr>'
        for day in week:
            if day == 0: html += '<td></td>'
            else:
                cls = "day-today" if day == now.day else ""
                html += f'<td class="{cls}">{day}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: ANDRZEJ WALCZAK</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "CZAT 🔴"])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, nazwa in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df_tab = pobierz_arkusz(nazwa)
        if not df_tab.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem", len(df_tab))
            m3.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
            st.data_editor(df_tab, use_container_width=True, hide_index=True, height=700)

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now_pl.strftime("%d.%m.%Y")}</span></div>', unsafe_allow_html=True)
