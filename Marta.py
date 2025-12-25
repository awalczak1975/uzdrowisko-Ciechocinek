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
st.set_page_config(
    page_title="System Uzdrowisko", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=300000, key="datarefresh")

# ==========================================================
# 2. DANE DOSTĘPOWE
# ==========================================================
KLUCZE_DOSTEPU = {
    "Andrzej": "8800",
    "Marta": "1234",
    "Rafał": "5566",
    "Agata": "9911",
    "Sławek": "4422"
}

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
    czy_admin = (user_url in ["Andrzej", "Marta"])
else:
    st.error("❌ BŁĄD DOSTĘPU: Nieprawidłowy link lub klucz.")
    st.stop()

# ==========================================================
# 4. FUNKCJE POMOCNICZE
# ==========================================================
def wyslij_telegram(wiadomosc):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": wiadomosc, "parse_mode": "HTML"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

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
        return pd.DataFrame(dane[1:], columns=dane[0])
    except:
        return pd.DataFrame()

# ==========================================================
# 5. STYLIZACJA CSS
# ==========================================================
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .stButton button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; text-transform: uppercase !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stMetric"] { 
        background-color: white !important; border-top: 4px solid #eab308 !important; 
        border-radius: 8px !important; padding: 10px !important; 
    }
    .tg_btn { 
        background-color: #0ea5e9 !important; border-radius: 4px !important; 
        display: flex; align-items: center; justify-content: center; 
        color: white !important; font-weight: bold !important; height: 40px !important; 
        text-decoration: none !important; margin-top: 20px; font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 6. OKNO DODAWANIA ZADANIA
# ==========================================================
@st.dialog("➕ Dodaj nowe zadanie")
def dodaj_zadanie_dialog():
    with st.form("form_dodaj"):
        tresc = st.text_area("Treść zadania:")
        domyslny_osoba = zalogowany_uzytkownik if zalogowany_uzytkownik in LISTA_OSOB else "Brak"
        osoba = st.selectbox("Przypisz do:", ["Brak"] + LISTA_OSOB, index=(["Brak"] + LISTA_OSOB).index(domyslny_osoba))
        termin = st.date_input("Termin realizacji:", datetime.now())
        uwagi = st.text_input("Dodatkowe uwagi:")
        if st.form_submit_button("ZAPISZ DO ARKUSZA"):
            try:
                client = polacz_z_google()
                sheet = client.open(NAZWA_ARKUSZA).worksheet("Zadania bieżące")
                osoba_zapis = "" if osoba == "Brak" else osoba
                sheet.append_row([tresc, osoba_zapis, termin.strftime("%d.%m.%Y"), uwagi, "W toku"])
                wyslij_telegram(f"🔔 <b>NOWE ZADANIE</b>\n\n📝 {tresc}\n👤 Dla: {osoba}\n✍️ Dodał: {zalogowany_uzytkownik}")
                st.success("Zapisano!"); st.cache_data.clear(); st.rerun()
            except: st.error("Błąd zapisu")

# ==========================================================
# 7. PANEL BOCZNY
# ==========================================================
with st.sidebar:
    st.markdown("<h2 style='color: #0ea5e9; text-align:center;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h2>", unsafe_allow_html=True)
    st.divider()
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True): dodaj_zadanie_dialog()
    if st.button("🔄 ODŚWIEŻ DANE", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.markdown(f'<a href="https://t.me/share/url?text=Monitorowanie" class="tg_btn">✈️ WYŚLIJ NA TELEGRAM</a>', unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; color:#94a3b8; margin-top:50px; font-size:0.8rem;'>Zalogowany: <b>{zalogowany_uzytkownik}</b></div>", unsafe_allow_html=True)

# ==========================================================
# 8. WIDOK GŁÓWNY
# ==========================================================
st.markdown('<h3 style="text-align:center; color: #1e293b;">Centrum Zarządzania Administracją</h3>', unsafe_allow_html=True)

if 'widok' not in st.session_state: st.session_state['widok'] = 'biezace'

c1, c2 = st.columns(2)
with c1:
    if st.button("📋 ZADANIA BIEŻĄCE", use_container_width=True): st.session_state['widok'] = 'biezace'
with c2:
    if st.button("✅ ZREALIZOWANE", use_container_width=True): st.session_state['widok'] = 'zrealizowane'

zakladka_nazwa = "Zadania bieżące" if st.session_state['widok'] == 'biezace' else "Zadania zrealizowane"
df = pobierz_dane(zakladka_nazwa)

if not df.empty:
    # 1. Usuwanie pustych wierszy
    df = df[df.iloc[:, 0].astype(str).str.strip() != ""]

    # 2. Sortowanie chronologiczne
    if 'TERMIN' in df.columns:
        df['temp_date'] = pd.to_datetime(df['TERMIN'], dayfirst=True, errors='coerce')
        df = df.sort_values(by='temp_date', ascending=True).drop(columns=['temp_date'])

    # 3. Filtrowanie uprawnień
    if not czy_admin:
        if zalogowany_uzytkownik == "Sławek":
            df = df[df['OSOBA'] == "Sławek"]
        else:
            df = df[df['OSOBA'] != "Sławek"]

    # 4. Metryki
    m1, m2, m3 = st.columns(3)
    m1.metric("📋 Razem", len(df))
    
    if st.session_state['widok'] == 'biezace' and 'DNI' in df.columns:
        df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(0)
        m2.metric("🔥 Pilne/Spóźnione", len(df[df['DNI_N'] >= -2]))
    else:
        m2.metric("✅ Status", "Zarchiwizowane")
    m3.metric("🕒 Odświeżono", datetime.now().strftime("%H:%M"))

    # 5. Wyświetlanie tabeli - OSTATECZNA POPRAWKA BŁĘDU
    # Całkowicie usuwamy parametr alignment, który powoduje błąd w wersji 1.52.2
    st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True, 
        height=650,
        column_config={
            "DNI_N": None  # Ukrywamy kolumnę techniczną
        }
    )
else:
    st.info("Brak danych.")
