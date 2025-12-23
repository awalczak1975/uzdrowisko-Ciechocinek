import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

def pobierz_polaczenie():
    """Łączy się z Google Sheets i naprawia błędy formatowania klucza."""
    try:
        if "gcp_service_account" in st.secrets:
            # Pobieramy dane z sekcji Tajniki (Secrets)
            info = dict(st.secrets["gcp_service_account"])
            
            # PANCERNA POPRAWKA: Naprawiamy klucz, jeśli został wklejony w jednej linii.
            # To rozwiązuje błędy 'Invalid JWT Signature' i 'base64' widoczne na zdjęciach.
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"BŁĄD KONFIGURACJI: {e}")
    return None

def pobierz_dane_po_indeksie(numer_arkusza):
    """Pobiera dane z arkusza na podstawie jego kolejności (indeksu)."""
    client = pobierz_polaczenie()
    if not client: return pd.DataFrame(), 0, "Błąd"
    try:
        doc = client.open(NAZWA_ARKUSZA)
        arkusze = doc.worksheets()
        if len(arkusze) > numer_arkusza:
            sheet = arkusze[numer_arkusza]
            tytul = sheet.title
            dane = sheet.get_all_values()
            if len(dane) < 2: return pd.DataFrame(), 0, tytul
            df = pd.DataFrame(dane[1:], columns=dane[0])
            liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba, tytul
        return pd.DataFrame(), 0, "Nie znaleziono"
    except Exception as e:
        return pd.DataFrame(), 0, f"BŁĄD WCZYTYWANIA: {e}"

# --- 2. START (Pobieranie 1, 2 i 5 zakładki) ---
df_biezace, liczba_b, nazwa_b = pobierz_dane_po_indeksie(0)
df_zrealizowane, liczba_z, nazwa_z = pobierz_dane_po_indeksie(1)
df_slawka, _, nazwa_s = pobierz_dane_po_indeksie(4)

# --- 3. WYGLĄD ---
st.markdown("<h2 style='text-align:center;'>Centrum Zarządzania Administracją</h2>", unsafe_allow_html=True)
st.write(f"Aktualizacja: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

kol1, kol2 = st.columns(2)
with kol1:
    st.metric(label=f"📋 {nazwa_b.upper()}", value=liczba_b)
with kol2:
    st.metric(label=f"✅ {nazwa_z.upper()}", value=liczba_z)

tabs = st.tabs([f"📋 {nazwa_b}", f"✅ {nazwa_z}", f"📅 {nazwa_s}"])
with tabs[0]: st.dataframe(df_biezace, use_container_width=True, hide_index=True) if not df_biezace.empty else st.info("Brak aktywnych zadań.")
with tabs[1]: st.dataframe(df_zrealizowane, use_container_width=True, hide_index=True) if not df_zrealizowane.empty else st.info("Brak zadań.")
with tabs[2]: st.dataframe(df_slawka, use_container_width=True, hide_index=True) if not df_slawka.empty else st.info("Brak danych.")
