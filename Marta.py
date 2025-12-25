import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# ==========================================================
# 1. KONFIGURACJA
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

# ==========================================================
# 3. WERYFIKACJA
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
# 4. FUNKCJA POBIERANIA (ULEPSZONA)
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
        # Otwieramy arkusz i szukamy zakładki (bezwzględnie)
        wb = client.open(NAZWA_ARKUSZA)
        ws = wb.worksheet(nazwa_zakladki)
        
        # Pobieramy wszystkie wartości jako tekst (najbardziej odporna metoda)
        dane_raw = ws.get_all_values()
        
        if not dane_raw or len(dane_raw) < 1:
            return pd.DataFrame()
        
        # Tworzymy tabelę: pierwszy wiersz to nagłówki, reszta to dane
        headers = dane_raw[0]
        data = dane_raw[1:]
        
        df = pd.DataFrame(data, columns=headers)
        
        # Usuwamy całkowicie puste wiersze
        df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
        return df
    except Exception as e:
        st.error(f"Problem z zakładką '{nazwa_zakladki}': {e}")
        return pd.DataFrame()

# ==========================================================
# 5. UI I NAWIGACJA
# ==========================================================
if 'widok' not in st.session_state: st.session_state['widok'] = 'biezace'

# Przyciski główne
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

# Wybór danych
mapa = {'biezace': "Zadania bieżące", 'zrealizowane': "Zadania zrealizowane", 'slawek': "Terminy Sławka"}
df = pobierz_dane_final(mapa[st.session_state['widok']])

# ==========================================================
# 6. WYŚWIETLANIE
# ==========================================================
st.markdown(f"### Widok: {mapa[st.session_state['widok']]}")

if not df.empty:
    # Filtrowanie dla osób niebędących adminem
    if not czy_admin:
        if zalogowany_uzytkownik == "Sławek":
            # Sławek widzi tylko swoje w ogólnych, ale w swojej zakładce wszystko
            if st.session_state['widok'] != 'slawek' and 'OSOBA' in df.columns:
                df = df[df['OSOBA'] == "Sławek"]
        else:
            # Rafał/Agata nie widzą zadań Sławka w ogólnych listach
            if 'OSOBA' in df.columns:
                df = df[df['OSOBA'] != "Sławek"]

    # Wyświetlanie metryki "Razem"
    st.metric("Liczba zadań", len(df))
    
    # Wyświetlanie tabeli (uproszczone, by uniknąć błędów)
    st.data_editor(df, use_container_width=True, hide_index=True, height=600)
else:
    st.info("Brak danych do wyświetlenia w tej zakładce. Sprawdź, czy w Google Sheets są wpisane zadania.")

with st.sidebar:
    st.markdown("### PANEL STEROWANIA")
    if st.button("🔄 ODŚWIEŻ ARKUSZ"):
        st.cache_data.clear()
        st.rerun()
    st.write(f"Zalogowany: {zalogowany_uzytkownik}")
