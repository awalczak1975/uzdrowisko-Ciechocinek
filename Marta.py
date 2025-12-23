import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- KONFIGURACJA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
KLUCZ_JSON = "nowy_klucz.json"  # <-- wpisz tutaj ścieżkę do nowego klucza JSON
SCOPES = ["https://spreadsheets.google.com/feeds",
          "https://www.googleapis.com/auth/drive"]

# --- AUTOREFRESH CO 60 SEKUND ---
st_autorefresh(interval=60 * 1000, key="datarefresh")

st.title("System Uzdrowiskowy - Administracja")

def pobierz_arkusz():
    try:
        # Autoryzacja
        creds = ServiceAccountCredentials.from_json_keyfile_name(KLUCZ_JSON, SCOPES)
        client = gspread.authorize(creds)

        # Próba otwarcia arkusza
        arkusz = client.open(NAZWA_ARKUSZA)
        sheet = arkusz.sheet1  # pierwszy arkusz

        # Pobranie danych
        dane = sheet.get_all_records()
        df = pd.DataFrame(dane)

        st.success(f"Pobrano dane z arkusza: {NAZWA_ARKUSZA}")
        st.dataframe(df)

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Nie znaleziono arkusza o nazwie: {NAZWA_ARKUSZA}. Sprawdź czy konto serwisowe ma dostęp.")
    except gspread.exceptions.APIError as e:
        st.error(f"Błąd API Google Sheets: {e}")
    except Exception as e:
        st.error(f"Wystąpił nieoczekiwany błąd: {e}")

# --- WYWOŁANIE FUNKCJI ---
pobierz_arkusz()

# --- INFORMACJA O CZASIE OSTATNIEJ AKTUALIZACJI ---
st.markdown(f"**Aktualizacja danych:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
