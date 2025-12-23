# Marta.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ----------------------------
# 1. KONFIGURACJA
# ----------------------------
KLUCZ_JSON = "klucz.json"            # <-- wpisz tutaj swój plik JSON
NAZWA_ARKUSZA = "Marta-Dział Techniczny"  # <-- wpisz tutaj nazwę arkusza
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ----------------------------
# 2. AUTOREFRESH CO 60 SEKUND
# ----------------------------
st_autorefresh(interval=60 * 1000, key="datarefresh")

# ----------------------------
# 3. TYTUŁ APLIKACJI
# ----------------------------
st.title("System Uzdrowiskowy - Administracja")

# ----------------------------
# 4. FUNKCJA POBIERAJĄCA DANE
# ----------------------------
def pobierz_arkusz():
    try:
        # Autoryzacja
        creds = ServiceAccountCredentials.from_json_keyfile_name(KLUCZ_JSON, SCOPES)
        client = gspread.authorize(creds)

        # Otwórz arkusz
        arkusz = client.open(NAZWA_ARKUSZA)
        sheet = arkusz.sheet1  # Pierwszy arkusz

        # Pobierz dane
        dane = sheet.get_all_records()
        df = pd.DataFrame(dane)

        # Wyświetl dane
        st.success(f"Pobrano dane z arkusza: {NAZWA_ARKUSZA}")
        st.dataframe(df)

    except FileNotFoundError:
        st.error(f"Nie znaleziono pliku JSON: {KLUCZ_JSON}")
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Nie znaleziono arkusza: {NAZWA_ARKUSZA}. Sprawdź dostęp konta serwisowego.")
    except gspread.exceptions.APIError as e:
        st.error(f"Błąd API Google Sheets: {e}")
    except Exception as e:
        st.error(f"Wystąpił nieoczekiwany błąd: {e}")

# ----------------------------
# 5. WYWOŁANIE FUNKCJI
# ----------------------------
pobierz_arkusz()

# ----------------------------
# 6. CZAS OSTATNIEJ AKTUALIZACJI
# ----------------------------
st.markdown(f"**Aktualizacja danych:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

