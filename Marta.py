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

APP_URL = "https://uzdrowisko-ciechocinek-nex3rfaat9fpxlpug35urd.streamlit.app/"
LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }}
    .logo-link {{ display: block; text-align: center; margin-top: -65px !important; margin-bottom: 15px !important; cursor: pointer; }}
    .logo-link img {{ width: 185px; }}
    .user-info-footer {{ background-color: #eab308 !important; color: #1e293b !important; padding: 10px; border-radius: 8px; font-weight: 900; font-size: 0.85rem; text-align: center; margin-top: 10px; margin-bottom: 20px; border: 2px solid white; }}
    [data-testid="stMetricValue"] > div {{ display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }}
    [data-testid="stMetricLabel"] > div {{ display: flex !important; justify-content: center !important; color: white !important; font-weight: 700 !important; text-transform: uppercase; }}
    [data-testid="stMetric"] {{ background-color: #1e293b !important; border-top: 5px solid #eab308 !important; border-radius: 12px !important; padding: 15px !important; text-align: center !important; }}
    button[data-baseweb="tab"] {{ font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 30px !important; border: none !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGIKA DANYCH (FOKUS NA KOLUMNĘ A)
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")

if u_p in USERS and USERS[u_p] == k_p: zalogowany = u_p
else: st.error("BŁĄD LOGOWANIA"); st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=10)
def pobierz_arkusz(nazwa, filtruj=True):
    try:
        sh = polacz().open("Marta-Dział Techniczny")
        ws = sh.worksheet(nazwa)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        
        df = pd.DataFrame(dane[1:], columns=dane[0])
        # Kluczowe: bierzemy kolumny od A do F
        df = df.iloc[:, :6].copy()
        
        # FILTR: Tylko jeśli KOLUMNA A (index 0) nie jest pusta
        df = df[df.iloc[:, 0].str.strip() != ""].copy()
        
        def wstaw_emotke(row):
            try:
                # Kolumna DNI (index 4)
                raw_dni = str(row.iloc[4]).replace(',', '.').strip()
                dni = pd.to_numeric(raw_dni, errors='coerce')
                tresc_zadania = str(row.iloc[0])
                
                if "zrealizowane" in nazwa.lower(): return f"✅ {tresc_zadania}"
                # ZASADA: Dni >= -2 (czyli -2, -1, 0, 3, 7...) to PILNE 🔥
                if not pd.isna(dni) and dni >= -2:
                    return f"🔥 {tresc_zadania}"
                return f"⏳ {tresc_zadania}"
            except: return str(row.iloc[0])

        # Podmiana treści w KOLUMNIE A na wersję z ikoną
        df.iloc[:, 0] = df.apply(wstaw_emotke, axis=1)

        if filtruj:
            # Kolumna OSOBA (index 5)
            col_osoba = df.iloc[:, 5].str.lower()
            if zalogowany == "Sławek":
                return df[col_osoba.str.contains("sławek", na=False)].copy()
            elif zalogowany in ["Rafał", "Agata"]:
                return df[~col_osoba.str.contains("sławek", na=False)].copy()
        return df 
    except: return pd.DataFrame()

# ==========================================================
# 4. WIDOK GŁÓWNY (POPRAWIONE LICZNIKI)
# ==========================================================
df_biez_raw = pobierz_arkusz("Zadania bieżące", filtruj=True)
df_zreal_full = pobierz_arkusz("Zadania zrealizowane", filtruj=False)

lista_zakladek = ["Zadania bieżące", "Zadania zrealizowane"]
if zalogowany == "Andrzej": lista_zakladek.append("Terminy Sławka")
lista_zakladek.append("CZAT 🔴")

tabs = st.tabs(lista_zakladek)
now = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, nazwa in enumerate(lista_zakladek):
    if nazwa == "CZAT 🔴":
        with tabs[i]: st.info("Czat aktywny.")
        continue
    with tabs[i]:
        df_tab = pobierz_arkusz(nazwa, filtruj=True)
        m1, m2, m3, m4 = st.columns(4)
        
        count_razem = len(df_tab)
        pilne_count = 0
        if not df_tab.empty:
            # Przeliczenie kolumny DNI (index 4) na liczby dla metryki
            vals_dni = pd.to_numeric(df_tab.iloc[:, 4].astype(str).str.replace(',', '.'), errors='coerce').fillna(-999)
            pilne_count = len(df_tab[vals_dni >= -2])
        
        m1.metric("RAZEM", count_razem)
        m2.metric("PILNE 🔥", pilne_count)
        m3.metric("ZREALIZOWANE", len(df_zreal_full))
        m4.metric("AKTUALIZACJA", now.strftime("%H:%M"))
        
        st.markdown("---")
        if not df_tab.empty:
            st.data_editor(df_tab, use_container_width=True, hide_index=True, height=700)
        else:
            st.info("Brak zadań.")

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now.strftime("%d.%m.%Y")}</span></div>', unsafe_allow_html=True)
