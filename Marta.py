import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. DANE DOSTĘPOWE ---
KLUCZE_DOSTEPU = {
    "Andrzej": "8800",
    "Marta": "1234",
    "Rafał": "5566",
    "Agata": "9911",
    "Sławek": "4422"
}

TELEGRAM_TOKEN = "7547926145:AAHnOIdm6n6_uK03Kk_o0-U0q2F8C_xLpY8"
TELEGRAM_CHAT_ID = "543788771"

def wyslij_telegram(wiadomosc):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": wiadomosc, "parse_mode": "HTML"}
    try: 
        requests.post(url, json=payload, timeout=5)
    except: 
        pass

# --- 2. KONFIGURACJA I AUTOREFRESH ---
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=300000, key="datarefresh")

# --- 3. WERYFIKACJA UŻYTKOWNIKA ---
user_url = st.query_params.get("u", "")
key_url = st.query_params.get("k", "")

if user_url in KLUCZE_DOSTEPU and KLUCZE_DOSTEPU[user_url] == key_url:
    zalogowany_uzytkownik = user_url
    czy_admin = (user_url == "Andrzej" or user_url == "Marta")
else:
    st.error("❌ BŁĄD DOSTĘPU: Nieprawidłowy link lub klucz.")
    st.stop()

# --- 4. STYLIZACJA CSS ---
st.markdown("""
    <style>
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .logo-full-box { display: flex; align-items: center; justify-content: center; width: 100%; padding: 0; margin-top: -25px !important; margin-bottom: 5px !important; }
    .stButton button {
        background-color: #334155 !important; color: #ffffff !important;
        border: 1px solid #94a3b8 !important; border-radius: 4px !important;
        font-size: 0.75rem !important; height: 34px !important; 
        text-transform: uppercase !important; font-weight: 500 !important;
    }
    [data-testid="stMetric"] { background-color: #ffffff !important; border-top: 4px solid #eab308 !important; border-radius: 8px !important; padding: 5px 15px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; font-weight: 800 !important; font-size: 1.6rem !important; color: #1e293b !important; }
    .tg_btn { background-color: #0ea5e9 !important; border-radius: 4px !important; display: flex; align-items: center; justify-content: center; text-decoration: none !important; color: white !important; font-weight: bold !important; font-size: 0.75rem !important; height: 34px !important; width: 100% !important; margin-top: 20px !important; text-transform: uppercase !important; }
    .op-footer { text-align: center; color: #94a3b8; border-top: 1px solid #334155; padding-top: 10px; margin-top: 20px; font-size: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. FUNKCJE DANYCH (GOOGLE SHEETS) ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
LISTA_OSOB = list(KLUCZE_DOSTEPU.keys())

def polacz_z_google():
    # Używamy st.secrets dla bezpieczeństwa na Streamlit Cloud
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], 
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_dane(zakladka):
    try:
        client = polacz_z_google()
        sheet = client.open(NAZWA_ARKUSZA).worksheet(zakladka)
        dane = sheet.get_all_values()
        if not dane:
            return pd.DataFrame()
        return pd.DataFrame(dane[1:], columns=dane[0])
    except Exception as e:
        st.error(f"Błąd pobierania: {e}")
        return pd.DataFrame()

@st.dialog("➕ Dodaj nowe zadanie")
def dodaj_zadanie_dialog():
    with st.form("form_dodaj"):
        tresc = st.text_area("Treść zadania:")
        domyslny_idx = LISTA_OSOB.index(zalogowany_uzytkownik) + 1 if zalogowany_uzytkownik in LISTA_OSOB else 0
        osoba = st.selectbox("Przypisz do:", ["Brak"] + LISTA_OSOB, index=domyslny_idx)
        termin = st.date_input("Termin realizacji:", datetime.now())
        uwagi = st.text_input("Dodatkowe uwagi:")
        
        if st.form_submit_button("ZAPISZ DO ARKUSZA"):
            try:
                client = polacz_z_google()
                sheet = client.open(NAZWA_ARKUSZA).worksheet("Zadania bieżące")
                osoba_zapis = "" if osoba == "Brak" else osoba
                sheet.append_row([tresc, osoba_zapis, termin.strftime("%d.%m.%Y"), uwagi, "W toku"])
                
                wyslij_telegram(f"🔔 <b>NOWE ZADANIE</b>\n\n📝 {tresc}\n👤 Dla: {osoba}\n✍️ Dodał: {zalogowany_uzytkownik}")
                
                st.success("Zadanie zapisane pomyślnie!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")

# --- 6. LOGIKA WIDOKU ---
if 'widok' not in st.session_state:
    st.session_state['widok'] = 'biezace'

# --- 7. PANEL BOCZNY ---
with st.sidebar:
    st.markdown("""<div class='logo-full-box'><svg width="240" height="75" viewBox="0 0 240 75" xmlns="http://www.w3.org/2000/svg"><circle cx="28" cy="35" r="10" fill="#eab308" /><path d="M28 18 L28 25 M28 45 L28 52 M11 35 L18 35 M38 35 L45 35 M16 23 L21 28 M35 42 L40 47 M16 47 L21 42 M35 23 L40 28" stroke="#eab308" stroke-width="3" stroke-linecap="round"/><text x="52" y="32" font-family="Arial Black" font-size="18" font-weight="900" fill="#0ea5e9">UZDROWISKO</text><text x="52" y="52" font-family="Arial Black" font-size="16" font-weight="900" fill="#0ea5e9">CIECHOCINEK S.A.</text></svg></div>""", unsafe_allow_html=True)
    st.divider()
    
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True):
        dodaj_zadanie_dialog()
    
    st.divider()
    if st.button("🔄 SYNCHRONIZUJ DANE", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown(f'<a href="https://t.me/share/url?text=Monitorowanie zadań" class="tg_btn">✈️ POWIADOM TELEGRAM</a>', unsafe_allow_html=True)
    st.markdown(f"<div class='op-footer'>Zalogowany: <b>{zalogowany_uzytkownik}</b></div>", unsafe_allow_html=True)

# --- 8. WIDOK GŁÓWNY ---
st.markdown('<h3 style="text-align:center; color: #1e293b;">Centrum Zarządzania Administracją</h3>', unsafe_allow_html=True)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("📋 ZADANIA BIEŻĄCE", use_container_width=True):
        st.session_state['widok'] = 'biezace'
with col_b2:
    if st.button("✅ ZREALIZOWANE", use_container_width=True):
        st.session_state['widok'] = 'zrealizowane'

# Pobieranie danych w zależności od wybranego widoku
zakladka_nazwa = "Zadania bieżące" if st.session_state['widok'] == 'biezace' else "Zadania zrealizowane"
df = pobierz_dane(zakladka_nazwa)

if not df.empty:
    # Filtrowanie uprawnień
    if not czy_admin:
        if zalogowany_uzytkownik == "Sławek":
            df = df[df['OSOBA'] == "Sławek"]
        else:
            # Rafał i Agata widzą swoje oraz te bez przypisanej osoby
            df = df[(df['OSOBA'] == zalogowany_uzytkownik) | (df['OSOBA'] == "") | (df['OSOBA'] == "Brak")]

    # Metryki dla widoku bieżącego
    if st.session_state['widok'] == 'biezace' and 'DNI' in df.columns:
        df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(0)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📋 Razem", len(df))
        m2.metric("🔥 Pilne", len(df[df['DNI_N'] <= 0]))
        m3.metric("⚠️ W toku", len(df[df['DNI_N'] > 0]))
        m4.metric("🕒 Godzina", datetime.now().strftime("%H:%M"))
    
    # Wyświetlanie tabeli
    st.data_editor(df, width=None, use_container_width=True, hide_index=True, height=600)
else:
    st.info(f"Brak zadań w zakładce: {zakladka_nazwa}")
