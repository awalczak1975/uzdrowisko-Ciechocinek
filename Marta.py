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
    st.error("❌ BŁĄD DOSTĘPU: Nieprawidłowy link lub klucz.")
    st.stop()

# ==========================================================
# 4. FUNKCJE POMOCNICZE
# ==========================================================
def polacz_z_google():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], 
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_dane(zakladka):
    try:
        client = polacz_z_google()
        sheet = client.open(NAZWA_ARKUSZA).worksheet(zakladka)
        dane = sheet.get('A1:E500') 
        if not dane: return pd.DataFrame()
        # Tworzymy DataFrame i upewniamy się, że nazwy kolumn są czyste
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df
    except:
        return pd.DataFrame()

# ==========================================================
# 5. STYLIZACJA CSS
# ==========================================================
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .stButton button { background-color: #334155 !important; color: white !important; border: 1px solid #94a3b8 !important; text-transform: uppercase !important; font-size: 0.8rem !important; }
    [data-testid="stMetric"] { background-color: white !important; border-top: 4px solid #eab308 !important; border-radius: 8px !important; padding: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 6. OKNO DODAWANIA ZADANIA
# ==========================================================
@st.dialog("➕ Dodaj nowe zadanie")
def dodaj_zadanie_dialog():
    with st.form("form_nowe"):
        tresc = st.text_area("Treść zadania:")
        osoba = st.selectbox("Osoba:", ["Brak"] + LISTA_OSOB)
        termin = st.date_input("Termin:", datetime.now())
        if st.form_submit_button("ZAPISZ"):
            try:
                client = polacz_z_google()
                if osoba == "Sławek":
                    sheet = client.open(NAZWA_ARKUSZA).worksheet("Terminy Sławka")
                    sheet.append_row([tresc, "Sławek", termin.strftime("%d.%m.%Y"), "", ""])
                else:
                    sheet = client.open(NAZWA_ARKUSZA).worksheet("Zadania bieżące")
                    sheet.append_row([tresc, osoba if osoba != "Brak" else "", termin.strftime("%d.%m.%Y"), "", "W toku"])
                st.success("Zapisano!"); st.cache_data.clear(); st.rerun()
            except: st.error("Błąd zapisu")

with st.sidebar:
    st.markdown("<h3 style='color: #0ea5e9; text-align:center;'>UZDROWISKO CIECHOCINEK</h3>", unsafe_allow_html=True)
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True): dodaj_zadanie_dialog()
    if st.button("🔄 ODŚWIEŻ DANE", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.markdown(f"<div style='text-align:center; color:#94a3b8; margin-top:30px;'>Zalogowany: {zalogowany_uzytkownik}</div>", unsafe_allow_html=True)

# ==========================================================
# 7. WIDOK GŁÓWNY
# ==========================================================
if 'widok' not in st.session_state: st.session_state['widok'] = 'biezace'

if czy_andrzej:
    c1, c2, c3 = st.columns(3)
else:
    c1, c2 = st.columns(2)

with c1:
    if st.button("📋 BIEŻĄCE", use_container_width=True): st.session_state['widok'] = 'biezace'
with c2:
    if st.button("✅ ZREALIZOWANE", use_container_width=True): st.session_state['widok'] = 'zrealizowane'
if czy_andrzej:
    with c3:
        if st.button("🔧 SŁAWEK", use_container_width=True): st.session_state['widok'] = 'slawek'

mapa_zakladek = {'biezace': "Zadania bieżące", 'zrealizowane': "Zadania zrealizowane", 'slawek': "Terminy Sławka"}
zakladka_nazwa = mapa_zakladek[st.session_state['widok']]
df = pobierz_dane(zakladka_nazwa)

if not df.empty:
    # 1. Usuwanie pustych wierszy na podstawie kolumny A
    df = df[df.iloc[:, 0].astype(str).str.strip() != ""]

    # 2. Sortowanie daty (Obsługa kolumn TERMIN lub DEADLINE)
    kolumna_terminu = "DEADLINE" if "DEADLINE" in df.columns else "TERMIN"
    if kolumna_terminu in df.columns:
        df['temp_date'] = pd.to_datetime(df[kolumna_terminu], dayfirst=True, errors='coerce')
        df = df.sort_values(by='temp_date', ascending=True).drop(columns=['temp_date'])

    # 3. Filtrowanie uprawnień
    if zalogowany_uzytkownik == "Sławek":
        if st.session_state['widok'] == 'slawek': pass
        else: df = df[df['OSOBA'] == "Sławek"]
    elif zalogowany_uzytkownik not in ["Andrzej", "Marta"]:
        df = df[df['OSOBA'] != "Sławek"]

    # 4. Metryki
    m1, m2, m3 = st.columns(3)
    m1.metric("📋 Razem", len(df))
    if 'DNI' in df.columns:
        df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(0)
        m2.metric("🔥 Pilne/Spóźnione", len(df[df['DNI_N'] >= -2]))
    else: m2.metric("Status", "Aktywne")
    m3.metric("🕒 Odświeżono", datetime.now().strftime("%H:%M"))

    # 5. Tabela - Usunięto parametr alignment, aby uniknąć błędu TypeError
    st.data_editor(df, use_container_width=True, hide_index=True, height=650, column_config={"DNI_N": None})
else:
    st.info(f"Brak zadań w: {zakladka_nazwa}")
