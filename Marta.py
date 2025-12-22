import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA ---
# Nazwa pliku w Google Sheets
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

def pobierz_polaczenie():
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                info, 
                ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd klucza w Secrets: {e}")
    return None

def pobierz_dane(zakladka_szukana):
    client = pobierz_polaczenie()
    if not client: return pd.DataFrame(), 0
    try:
        doc = client.open(NAZWA_ARKUSZA)
        arkusze = doc.worksheets()
        
        # Pancerna logika szukania zakładki (ignoruje spacje i wielkość liter)
        sheet = next((s for s in arkusze if s.title.strip().lower() == zakladka_szukana.strip().lower()), None)
        
        if not sheet:
            return pd.DataFrame(), 0
        
        dane = sheet.get_all_values()
        if not dane or len(dane) < 2:
            return pd.DataFrame(), 0
        
        # Tworzenie tabeli
        df = pd.DataFrame(dane[1:], columns=dane[0])
        
        # Licznik zadań (niepuste wiersze w kolumnie A)
        liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
        return df, liczba
    except:
        return pd.DataFrame(), 0

# --- 2. POBIERANIE DANYCH ---
df_biezace, liczba_b = pobierz_dane("Zadania bieżące")
df_zrealizowane, liczba_z = pobierz_dane("Zadania zrealizowane")
df_slawka, _ = pobierz_dane("Terminy Sławka")

# --- 3. WYGLĄD ---
st.markdown("<h3 style='text-align:center;'>Centrum Zarządzania Administracją</h3>", unsafe_allow_html=True)
st.write(f"Ostatnia aktualizacja: {datetime.now().strftime('%H:%M:%S')}")

# Kafelki główne
c1, c2 = st.columns(2)
with c1:
    st.metric("📋 WSZYSTKIE BIEŻĄCE", liczba_b)
with c2:
    st.metric("✅ ZREALIZOWANE", liczba_z)

# Widok tabel
tabs = st.tabs(["📋 LISTA BIEŻĄCA", "✅ ZREALIZOWANE", "📅 TERMINY SŁAWKA"])

with tabs[0]:
    if not df_biezace.empty:
        st.dataframe(df_biezace, use_container_width=True)
    else:
        st.info("Brak danych lub nie znaleziono zakładki 'Zadania bieżące'.")

with tabs[1]:
    if not df_zrealizowane.empty:
        st.dataframe(df_zrealizowane, use_container_width=True)
    else:
        st.info("Brak danych lub nie znaleziono zakładki 'Zadania zrealizowane'.")

with tabs[2]:
    if not df_slawka.empty:
        st.dataframe(df_slawka, use_container_width=True)
    else:
        st.info("Brak danych lub nie znaleziono zakładki 'Terminy Sławka'.")
