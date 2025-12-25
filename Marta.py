import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh
import requests

# ================== KONFIGURACJA ==================
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

KLUCZE_DOSTEPU = {
    "Andrzej": "8800",
    "Marta": "1234",
    "Rafał": "5566",
    "Agata": "9911",
    "Sławek": "4422"
}

TELEGRAM_TOKEN = "7547926145:AAHnOIdm6n6_uK03Kk_o0-U0q2F8C_xLpY8"
TELEGRAM_CHAT_ID = "543788771"

# ================== FUNKCJE ==================
def wyslij_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
        )
    except Exception as e:
        st.warning(f"Telegram: {e}")

def polacz_z_google():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
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
        st.error(f"❌ Google Sheets: {e}")
        return pd.DataFrame()

# ================== STREAMLIT ==================
st.set_page_config(
    page_title="System Uzdrowisko",
    layout="wide",
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=300000)

# ================== LOGOWANIE ==================
user = st.query_params.get("u", "")
key = st.query_params.get("k", "")

if user not in KLUCZE_DOSTEPU or KLUCZE_DOSTEPU[user] != key:
    st.error("❌ BŁĘDNY LINK DOSTĘPU")
    st.stop()

czy_admin = user in ["Andrzej", "Marta"]

# ================== TEST POŁĄCZENIA ==================
try:
    client = polacz_z_google()
    arkusze = [s.title for s in client.openall()]
    if NAZWA_ARKUSZA not in arkusze:
        st.error("❌ BRAK DOSTĘPU DO ARKUSZA")
        st.stop()
except Exception as e:
    st.error(f"❌ AUTORYZACJA GOOGLE: {e}")
    st.stop()

# ================== UI ==================
st.markdown(
    "<h3 style='text-align:center'>Centrum Zarządzania Administracją</h3>",
    unsafe_allow_html=True
)

if "widok" not in st.session_state:
    st.session_state["widok"] = "biezace"

c1, c2 = st.columns(2)
with c1:
    if st.button("📋 ZADANIA BIEŻĄCE", use_container_width=True):
        st.session_state["widok"] = "biezace"
with c2:
    if st.button("✅ ZREALIZOWANE", use_container_width=True):
        st.session_state["widok"] = "zrealizowane"

zakladka = "Zadania bieżące" if st.session_state["widok"] == "biezace" else "Zadania zrealizowane"
df = pobierz_dane(zakladka)

# ================== FILTROWANIE ==================
if not df.empty and not czy_admin:
    df = df[(df["OSOBA"] == user) | (df["OSOBA"] == "")]

# ================== METRYKI ==================
if not df.empty and "DNI" in df.columns:
    df["DNI"] = pd.to_numeric(df["DNI"], errors="coerce").fillna(0)
    m1, m2, m3 = st.columns(3)
    m1.metric("📋 Razem", len(df))
    m2.metric("🔥 Pilne", len(df[df["DNI"] <= 0]))
    m3.metric("🕒 Godzina", datetime.now().strftime("%H:%M"))

# ================== TABELA ==================
if df.empty:
    st.info("Brak zadań do wyświetlenia")
else:
    st.data_editor(df, hide_index=True, height=700)

# ================== DODAWANIE ZADANIA ==================
@st.dialog("➕ Dodaj zadanie")
def dodaj_zadanie():
    with st.form("nowe"):
        tresc = st.text_area("Treść zadania")
        osoba = st.selectbox("Osoba", [""] + list(KLUCZE_DOSTEPU.keys()))
        termin = st.date_input("Termin", datetime.now())
        uwagi = st.text_input("Uwagi")

        if st.form_submit_button("ZAPISZ"):
            try:
                client = polacz_z_google()
                ws = client.open(NAZWA_ARKUSZA).worksheet("Zadania bieżące")
                ws.append_row([
                    tresc,
                    osoba,
                    termin.strftime("%d.%m.%Y"),
                    uwagi,
                    "W toku"
                ])
                wyslij_telegram(f"🔔 <b>NOWE ZADANIE</b>\n{tresc}")
                st.success("✅ Dodano")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Zapis: {e}")

with st.sidebar:
    if st.button("➕ DODAJ ZADANIE"):
        dodaj_zadanie()
    st.markdown(f"Zalogowany: **{user}**")





