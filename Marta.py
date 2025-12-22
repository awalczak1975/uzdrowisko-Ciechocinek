import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA ---
# Upewnij się, że nazwa poniżej jest IDENTYCZNA z nazwą pliku w Google Sheets
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

# --- 2. FUNKCJE POŁĄCZENIA ---
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
        st.error(f"Problem z kluczem w Secrets: {e}")
    return None

def pobierz_dane(zakladka):
    client = pobierz_polaczenie()
    if not client:
        return pd.DataFrame(), 0
    try:
        # Otwieramy arkusz i konkretną zakładkę
        sheet = client.open(NAZWA_ARKUSZA).worksheet(zakladka)
        dane = sheet.get_all_values()
        
        if not dane or len(dane) < 2:
            return pd.DataFrame(), 0
        
        # Tworzymy tabelę (pierwszy rząd to nagłówki)
        df = pd.DataFrame(dane[1:], columns=dane[0])
        
        # Liczymy zadania (niepuste wiersze w pierwszej kolumnie)
        liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
        
        return df, liczba
    except Exception as e:
        # Jeśli nie znajdzie zakładki, wyświetli podpowiedź
        st.warning(f"Nie znaleziono zakładki: '{zakladka}'. Sprawdź pisownię w arkuszu.")
        return pd.DataFrame(), 0

# --- 3. POBIERANIE DANYCH ---
# Nazwy poniżej muszą być identyczne z zakładkami na dole Twojego arkusza (zdjęcie nr 13)
df_biezace, liczba_b = pobierz_dane("Zadania bieżące")
df_zrealizowane, liczba_z = pobierz_dane("Zadania zrealizowane")
df_slawka, _ = pobierz_dane("Terminy Sławka")

# --- 4. WYGLĄD APLIKACJI ---
st.markdown("<h3 style='text-align:center;'>Centrum Zarządzania Administracją</h3>", unsafe_allow_html=True)
st.write(f"Ostatnia aktualizacja: {datetime.now().strftime('%H:%M:%S')}")

# Kafelki z licznikami
c1, c2 = st.columns(2)
with c1:
    st.metric("📋 WSZYSTKIE BIEŻĄCE", liczba_b)
with c2:
    st.metric("✅ ZREALIZOWANE", liczba_z)

# Tabele z danymi
tabs = st.tabs(["📋 LISTA BIEŻĄCA", "✅ ZREALIZOWANE", "📅 TERMINY SŁAWKA"])

with tabs[0]:
    if not df_biezace.empty:
        st.dataframe(df_biezace, use_container_width=True)
    else:
        st.write("Brak danych w zakładce 'Zadania bieżące'.")

with tabs[1]:
    if not df_zrealizowane.empty:
        st.dataframe(df_zrealizowane, use_container_width=True)
    else:
        st.write("Brak danych w zakładce 'Zadania zrealizowane'.")

with tabs[2]:
    if not df_slawka.empty:
        st.dataframe(df_slawka, use_container_width=True)
    else:
        st.write("Brak danych w zakładce 'Terminy Sławka'.")
