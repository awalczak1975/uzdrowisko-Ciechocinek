import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json
import os

# --- KONFIGURACJA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
PLIK_KLUCZA = "klucz.json"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")

def pobierz_polaczenie():
    """Łączy się z Google Sheets używając pliku klucz.json z GitHub."""
    try:
        # Sprawdzamy czy plik istnieje w folderze aplikacji
        if os.path.exists(PLIK_KLUCZA):
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(PLIK_KLUCZA, scope)
            return gspread.authorize(creds)
        else:
            st.error("❌ Nie znaleziono pliku klucz.json w repozytorium!")
            return None
    except Exception as e:
        st.error(f"❌ Błąd połączenia: {e}")
        return None

def pobierz_dane(indeks):
    """Pobiera dane z konkretnej zakładki arkusza."""
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
            liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba, sheet.title
        return pd.DataFrame(), 0, "Brak"
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd: {e}"

# --- POBIERANIE DANYCH ---
df_b, l_b, n_b = pobierz_dane(0) # Bieżące
df_z, l_z, n_z = pobierz_dane(1) # Zrealizowane
df_s, _, n_s = pobierz_dane(4)   # Sławek

# --- INTERFEJS ---
st.markdown("<h2 style='text-align:center;'>Centrum Zarządzania Administracją</h2>", unsafe_allow_html=True)
st.write(f"Stan na: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

# Kafelki z liczbami
c1, c2 = st.columns(2)
c1.metric(f"📋 {n_b}", l_b)
c2.metric(f"✅ {n_z}", l_z)

# Zakładki z tabelami
tabs = st.tabs([n_b, n_z, n_s])
with tabs[0]:
    if not df_b.empty: st.dataframe(df_b, use_container_width=True, hide_index=True)
    else: st.info("Brak zadań.")
with tabs[1]:
    if not df_z.empty: st.dataframe(df_z, use_container_width=True, hide_index=True)
with tabs[2]:
    if not df_s.empty: st.dataframe(df_s, use_container_width=True, hide_index=True)
