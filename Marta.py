import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. PEŁNA STYLIZACJA (IMIĘ WIKIMI LITERAMI)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

APP_URL = "https://uzdrowisko-ciechocinek-nex3rfaat9fpxlpug35urd.streamlit.app/"
LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }}
    .logo-link {{ display: block; text-align: center; margin-top: -65px !important; margin-bottom: 15px !important; cursor: pointer; }}
    .logo-link img {{ width: 185px; }}
    .user-info-footer {{ background-color: #eab308 !important; color: #1e293b !important; padding: 10px; border-radius: 8px; font-weight: 900; font-size: 0.85rem; text-align: center; margin-top: 5px; margin-bottom: 20px; border: 2px solid white; }}
    [data-testid="stMetricValue"] > div {{ display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }}
    [data-testid="stMetricLabel"] > div {{ display: flex !important; justify-content: center !important; color: white !important; font-weight: 700 !important; text-transform: uppercase; }}
    [data-testid="stMetric"] {{ background-color: #1e293b !important; border-top: 5px solid #eab308 !important; border-radius: 12px !important; padding: 15px !important; text-align: center !important; }}
    button[data-baseweb="tab"] {{ font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 30px !important; border: none !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGIKA UPRAWNIEŃ I FILTROWANIA
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")

if u_p in USERS and USERS[u_p] == k_p:
    zalogowany = u_p
else:
    st.error("BŁĄD LOGOWANIA"); st.stop()

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
        df = df[df['TREŚĆ ZADANIA'].str.strip() != ""].copy()
        
        # --- FILTROWANIE DANYCH WEDŁUG UPRAWNIEŃ ---
        if zalogowany == "Sławek":
            return df[df['OSOBA'].str.contains("Sławek", na=False)].copy()
        elif zalogowany in ["Rafał", "Agata"]:
            return df[~df['OSOBA'].str.contains("Sławek", na=False)].copy()
        return df # Andrzej i Marta widzą wszystko w tych arkuszach
    except: return pd.DataFrame()

# ==========================================================
# 3. SIDEBAR (DYNAMICZNY LINK I IMIĘ)
# ==========================================================
df_biez = pobierz_arkusz("Zadania bieżące")
PERSONAL_URL = f"{APP_URL}?u={zalogowany}&k={USERS[zalogowany]}"

with st.sidebar:
    st.markdown(f'<a href="{PERSONAL_URL}" target="_self" class="logo-link"><img src="{LOGO_URL}"></a>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {zalogowany.upper()}</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (FILTROWANIE ZAKŁADEK)
# ==========================================================
# Określenie dostępnych zakładek
lista_zakladek = ["Zadania bieżące", "Zadania zrealizowane"]
if zalogowany == "Andrzej":
    lista_zakladek.append("Terminy Sławka")
# Zakładka Czat dostępna dla wszystkich
lista_zakladek.append("CZAT 🔴")

tabs = st.tabs(lista_zakladek)
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, nazwa in enumerate(lista_zakladek):
    if nazwa == "CZAT 🔴":
        with tabs[i]:
            st.info("Komunikator firmowy aktywny.")
        continue
        
    with tabs[i]:
        df_tab = pobierz_arkusz(nazwa)
        m1, m2, m3, m4 = st.columns(4)
        if not df_tab.empty:
            df_tab['DNI_N'] = pd.to_numeric(df_tab['DNI'], errors='coerce').fillna(-999)
            m1.metric("📋 Razem", len(df_tab))
            m2.metric("🔥 Pilne (-2+)", len(df_tab[df_tab['DNI_N'] >= -2]))
            m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
            st.markdown("---")
            st.data_editor(df_tab.drop(columns=['DNI_N']), use_container_width=True, hide_index=True, height=700)
        else:
            st.info("Brak zadań do wyświetlenia dla Twoich uprawnień.")

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now_pl.strftime("%d.%m.%Y")}</span></div>', unsafe_allow_html=True)
