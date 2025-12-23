import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import os

# --- 1. KONFIGURACJA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
PLIK_KLUCZA = "klucz.json"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")

def pobierz_polaczenie():
    """Łączy się z arkuszem używając pliku klucz.json wgranego na GitHub."""
    try:
        if os.path.exists(PLIK_KLUCZA):
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(PLIK_KLUCZA, scope)
            return gspread.authorize(creds)
        else:
            st.error("❌ Brak pliku klucz.json w repozytorium GitHub!")
            return None
    except Exception as e:
        st.error(f"❌ Błąd autoryzacji: {e}")
        return None

def pobierz_dane(indeks):
    """Pobiera dane z konkretnej zakładki arkusza Marty."""
    client = pobierz_polaczenie()
    if not client: return pd.DataFrame(), 0, "Błąd"
    try:
        doc = client.open(NAZWA_ARKUSZA)
        arkusze = doc.worksheets()
        if len(arkusze) > indeks:
            sheet = arkusze[indeks]
            dane = sheet.get_all_values()
            if len(dane) < 2: return pd.DataFrame(), 0, sheet.title
            df = pd.DataFrame(dane[1:], columns=dane[0])
            # Liczymy rzędy, które nie są puste
            liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba, sheet.title
        return pd.DataFrame(), 0, "Nie znaleziono"
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd: {e}"

# --- 2. START ---
df_b, l_b, n_b = pobierz_dane(0) # Zadania bieżące
df_z, l_z, n_z = pobierz_dane(1) # Zadania zrealizowane
df_s, _, n_s = pobierz_dane(4)   # Terminy Sławka

# --- 3. WYŚWIETLANIE ---
st.markdown("<h2 style='text-align:center;'>Centrum Zarządzania Administracją</h2>", unsafe_allow_html=True)
st.write(f"Stan na dzień: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# Główne liczniki (Poprawiona składnia usuwająca AttributeError)
kol1, kol2 = st.columns(2)
kol1.metric(label=f"📋 {n_b}", value=l_b)
kol2.metric(label=f"✅ {n_z}", value=l_z)

st.divider()

# Zakładki z tabelami
zakladki = st.tabs([f"📋 {n_b}", f"✅ {n_z}", f"📅 {n_s}"])

with zakladki[0]:
    if not df_b.empty:
        st.dataframe(df_b, use_container_width=True, hide_index=True)
    else:
        st.info("Brak aktywnych zadań.")

with zakladki[1]:
    if not df_z.empty:
        st.dataframe(df_z, use_container_width=True, hide_index=True)

with zakladki[2]:
    if not df_s.empty:
        st.dataframe(df_s, use_container_width=True, hide_index=True)
