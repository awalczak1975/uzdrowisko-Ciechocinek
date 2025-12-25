import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# ==========================================================
# 1. KONFIGURACJA STRONY
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=300000, key="datarefresh")

# ==========================================================
# 2. DANE DOSTĘPOWE
# ==========================================================
KLUCZE_DOSTEPU = {"Andrzej": "8800", "Marta": "1234", "Rafał": "5566", "Agata": "9911", "Sławek": "4422"}
TELEGRAM_TOKEN = "7547926145:AAHnOIdm6n6_uK03Kk_o0-U0q2F8C_xLpY8"
TELEGRAM_CHAT_ID = "543788771"
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
LISTA_OSOB = list(KLUCZE_DOSTEPU.keys())

# ==========================================================
# 3. WERYFIKACJA UŻYTKOWNIKA
# ==========================================================
user_url = st.query_params.get("u", "")
key_url = st.query_params.get("k", "")

if user_url in KLUCZE_DOSTEPU and KLUCZE_DOSTEPU[user_url] == key_url:
    zalogowany_uzytkownik = user_url
    czy_andrzej = (user_url == "Andrzej")
    czy_admin = (user_url in ["Andrzej", "Marta"])
else:
    st.error("❌ BŁĄD DOSTĘPU")
    st.stop()

# ==========================================================
# 4. FUNKCJE GOOGLE SHEETS (Ograniczenie do 5 kolumn)
# ==========================================================
def polacz_z_google():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], 
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_dane_final(nazwa_zakladki):
    try:
        client = polacz_z_google()
        wb = client.open(NAZWA_ARKUSZA)
        ws = wb.worksheet(nazwa_zakladki)
        # POBIERAMY TYLKO ZAKRES A1:E500 (5 kolumn)
        dane_raw = ws.get('A1:E500')
        if not dane_raw: return pd.DataFrame()
        df = pd.DataFrame(dane_raw[1:], columns=dane_raw[0])
        df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
        return df
    except:
        return pd.DataFrame()

def aktualizuj_arkusz(df_nowy, nazwa_zakladki):
    try:
        client = polacz_z_google()
        ws = client.open(NAZWA_ARKUSZA).worksheet(nazwa_zakladki)
        # Przygotowanie danych do zapisu (tylko 5 kolumn)
        dane_do_zapisu = [df_nowy.columns.values.tolist()] + df_nowy.values.tolist()
        # AKTUALIZUJEMY TYLKO ZAKRES A:E, aby nie uszkodzić formuł w kolumnie F
        ostatni_wiersz = len(dane_do_zapisu)
        zakres = f"A1:E{ostatni_wiersz}"
        ws.update(zakres, dane_do_zapisu)
        return True
    except:
        return False

# ==========================================================
# 5. STYLIZACJA CSS
# ==========================================================
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .stButton button { background-color: #334155 !important; color: white !important; border: 1px solid #94a3b8 !important; font-size: 0.8rem !important; width: 100%; }
    
    [data-testid="stMetric"] { 
        background-color: white !important; border-top: 4px solid #eab308 !important; 
        border-radius: 8px !important; padding: 15px !important; text-align: center !important; 
    }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; font-weight: 900 !important; font-size: 2.2rem !important; color: #1e293b !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; font-size: 1.1rem !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 6. PANEL BOCZNY
# ==========================================================
with st.sidebar:
    st.markdown("<h2 style='color: #0ea5e9; text-align:center;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h2>", unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 ODŚWIEŻ DANE"):
        st.cache_data.clear(); st.rerun()
    st.write(f"Zalogowany: **{zalogowany_uzytkownik}**")

# ==========================================================
# 7. WIDOK GŁÓWNY
# ==========================================================
if 'widok' not in st.session_state: st.session_state['widok'] = 'biezace'

if czy_andrzej:
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("📋 BIEŻĄCE", use_container_width=True): st.session_state['widok'] = 'biezace'
    with c2: 
        if st.button("✅ ZREALIZOWANE", use_container_width=True): st.session_state['widok'] = 'zrealizowane'
    with c3: 
        if st.button("🔧 SŁAWEK", use_container_width=True): st.session_state['widok'] = 'slawek'
else:
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("📋 BIEŻĄCE", use_container_width=True): st.session_state['widok'] = 'biezace'
    with c2: 
        if st.button("✅ ZREALIZOWANE", use_container_width=True): st.session_state['widok'] = 'zrealizowane'

mapa = {'biezace': "Zadania bieżące", 'zrealizowane': "Zadania zrealizowane", 'slawek': "Terminy Sławka"}
zakladka_aktualna = mapa[st.session_state['widok']]
df = pobierz_dane_final(zakladka_aktualna)

if not df.empty:
    # Sortowanie daty
    kol_data = "DEADLINE" if "DEADLINE" in df.columns else "TERMIN"
    if kol_data in df.columns:
        df['tmp'] = pd.to_datetime(df[kol_data], dayfirst=True, errors='coerce')
        df = df.sort_values(by='tmp', ascending=True).drop(columns=['tmp'])

    # Filtry uprawnień
    if not czy_admin:
        if zalogowany_uzytkownik == "Sławek":
            if st.session_state['widok'] != 'slawek' and 'OSOBA' in df.columns:
                df = df[df['OSOBA'] == "Sławek"]
        else:
            if 'OSOBA' in df.columns:
                df = df[df['OSOBA'] != "Sławek"]

    # Metryki
    m1, m2, m3 = st.columns(3)
    m1.metric("📋 Razem", len(df))
    if 'DNI' in df.columns:
        df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(0)
        # -2 dni do realizacji to pilne
        m2.metric("🔥 Pilne/Spóźnione", len(df[df['DNI_N'] >= -2]))
    else: m2.metric("Status", "Aktywne")
    m3.metric("🕒 Godzina", datetime.now().strftime("%H:%M"))

    # EDYTOR TABELI
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True, 
        height=600,
        disabled=not czy_admin,
        column_config={"DNI_N": None}
    )

    # Przycisk zapisu dla Admina
    if czy_admin and not edited_df.equals(df):
        if st.button("💾 ZAPISZ ZMIANY (KOLUMNY A-E)", type="primary"):
            # Upewniamy się, że zapisujemy tylko 5 kolumn, nawet jeśli w DataFrame jest ich więcej (np. DNI_N)
            df_do_zapisu = edited_df.iloc[:, :5]
            if aktualizuj_arkusz(df_do_zapisu, zakladka_aktualna):
                st.success("Zaktualizowano kolumny A:E!")
                st.cache_data.clear(); st.rerun()
            else:
                st.error("Błąd zapisu.")
else:
    st.info(f"Brak zadań w: {zakladka_aktualna}")
