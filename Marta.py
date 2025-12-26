import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

# ==========================================================
# 2. STYLING (CSS)
# ==========================================================
st.markdown("""
<style>
/* UKŁAD */
.block-container { padding-top: 0.5rem !important; }
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
    border-right: 5px solid #eab308 !important;
    min-width: 310px !important;
}

/* LOGO W SIDEBARZE */
.logo-link { display: block; text-align: center; margin-top: -30px !important; margin-bottom: 20px !important; }
.logo-link img { width: 180px; }

/* ZAKŁADKI */
button[data-baseweb="tab"] {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #1e293b !important;
    background-color: #cbd5e1 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 8px 25px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: white !important;
    background-color: #0f172a !important;
    border-bottom: 5px solid #ef4444 !important;
}

/* NAGŁÓWEK TABELI */
div[data-testid="stDataFrame"] thead tr th {
    background-color: #0f172a !important;
    border-bottom: 3px solid #eab308 !important;
}
div[data-testid="stDataFrameHeaderCell"] * {
    color: #eab308 !important;
    font-weight: 900 !important;
    text-transform: uppercase;
}

/* PIERWSZY WIERSZ DANYCH */
div[data-testid="stDataFrame"] tbody tr:first-child {
    background-color: #fef3c7 !important;
}
div[data-testid="stDataFrame"] tbody tr:first-child td {
    color: #92400e !important;
    font-weight: 800 !important;
}

/* METRYKI */
[data-testid="stMetric"] {
    background-color: #1e293b !important;
    border-top: 5px solid #eab308 !important;
    border-radius: 12px !important;
    padding: 10px !important;
}
[data-testid="stMetricValue"] > div {
    color: #eab308 !important;
    font-weight: 900 !important;
    font-size: 2rem !important;
}
[data-testid="stMetricLabel"] > div {
    color: white !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.8rem !important;
}

/* Sidebar Text Color */
[data-testid="stSidebar"] section[data-testid="stSidebarNav"] + div {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 3. LOGIKA DANYCH
# ==========================================================
USERS = {
    "Andrzej": "8800", "Marta": "1111", "Sławek": "2222",
    "Agata": "3333", "Rafał": "4444", "Dagmara": "5555",
    "Ewelina": "6666", "Ireneusz": "7777"
}

u_p = st.query_params.get("u", "")
k_p = st.query_params.get("k", "")

if u_p in USERS and USERS[u_p] == k_p:
    zalogowany = u_p
else:
    st.error("BŁĄD LOGOWANIA - Nieprawidłowe parametry w adresie URL.")
    st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

@st.cache_data(ttl=10)
def pobierz_arkusz(nazwa):
    sh = polacz().open("Marta-Dział Techniczny")
    ws = sh.worksheet(nazwa)
    dane = ws.get_all_values()
    df = pd.DataFrame(dane[1:], columns=dane[0])
    df = df[df.iloc[:, 0].str.strip() != ""]
    return df

# ==========================================================
# 4. UI - PANEL BOCZNY (SIDEBAR)
# ==========================================================
with st.sidebar:
    # Wyświetlenie logo
    st.markdown(f'<div class="logo-link"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    
    st.markdown("<h3 style='color: white; text-align: center;'>SYSTEM OPERACYJNY</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Informacje o użytkowniku
    st.write(f"👤 Zalogowany: **{zalogowany}**")
    st.write(f"📅 Data: {datetime.now(pytz.timezone('Europe/Warsaw')).strftime('%d.%m.%Y')}")
    
    st.markdown("---")
    
    # Dodatkowy przycisk odświeżania w panelu
    if st.button("🔄 Odśwież dane"):
        st.cache_data.clear()
        st.rerun()

# ==========================================================
# 5. UI - GŁÓWNA TREŚĆ
# ==========================================================
df = pobierz_arkusz("Zadania bieżące")
now = datetime.now(pytz.timezone("Europe/Warsaw"))

tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "CZAT 🔴"])

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    # Wyświetlamy statystyki
    c1.metric("RAZEM", len(df))
    # Przykład: liczymy zadania "PILNE" (zakładając, że masz taką kolumnę lub logikę)
    c2.metric("PILNE 🔥", len(df)) 
    c3.metric("ZREALIZOWANE", 0)
    c4.metric("AKTUALIZACJA", now.strftime("%H:%M"))

    st.markdown("---")
    # Tabela zadań
    st.data_editor(df, use_container_width=True, hide_index=True, height=700)

with tabs[1]:
    st.info("Tutaj pojawią się zadania przeniesione do archiwum.")

with tabs[2]:
    st.info("Moduł czatu komunikacyjnego.")
