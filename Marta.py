# Marta.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =========================
# KONFIGURACJA – JEDYNE MIEJSCE ZMIAN
# =========================
KLUCZ_JSON = "klucz.json"   # plik lokalny, NIE w repo
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# =========================
st_autorefresh(interval=60 * 1000, key="refresh")
st.title("System Uzdrowiskowy - Administracja")

def pobierz_dane():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            KLUCZ_JSON, SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open(NAZWA_ARKUSZA).sheet1

        df = pd.DataFrame(sheet.get_all_records())
        st.success("Połączono z Google Sheets")
        st.dataframe(df)

    except FileNotFoundError:
        st.error("❌ Brak pliku klucz.json (nie dodawaj go do repo!)")
    except Exception as e:
        st.error(f"❌ Błąd: {e}")

pobierz_dane()
st.caption(f"Aktualizacja: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
